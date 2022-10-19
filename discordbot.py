# -*- coding: utf-8 -*-
import asyncio
import csv
import datetime
import gdshortener
import glob
import MeCab
from nltk import ngrams
from ntpath import join
import os
import random
import re
# import sys
import ffmpeg
import time
import typing
import discord
import modules.img
import requests
import tweepy
import yt_dlp
from collections import Counter, defaultdict
from discord.ext import commands
from googleapiclient.discovery import build
from niconico import NicoNico
from os import getenv
from PIL import Image
from spotdl import Spotdl
from yt_dlp import YoutubeDL

# spotdl
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET")
spotdl = Spotdl(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)

# DiscordBot
DISCORD_BOT_TOKEN = getenv("DISCORD_BOT_TOKEN")
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
# Botの接頭辞を ! にする
bot = commands.Bot(command_prefix="!", intents=intents)

# Annict
ANNICT_API_KEY = getenv("ANNICT_API_KEY")

# google-api-python-client / YouTube Data API v3
YOUTUBE_API_KEY = getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Tweepy
TWITTER_CONSUMER_KEY = getenv("CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = getenv("CONSUMER_SECRET")
TWITTER_ACCESS_TOKEN_KEY = getenv("ACCESS_TOKEN_KEY")
TWITTER_ACCESS_TOKEN_SECRET = getenv("ACCESS_TOKEN_SECRET")
twauth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
twauth.set_access_token(TWITTER_ACCESS_TOKEN_KEY, TWITTER_ACCESS_TOKEN_SECRET)

twapi = tweepy.API(twauth)

# yt_dlp
YTDL_FORMAT_OPTIONS = {
    "format": "bestaudio/best*[acodec=aac]",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0"  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

# before_optionsではなくoptionsで指定されてました。修正。様子見でお願いします。
# https://stackoverflow.com/questions/58892635/discord-py-and-youtube-dl-read-error-and-the-session-has-been-invalidated-fo
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_at_eof 1 -reconnect_on_network_error 1 -reconnect_delay_max 5",
    "options": "-vn"
}

# https://qiita.com/sizumita/items/cafd00fe3e114d834ce3
# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda: ""

ytdl = yt_dlp.YoutubeDL(YTDL_FORMAT_OPTIONS)

# 定数 - 基本的に大文字
# 聖バリ鯖のサーバーID
SEIBARI_GUILD_ID = 889049222152871986
# 白猫ハウスのサーバーID
SIRONEKO_GUILD_ID = 733998377074688050
# パソ人ハウスのサーバーID
PASOJIN_GUILD_ID = 894896479804727366

# 検索欄のチャンネルID
TWITTER_SEARCH_CHANNEL_ID = 974430034691498034
# mp3_to_mp4のチャンネルID
WIP_CHANNEL_ID = 940966825087361025
# ファル子☆おもしろ画像集のチャンネルID
FALCO_CHANNEL_ID = 955809774849646603
# まちカドたんほいざのチャンネルID
MACHITAN_CHANNEL_ID = 987930969040355361
# no context hentai imgのチャンネルID
NO_CONTEXT_HENTAI_IMG_CHANNEL_ID = 988071456430760006
# ﾎﾞｸはﾃｲｵｰ!ちゃんねる
TEIOU_CHANNEL_ID = 1012808118469677148
# ボイスチャット通知のチャンネルID
VOICECHAT_NOTIFICATION_CHANNEL_ID = 1009127020518707201

# あるくおすしのユーザーID
WALKINGSUSHIBOX_USER_ID = 575588255647399958
# 野獣先輩のユーザーID
TADOKOROKOUJI_USER_ID = 1145141919810364364

client = discord.Client()


class NicoNicoDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, url, original_url, video, volume=0.5):
        super().__init__(source, volume)

        self.url = url
        self.original_url = original_url
        self.video = video
        self.title = video.video.title

    @classmethod
    async def from_url(cls, url):
        # とりあえず毎回clientを作っておく
        niconico_client = NicoNico()
        video = niconico_client.video.get_video(url)
        # 必ずあとでコネクションを切る
        video.connect()

        source = discord.FFmpegPCMAudio(video.download_link, **FFMPEG_OPTIONS)
        return cls(source, video.download_link, url, video)

    def close_connection(self):
        self.video.close()


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data
        self.id = data.get("id")
        self.original_url = data.get("original_url")
        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        # もしプレイリストだった場合
        if "entries" in data:
            # プレイリストの1曲目をとる
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)

        source = discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS)
        return cls(source, data=data)


# Cog とは: コマンドとかの機能をひとまとめにできる
class Music(commands.Cog):
    def __init__(self, bot_arg):
        self.bot = bot_arg
        self.loop: bool = False
        self.player: typing.Union[YTDLSource, NicoNicoDLSource, None] = None
        self.queue: typing.List[typing.Union[YTDLSource, NicoNicoDLSource]] = []

    def after_play(self, guild, err):
        if type(self.player) == NicoNicoDLSource:
            self.player.close_connection()

        if err:
            return print(f"has error: {err}")

        if len(self.queue) <= 0:
            return

        self.player = self.queue.pop(0)

        guild.voice_client.play(self.player, after=lambda e: self.after_play(guild, e))

    @commands.command()
    async def join(self, ctx):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            embed = discord.Embed(colour=0xff0000, title="エラーが発生しました", description="操作する前にボイスチャンネルに接続してください")
            return await ctx.channel.send(embed=embed)

        # ボイスチャンネルに接続する
        await ctx.author.voice.channel.connect()

        embed = discord.Embed(colour=0xff00ff, title="接続しました")
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def leave(self, ctx):
        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            embed = discord.Embed(colour=0xff0000, title="エラーが発生しました", description="Botがボイスチャンネルに接続していません")
            await ctx.channel.send(embed=embed)
            return

        # 切断する
        await ctx.guild.voice_client.disconnect()

        embed = discord.Embed(colour=0xff00ff, title="切断しました")
        await ctx.channel.send(embed=embed)

    # @commands.command(aliases=["l"])
    # async def loop(self, ctx):
    #     # コマンドを送ったユーザーがボイスチャンネルに居ない場合
    #     if ctx.author.voice is None:
    #         embed = discord.Embed(colour=0xff0000, title="エラーが発生しました", description="操作する前にボイスチャンネルに接続してください")
    #         return await ctx.channel.send(embed=embed)
    #
    #     # Botがボイスチャンネルに居ない場合
    #     if ctx.guild.voice_client is None:
    #         embed = discord.Embed(colour=0xff0000, title="エラーが発生しました", description="Botがボイスチャンネルに接続していません")
    #         await ctx.channel.send(embed=embed)
    #         return
    #
    #     self.loop = not self.loop
    #
    #     embed = discord.Embed(colour=0xff00ff, title=f"ループを {"`有効`" if self.loop else "`無効`"} にしました")
    #     await ctx.channel.send(embed=embed)

    @commands.command(aliases=["np"])
    async def nowplaying(self, ctx):
        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            embed = discord.Embed(colour=0xff0000, title="エラーが発生しました", description="Botがボイスチャンネルに接続していません")
            await ctx.channel.send(embed=embed)
            return

        embed = discord.Embed(colour=0xff00ff, title="現在再生中", description=f"[{self.player.title}]({self.player.original_url})" if ctx.guild.voice_client.is_playing() else "再生していません")
        embed.set_footer(text=f"残りキュー: {len(self.queue)}")
        # embed.set_footer(text=f"残りキュー: {len(self.queue)} | ループ: {"有効" if self.loop else "無効"}")

        # サムネイルをAPIで取得
        if ctx.guild.voice_client.is_playing() and ("youtube.com" in self.player.original_url or "youtu.be" in self.player.original_url):
            np_youtube_video = youtube.videos().list(part="snippet", id=self.player.id).execute()
            np_thumbnail = np_youtube_video["items"][0]["snippet"]["thumbnails"]
            np_highres_thumbnail = list(np_thumbnail.keys())[-1]
            embed.set_thumbnail(url=np_thumbnail[np_highres_thumbnail]["url"])

        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, url):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            embed = discord.Embed(colour=0xff0000, title="エラーが発生しました", description="操作する前にボイスチャンネルに接続してください")
            return await ctx.channel.send(embed=embed)

        # ボイスチャンネルにBotが未接続の場合はボイスチャンネルに接続する
        if ctx.guild.voice_client is None:
            await ctx.author.voice.channel.connect()

        embed = discord.Embed(colour=0xff00ff, title="処理中です...")
        play_msg: discord.Message = await ctx.channel.send(embed=embed)

        # niconico.py は短縮URLも取り扱えるっぽいので信じてみる
        # https://github.com/tasuren/niconico.py/blob/b4d9fcb1d0b80e83f2d8635dd85987d1fa2d84fc/niconico/video.py#L367
        is_niconico_mylist = url.startswith("https://www.nicovideo.jp/mylist") or url.startswith("https://nico.ms/mylist")
        is_niconico = url.startswith("https://www.nicovideo.jp/") or url.startswith("https://nico.ms/")
        is_spotify = url.startswith("https://open.spotify.com/")
        other_sources = []

        # 各サービスごとに振り分け
        if is_niconico_mylist:
            niconico_client = NicoNico()
            for item in niconico_client.video.get_mylist(url):
                item_first = item.items[0]
                item_first_url = item_first.video.url
                source = await NicoNicoDLSource.from_url(item_first_url)

            # キューへの追加
            if ctx.guild.voice_client.is_playing():  # 他の曲を再生中の場合
                # self.playerに追加すると再生中の曲と衝突する
                self.queue.append(source)
                embed = discord.Embed(colour=0xff00ff, title="キューに追加しました", description=f"[{source.title}]({source.original_url})")
                await play_msg.edit(embed=embed)

            else:  # 他の曲を再生していない場合
                # self.playerにURLを追加し再生する
                self.player = source
                ctx.guild.voice_client.play(self.player, after=lambda e: self.after_play(ctx.guild, e))
                embed = discord.Embed(colour=0xff00ff, title="再生を開始します", description=f"[{source.title}]({source.original_url})")
                await play_msg.edit(embed=embed)

                # マイリストの2曲目以降のURLを変換してother_sourcesに入れる
                item_others = item.items[1:]
                for item_others_item in item_others:
                    item_others_item_url = item_others_item.video.url
                    other_sources.append(await NicoNicoDLSource.from_url(item_others_item_url))

        elif is_niconico:
            source = await NicoNicoDLSource.from_url(url)

            # キューへの追加
            if ctx.guild.voice_client.is_playing():  # 他の曲を再生中の場合
                # self.playerに追加すると再生中の曲と衝突する
                self.queue.append(source)
                embed = discord.Embed(colour=0xff00ff, title="キューに追加しました", description=f"[{source.title}]({source.original_url})")
                await play_msg.edit(embed=embed)

            else:  # 他の曲を再生していない場合
                # self.playerにURLを追加し再生する
                self.player = source
                ctx.guild.voice_client.play(self.player, after=lambda e: self.after_play(ctx.guild, e))
                embed = discord.Embed(colour=0xff00ff, title="再生を開始します", description=f"[{source.title}]({source.original_url})")
                await play_msg.edit(embed=embed)

        elif is_spotify:
            # プレイリストの1曲目のURLを変換してsourceに入れる
            songs = spotdl.search([url])
            urls = spotdl.get_download_urls(songs)
            source = await YTDLSource.from_url(urls[0], loop=client.loop, stream=True)

            # キューへの追加
            if ctx.guild.voice_client.is_playing():  # 他の曲を再生中の場合
                # self.playerに追加すると再生中の曲と衝突する
                self.queue.append(source)
                embed = discord.Embed(colour=0xff00ff, title="キューに追加しました", description=f"[{source.title}]({source.original_url})")
                await play_msg.edit(embed=embed)

            else:  # 他の曲を再生していない場合
                # self.playerにURLを追加し再生する
                self.player = source
                ctx.guild.voice_client.play(self.player, after=lambda e: self.after_play(ctx.guild, e))
                embed = discord.Embed(colour=0xff00ff, title="再生を開始します", description=f"[{source.title}]({source.original_url})")
                # サムネイルをAPIで取得
                np_youtube_video = youtube.videos().list(part="snippet", id=self.player.id).execute()
                np_thumbnail = np_youtube_video["items"][0]["snippet"]["thumbnails"]
                np_highres_thumbnail = list(np_thumbnail.keys())[-1]
                embed.set_thumbnail(url=np_thumbnail[np_highres_thumbnail]["url"])
                await play_msg.edit(embed=embed)

            # プレイリストの2曲目以降のURLを変換してother_sourcesに入れる
            for url in urls[1:]:
                other_sources.append(await YTDLSource.from_url(url, loop=client.loop, stream=True))

        else:
            data = await client.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

            # もしプレイリストだった場合
            if "entries" in data:
                datalist_first = data["entries"][0]
                original_url = datalist_first.get("original_url")
                source = await YTDLSource.from_url(original_url, loop=client.loop, stream=True)

                # キューへの追加
                if ctx.guild.voice_client.is_playing():  # 他の曲を再生中の場合
                    # self.playerに追加すると再生中の曲と衝突する
                    self.queue.append(source)
                    embed = discord.Embed(colour=0xff00ff, title="キューに追加しました", description=f"[{source.title}]({source.original_url})")
                    await play_msg.edit(embed=embed)

                else:  # 他の曲を再生していない場合
                    # self.playerにURLを追加し再生する
                    self.player = source
                    ctx.guild.voice_client.play(self.player, after=lambda e: self.after_play(ctx.guild, e))
                    embed = discord.Embed(colour=0xff00ff, title="再生を開始します", description=f"[{source.title}]({source.original_url})")
                    # サムネイルをAPIで取得
                    np_youtube_video = youtube.videos().list(part="snippet", id=self.player.id).execute()
                    np_thumbnail = np_youtube_video["items"][0]["snippet"]["thumbnails"]
                    np_highres_thumbnail = list(np_thumbnail.keys())[-1]
                    embed.set_thumbnail(url=np_thumbnail[np_highres_thumbnail]["url"])
                    await play_msg.edit(embed=embed)

                    # プレイリストの2曲目以降のURLを変換してother_sourcesに入れる
                datalist_others = data["entries"][1:]
                for item in datalist_others:
                    original_url = item.get("original_url")
                    other_sources.append(await YTDLSource.from_url(original_url, loop=client.loop, stream=True))

            else:
                original_url = data.get("original_url")
                source = await YTDLSource.from_url(original_url, loop=client.loop, stream=True)

                # キューへの追加
                if ctx.guild.voice_client.is_playing():  # 他の曲を再生中の場合
                    # self.playerに追加すると再生中の曲と衝突する
                    self.queue.append(source)
                    embed = discord.Embed(colour=0xff00ff, title="キューに追加しました", description=f"[{source.title}]({source.original_url})")
                    await play_msg.edit(embed=embed)

                else:  # 他の曲を再生していない場合
                    # self.playerにURLを追加し再生する
                    self.player = source
                    ctx.guild.voice_client.play(self.player, after=lambda e: self.after_play(ctx.guild, e))
                    embed = discord.Embed(colour=0xff00ff, title="再生を開始します", description=f"[{source.title}]({source.original_url})")
                    np_youtube_video = youtube.videos().list(part="snippet", id=self.player.id).execute()
                    # サムネイル情報が入っている場合
                    if np_youtube_video["items"]:
                        np_thumbnail = np_youtube_video["items"][0]["snippet"]["thumbnails"]
                        np_highres_thumbnail = list(np_thumbnail.keys())[-1]
                        embed.set_thumbnail(url=np_thumbnail[np_highres_thumbnail]["url"])
                        await play_msg.edit(embed=embed)
                    else:
                        await play_msg.edit(embed=embed)

        self.queue.extend(other_sources)

    @commands.command(aliases=["q"])
    async def queue(self, ctx):

        embed = discord.Embed(colour=0xff00ff, title="キュー")

        if not ctx.guild.voice_client.is_playing():
            embed.description = "再生していません"

        else:
            queue_embed = [f"__現在再生中__:\n[{self.player.title}]({self.player.original_url})"]

            for i in range(min(len(self.queue), 10)):
                queue_embed.append(("__次に再生__:\n" if i == 0 else "") + f"`{i + 1}.` [{self.queue[i].title}]({self.queue[i].original_url})")

            embed.description = "\n\n".join(queue_embed)

        embed.set_footer(text=f"残りキュー: {len(self.queue)}")
        # embed.set_footer(text=f"残りキュー: {len(self.queue)} | ループ: {"有効" if self.loop else "無効"}")
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["s"])
    async def skip(self, ctx):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            embed = discord.Embed(colour=0xff0000, title="エラーが発生しました", description="操作する前にボイスチャンネルに接続してください")
            return await ctx.channel.send(embed=embed)

        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            embed = discord.Embed(colour=0xff0000, title="エラーが発生しました", description="Botがボイスチャンネルに接続していません")
            await ctx.channel.send(embed=embed)
            return

        # 再生中ではない場合は実行しない
        if not ctx.guild.voice_client.is_playing():
            embed = discord.Embed(colour=0xff0000, title="エラーが発生しました", description="再生していません")
            await ctx.channel.send(embed=embed)
            return

        ctx.guild.voice_client.stop()
        embed = discord.Embed(colour=0xff00ff, title="スキップします")
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def shuffle(self, ctx):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            embed = discord.Embed(colour=0xff0000, title="エラーが発生しました", description="操作する前にボイスチャンネルに接続してください")
            return await ctx.channel.send(embed=embed)

        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            embed = discord.Embed(colour=0xff0000, title="エラーが発生しました", description="Botがボイスチャンネルに接続していません")
            await ctx.channel.send(embed=embed)
            return

        # 再生中ではない場合は実行しない
        if not ctx.guild.voice_client.is_playing():
            embed = discord.Embed(colour=0xff0000, title="エラーが発生しました", description="再生していません")
            await ctx.channel.send(embed=embed)
            return

        random.shuffle(self.queue)
        embed = discord.Embed(colour=0xff00ff, title="キューをシャッフルしました")
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def stop(self, ctx):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            embed = discord.Embed(colour=0xff0000, title="エラーが発生しました", description="操作する前にボイスチャンネルに接続してください")
            return await ctx.channel.send(embed=embed)

        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            embed = discord.Embed(colour=0xff0000, title="エラーが発生しました", description="Botがボイスチャンネルに接続していません")
            await ctx.channel.send(embed=embed)
            return

        # 再生中ではない場合は実行しない
        if not ctx.guild.voice_client.is_playing():
            embed = discord.Embed(colour=0xff0000, title="エラーが発生しました", description="再生していません")
            await ctx.channel.send(embed=embed)
            return

        self.queue.clear()
        ctx.guild.voice_client.stop()
        embed = discord.Embed(colour=0xff00ff, title="再生を停止します")
        await ctx.channel.send(embed=embed)


# Bot起動時に実行される関数
@bot.event
async def on_ready():
    now_time = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    await bot.change_presence(activity=discord.Game(name="ギラティナ、オォン！"))

    time.sleep(5)

    await bot.change_presence(activity=discord.Game(name=f"{now_time.strftime('%Y/%m/%d %H:%M:%S')} - オォン"))


# https://techblog.cartaholdings.co.jp/entry/archives/6412
# チャンネル入退室時の通知処理
@bot.event
async def on_voice_state_update(member, before, after):
    # チャンネルへの入室ステータスが変更されたとき（ミュートON、OFFに反応しないように分岐）
    if before.channel != after.channel:
        # 通知メッセージを書き込むテキストチャンネル（チャンネルIDを指定）
        notification_channel = bot.get_channel(VOICECHAT_NOTIFICATION_CHANNEL_ID)

        # 入退室を監視する対象のボイスチャンネル（チャンネルIDを指定）
        SEIBARI_VOICE_CHANNEL_IDs = [889049222152871990, 889251836312309800, 938212082363539526, 889312365466775582, 934783864226844682, 934783998935302214, 938212160075628624, 956176543850311700,
                                     988470466249359461, 1005195693465538591, 1001860023917477908, 937319677162565672, 890539305276174357]

        # 終了通知
        if before.channel is not None and before.channel.id in SEIBARI_VOICE_CHANNEL_IDs:
            if len(before.channel.members) == 0:
                embed = discord.Embed(colour=0xff00ff, title="通知", description="**" + before.channel.name + "** の通話が終了しました")
                await notification_channel.send(embed=embed)
        # 開始通知
        if after.channel is not None and after.channel.id in SEIBARI_VOICE_CHANNEL_IDs:
            if len(after.channel.members) == 1:
                embed = discord.Embed(colour=0xff00ff, title="通知", description="**" + after.channel.name + "** の通話が開始しました")
                await notification_channel.send(embed=embed)


# メッセージ送信時に実行される関数
@bot.event
async def on_message(ctx):
    # 送信者がBotである場合は弾く
    # ここで弾けば以降は書かなくて良さそう
    if ctx.author.bot:
        return

    if ctx.guild.id == PASOJIN_GUILD_ID:
        return

    # メッセージの本文が big brother だった場合
    if "big brother" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942107244349247488/9BD8903B-74D1-4740-8EC8-13110C0D943C.jpg")

    # メッセージの本文が somunia だった場合
    if "somunia" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://twitter.com/aaruaika/status/1518874935024054272")

    # メッセージの本文が アーメン だった場合
    if "アーメン" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://media.discordapp.net/attachments/964831309627289620/1012764896900956281/unknown.png")

    # メッセージの本文が いい曲 だった場合
    if "いい曲" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942071776815480832/unknown.png")

    # メッセージの本文が おはよう だった場合
    if "おはよう" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942108884275982426/FJxaIJIaMAAlFYc.png")

    # メッセージの本文が カニ だった場合
    if "かに" in str(ctx.content) or "カニ" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://media.discordapp.net/attachments/964831309627289620/1006257985846263808/6C4D7AD5-ADBA-4BC7-824C-5A118E09A43A.png")

    # メッセージの本文が クワガタ だった場合
    if "くわがた" in str(ctx.content) or "クワガタ" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        images_kuwagata = [
            "https://cdn.discordapp.com/attachments/959475816209739796/1000340129703006218/14C3BEA6-F0E3-4046-97E7-2D37732A3F75.png",
            "https://media.discordapp.net/attachments/991551726308048896/1012775482955145347/Fa_-bj2aUAALUIr.png"
        ]
        image_pickup = random.choice(images_kuwagata)
        await ctx.channel.send(image_pickup)

    # ドナルドの言葉狩り - https://qiita.com/sizumita/items/9d44ae7d1ce007391699
    # メッセージの本文が ドナルド だった場合
    if "ドナルド" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://tenor.com/view/ronald-mcdonald-insanity-ronald-mcdonald-gif-21974293")

    # メッセージの本文が バキ だった場合
    if "バキ" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/934792442178306108/942106647927595008/unknown.png")

    # メッセージの本文が メタ だった場合
    if "メタ" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942109742782889994/GWHiBiKi_StYle_9_-_YouTube_1.png")

    # メッセージの本文が やんぱ だった場合
    if "やんぱ" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("やんぱ2")

    # メッセージの本文が ライカ だった場合
    if "ライカ" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("はぁ、どちら様ですか？")

    # メッセージの本文が ランキング だった場合
    if "ランキング" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942109619243864085/E8sV781VIAEtwZq.png")

    # メッセージの本文が 一週間 だった場合
    if "一週間" in str(ctx.content) or "1週間" in str(ctx.content):
        yamadahouse_thumbnails = []

        # サムネイルをAPIで取得
        yamadahouse_response = youtube.search().list(channelId="UCmEG6Kw9z2PJM2yjQ1VQouw", part="snippet", maxResults=50).execute()

        for item in yamadahouse_response.get("items", []):
            # 一番高画質なサムネイルのキーを取得
            yamadahouse_highres_thumb = list(item["snippet"]["thumbnails"].keys())[-1]
            # サムネイルのURLだけを抽出して配列に突っ込む
            yamadahouse_thumbnails.append(item["snippet"]["thumbnails"][yamadahouse_highres_thumb]["url"])

        # サムネイルURLの配列内から1つランダムで選ぶ
        yamadahouse_random_thumb = random.choice(yamadahouse_thumbnails)

        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send(yamadahouse_random_thumb)

    # メッセージの本文が 君しかいないんだよ だった場合
    if "君しかいないんだよ" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        ydl_opts_you = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "outtmpl": "you.mp3",
        }
        with YoutubeDL(ydl_opts_you) as ydl:
            ydl.download(["https://soundcloud.com/kejiramikitanai/h9jsjiorr7ln"])
        # ボイスチャンネルに接続する
        if ctx.author.voice is None:
            return
        if ctx.guild.voice_client is None:
            await ctx.author.voice.channel.connect()
        # 音声を再生する
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio("you.mp3"))
        # 音声が再生中か確認する
        while ctx.guild.voice_client.is_playing():
            await asyncio.sleep(1)
        # 切断する
        await ctx.guild.voice_client.disconnect()

    # メッセージの本文が 死んだ だった場合
    if "死んだ" in str(ctx.content) or "しんだ" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/941239897400950794/newdance-min.gif")

    # メッセージの本文が 昼 だった場合
    if "昼" in str(ctx.content) or "おひる" in str(ctx.content):
        images = [
            "https://cdn.discordapp.com/attachments/1002875196522381325/1003699645458944011/FTakxQUaIAAoyn3CUnetnoise_scaleLevel2x4.000000.png",
            "https://cdn.discordapp.com/attachments/1002875196522381325/1008245051077443664/FZmJ06EUIAAcZNi.jpg"
        ]
        image_pickup = random.choice(images)
        await ctx.channel.send(image_pickup)

    # メッセージの本文が 風呂 だった場合
    if "風呂" in str(ctx.content) or "ふろ" in str(ctx.content):
        # あるくおすしの場合
        if ctx.author.id == WALKINGSUSHIBOX_USER_ID:
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942389072117256192/19ffe7f2e7464263.png")
        # あるくおすし以外の場合
        # 俺か俺以外か（by あるくおすし）   
        else:
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/943155933343785040/d9ce03af4958b0b7.png")

    if ctx.attachments and ctx.channel.id == WIP_CHANNEL_ID:
        for attachment in ctx.attachments:
            # Attachmentの拡張子がmp3, wavのどれかだった場合
            # https://discordpy.readthedocs.io/ja/latest/api.html#attachment
            if "audio" in attachment.content_type:
                await attachment.save("resources/temporary/wip_input.mp3")
                command = "ffmpeg -y -loop 1 -i resources/wip_input.jpg -i resources/temporary/wip_input.mp3 -vcodec libx264 -vb 50k -acodec aac -strict experimental -ab 128k -ac 2 -ar 48000 -pix_fmt yuv420p -shortest resources/temporary/wip_output.mp4"
                proc = await asyncio.create_subprocess_exec(*command.split(" "), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                stdout, stderr = await proc.communicate()
                await ctx.channel.send(file=discord.File("resources/temporary/wip_output.mp4"))
                os.remove("resources/temporary/wip_input.mp3")
                os.remove("resources/temporary/wip_output.mp4")

    # 検索欄チャンネルに投稿されたメッセージから、TwitterAPIを通してそのメッセージを検索して、チャンネルに画像を送信する
    # if ctx.content and ctx.channel.id == TWITTER_SEARCH_CHANNEL_ID:
    #     tweets = twapi.search_tweets(q=f"filter:images {arg}", tweet_mode="extended", include_entities=True, count=1)
    #     for tweet in tweets:
    #         media = tweet.extended_entities["media"]
    #         for m in media:
    #             origin = m["media_url"]
    #     await ctx.channel.send(origin)

    # n575
    # https://gist.github.com/4geru/46f300e561374833646ffd8f4b916672
    # if not ctx.author.bot:
    #     m = MeCab.Tagger()
    #     print(str(ctx.content))
    #     print(m.parse(str(ctx.content)))
    # check = [5, 7, 5]  # 5, 7, 5
    # check_index = 0
    # word_cnt = 0
    # node = m.parseToNode(str(ctx.content))
    # # # suggestion文の各要素の品詞を確認
    # while node:
    #     feature = node.feature.split(",")[0]
    #     surface = node.surface.split(",")[0]
    #     print(feature)
    #     print(surface)
    #     # 記号, BOS/EOSはスルー
    #     if feature == "記号" or feature == "BOS/EOS":
    #         node = node.next
    #         continue
    #     # 文字数をカウント
    #     word_cnt += len(surface)
    #     # 字数チェック
    #     if word_cnt == check[check_index]:
    #         check_index += 1
    #         word_cnt = 0
    #         continue
    #     # 字余りチェック
    #     elif word_cnt > check[check_index]:
    #         return False
    #
    #     # [5, 7, 5] の長さになっているか
    #     if check_index == len(check) - 1:
    #         return True
    #     node = node.next
    # print("俳句を見つけました！")
    # return False

    await bot.process_commands(ctx)


# アニクトから取得したアニメをランダムで表示
@bot.command(aliases=["ani"])
async def anime(ctx):
    random_id = random.randint(1, 9669)
    # エンドポイント
    annict_url = f"https://api.annict.com/v1/works?access_token={ANNICT_API_KEY}&filter_ids={random_id}"
    # リクエスト
    annict_res = requests.get(annict_url)
    # 取得したjsonから必要な情報を取得
    annict_works = annict_res.json()["works"][0]
    annict_works_title = annict_works["title"]
    annict_works_season_name_text = annict_works["season_name_text"]
    annict_works_episodes_count = annict_works["episodes_count"]
    annict_works_images_recommended_url = annict_works["images"]["recommended_url"]
    await ctx.channel.send(f"{annict_works_title}({annict_works_season_name_text}-{annict_works_episodes_count}話)\nhttps://annict.com/works/{random_id}")


# bokuseku.mp3 流し逃げ - https://qiita.com/sizumita/items/cafd00fe3e114d834ce3
@bot.command()
async def bokuseku(ctx):
    if ctx.author.voice is None:
        await ctx.channel.send("望月くん・・・ボイスチャンネルに来なさい")
        return

    # ボイスチャンネルに接続する
    if ctx.guild.voice_client is None:
        await ctx.author.voice.channel.connect()
    # 音声を再生する
    ctx.guild.voice_client.play(discord.FFmpegPCMAudio("resources/bokuseku.mp3"))
    # 音声が再生中か確認する
    while ctx.guild.voice_client.is_playing():
        await asyncio.sleep(1)
    # 切断する
    await ctx.guild.voice_client.disconnect()


# チーバくんの、なのはな体操
@bot.command()
async def chiibakun(ctx):
    await ctx.channel.send("https://www.youtube.com/watch?v=dC0eie-WQss")


# ファルコおもしろ画像を送信
@bot.command(aliases=["syai", "faruko"])
async def falco(ctx):
    guild = bot.get_guild(SEIBARI_GUILD_ID)

    channel = guild.get_channel(FALCO_CHANNEL_ID)

    falco_channel_messages = [message async for message in channel.history(limit=None)]

    random_falco = random.choice(falco_channel_messages)

    content = random_falco.attachments[0].url if random_falco.content == "" else random_falco.content

    # メッセージが送られてきたチャンネルに送る
    await ctx.channel.send(content)


# ファミ通
@bot.command(aliases=["fami", "famitu", "fami2"])
async def famitsu(ctx):
    texts = []
    tweets = twapi.search_tweets(q="from:@fami2repo_bot", count=10)
    for tweet in tweets:
        text = tweet.text
        texts.append(text)
    text_pickup = random.choice(texts)
    await ctx.channel.send(text_pickup)


# Twitterから#GenshinImpactの1000いいね以上を探して送信
@bot.command(aliases=["gennshinn", "gensin", "gennsinn", "gs"])
async def genshin(ctx):
    tweets = twapi.search_tweets(q=f"filter:images min_faves:1000 #GenshinImpact", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.extended_entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


# ギラティナの画像を送る
@bot.command()
async def giratina(ctx):
    await ctx.channel.send("https://img.gamewith.jp/article/thumbnail/rectangle/36417.png")


# no context hentai imgの画像を送信
@bot.command()
async def hentai(ctx):
    guild = bot.get_guild(SIRONEKO_GUILD_ID)

    channel = guild.get_channel(NO_CONTEXT_HENTAI_IMG_CHANNEL_ID)

    hentai_channel_messages = [message async for message in channel.history(limit=None)]

    random_hentai = random.choice(hentai_channel_messages)

    content = random_hentai.attachments[0].url if random_hentai.content == "" else random_hentai.content

    # メッセージが送られてきたチャンネルに送る
    await ctx.channel.send(content)


# Twitterから#胡桃の1000いいね以上を探して送信
@bot.command(aliases=["kisshutao"])
async def hutao(ctx):
    tweets = twapi.search_tweets(q=f"filter:images min_faves:1000 #胡桃", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.extended_entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


# イキス
@bot.command()
async def inm(ctx):
    await ctx.channel.send(
        "聖バリ「イキスギィイクイク！！！ンアッー！！！マクラがデカすぎる！！！」\n\n"
        f"{ctx.author.name}「聖なるバリア －ミラーフォース－、淫夢はもうやめてよ！淫夢ごっこは恥ずかしいよ！」\n\n"
        f"聖バリ「{ctx.author.name}、おっ大丈夫か大丈夫か〜？？？バッチェ冷えてるぞ〜淫夢が大好きだってはっきりわかんだね」"
    )


# かおすちゃんを送信
@bot.command()
async def kaosu(ctx):
    tweets = twapi.search_tweets(q="from:@kaosu_pic", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


# こまちゃんを送信
@bot.command()
async def komachan(ctx):
    tweets = twapi.search_tweets(q="from:@komachan_pic", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


# らきすたを送信
# https://ja.stackoverflow.com/questions/56894/twitter-api-%e3%81%a7-%e5%8b%95%e7%94%bb%e3%83%84%e3%82%a4%e3%83%bc%e3%83%88-%e3%82%921%e4%bb%b6%e5%8f%96%e5%be%97%e3%81%97%e3%81%a6html%e4%b8%8a%e3%81%a7%e8%a1%a8%e7%a4%ba%e3%81%95%e3%81%9b%e3%81%9f%e3%81%84%e3%81%ae%e3%81%a7%e3%81%99%e3%81%8c-m3u8-%e5%bd%a2%e5%bc%8f%e3%81%a8-mp4-%e5%bd%a2%e5%bc%8f%e3%81%ae%e9%96%a2%e4%bf%82%e6%80%a7%e3%81%af
# https://syncer.jp/Web/API/Twitter/REST_API/Object/Entity/#:~:text=Filter-,%E3%83%84%E3%82%A4%E3%83%BC%E3%83%88%E3%82%AA%E3%83%96%E3%82%B8%E3%82%A7%E3%82%AF%E3%83%88%20(%E5%8B%95%E7%94%BB),-%E5%8B%95%E7%94%BB%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB%E3%82%92
@bot.command()
async def lucky(ctx):
    tweets = twapi.search_tweets(q="from:@LuckyStarPicBot", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)

    # 動画も取得して送信できるようにしたかったけど、うまくいってません
    # for tweet in tweets:
    #     media = tweet.extended_entities["media"]
    #     for m in media:
    #         if m["type"] == "video":
    #             for video_info in m:
    #                 for variants in video_info:
    #                     for url in variants[0]:
    #                         origin = url
    #                         await ctx.channel.send(origin)
    #         else:
    #             origin = m["media_url"]
    #             await ctx.channel.send(origin)


@bot.command()
async def ma(ctx):
    await ctx.channel.send("https://cdn.discordapp.com/attachments/964831309627289620/982691239025598494/long_ver.___feat._0s_screenshot.png")


# マチカネタンホイザの画像を送信
@bot.command(aliases=["matitan", "matikanetanhoiza"])
async def machitan(ctx):
    guild = bot.get_guild(SEIBARI_GUILD_ID)

    channel = guild.get_channel(MACHITAN_CHANNEL_ID)

    machitan_channel_messages = [message async for message in channel.history(limit=None)]

    random_machitan = random.choice(machitan_channel_messages)

    content = random_machitan.attachments[0].url if random_machitan.content == "" else random_machitan.content

    # メッセージが送られてきたチャンネルに送る
    await ctx.channel.send(content)


# マノム
@bot.command(aliases=["mano"])
async def manomu(ctx):
    await ctx.channel.send(
        "家で飼ってるピーちゃんを\n" +
        "　　　　使ったお料理も好きです。\n\n" +
        "　　　　　あ　ら　ま\n\n" +
        "動物性たんぱくパク　たべるルル\n\n" +
        "　　　　＼内臓もっと／\n\n" +
        "頂戴な　　　　　　　　　頂戴な\n" +
        "ねぇ　　　　　　　　　　　ねぇ\n\n" +
        "　　灯織ちゃんもおいでって"
    )


# アニクトから取得したキャラクターをランダムで表示
@bot.command()
async def odai(ctx):
    while 1:
        # 10個のランダムな数を生成
        random_ids = [str(random.randint(1, 41767)) for _ in range(10)]
        # リストの中の要素を結合する
        filter_ids = ",".join(random_ids)
        # エンドポイント
        annict_url = f"https://api.annict.com/v1/characters?access_token={ANNICT_API_KEY}&filter_ids={filter_ids}"
        # リクエスト
        annict_res = requests.get(annict_url)
        # 変数
        annict_characters = annict_res.json()["characters"]
        # シャッフルする
        random.shuffle(annict_characters)
        # お気に入り数が5以上の要素のみ抽出
        annict_characters_favorite_count = list(filter(lambda e: e["favorite_characters_count"] > 4, annict_characters))
        # 要素が0個では無い場合にループを解除
        if len(annict_characters_favorite_count) > 0:
            target_character = annict_characters_favorite_count[0]
            break

    # 共通の要素
    annict_character_name = target_character["name"]
    annict_character_id = target_character["id"]
    annict_character_fan = target_character["favorite_characters_count"]

    # 送信するメッセージの変数の宣言
    annict_character_msg = f"{annict_character_name} - ファン数{annict_character_fan}人\nhttps://annict.com/characters/{annict_character_id}"

    # シリーズの記載がある場合
    if target_character["series"] is not None:
        annict_character_series = target_character["series"]["name"]
        # 送信するメッセージの変数にシリーズを入れたテキストを代入
        annict_character_msg = f"{annict_character_name}({annict_character_series}) - ファン数{annict_character_fan}人\nhttps://annict.com/characters/{annict_character_id}"

    await ctx.channel.send(annict_character_msg)


# ピンポン
@bot.command()
async def ping(ctx):
    latency = bot.latency
    latency_milli = round(latency * 1000)
    await ctx.channel.send(f"Pong!: {latency_milli}ms")


# Raika
@bot.command()
async def raika(ctx):
    txtfile = open("resources/Wonderful_Raika_Tweet.txt", "r", encoding="utf-8")
    word = ",".join(list(map(lambda s: s.rstrip("\n"), random.sample(txtfile.readlines(), 1)))).replace("["", "").replace(""]", "")
    url = [word]
    pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    for url in url:
        if re.match(pattern, url):
            await ctx.channel.send(requests.get(url).url)
        else:
            await ctx.channel.send(word)


# raikaマルコフ
# https://monachanpapa-scripting.com/marukofu-python/ほぼ丸コピですすみません...
@bot.command()
async def mraika(ctx):
    def parse_words(test_data):
        with open("resources/Wonderful_Raika_Tweet.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        t = MeCab.Tagger("-Owakati")
        datas = []
        for line in lines:
            data = t.parse(line).strip()
            datas.append(data)
        datas = [f"__BEGIN__ {data} __END__" for data in datas]
        datas = [data.split() for data in datas]
        return datas

    def create_words_cnt_dic(datas):
        words = []
        for data in datas:
            words.extend(list(ngrams(data, 3)))
        words_cnt_dic = Counter(words)
        return words_cnt_dic

    def create_m_dic(words_cnt_dic):
        m_dic = {}
        for k, v in words_cnt_dic.items():
            two_words, next_word = k[:2], k[2]
            if two_words not in m_dic:
                m_dic[two_words] = {"words": [], "weights": []}
            m_dic[two_words]["words"].append(next_word)
            m_dic[two_words]["weights"].append(v)
        return m_dic

    def create_begin_words_weights(words_cnt_dic):
        begin_words_dic = defaultdict(int)
        for k, v in words_cnt_dic.items():
            if k[0] == "__BEGIN__":
                next_word = k[1]
                begin_words_dic[next_word] = v
        begin_words = [k for k in begin_words_dic.keys()]
        begin_weights = [v for v in begin_words_dic.values()]
        return begin_words, begin_weights

    def create_sentences(m_dic, begin_words, begin_weights):
        begin_word = random.choices(begin_words, weights=begin_weights, k=1)[0]
        sentences = ["__BEGIN__", begin_word]
        while True:
            back_words = tuple(sentences[-2:])
            words, weights = m_dic[back_words]["words"], m_dic[back_words]["weights"]
            next_word = random.choices(words, weights=weights, k=1)[0]
            if next_word == "__END__":
                break
            sentences.append(next_word)
        return "".join(sentences[1:])

    datas = parse_words("osake.txt")
    words_cnt_dic = create_words_cnt_dic(datas)
    m_dic = create_m_dic(words_cnt_dic)
    begin_words, begin_weights = create_begin_words_weights(words_cnt_dic)
    for i in range(1):
        text = create_sentences(m_dic, begin_words, begin_weights)
        await ctx.channel.send(text)


# おしゃべりひろゆきメーカーの実装。リリース半日クオリティーなので許してください
@bot.command()
async def hiroyuki(ctx, *arg):
    if arg:
        text = arg[0]
        embed = discord.Embed(colour=0xff00ff, title=f"{text}を生成中です...")
        hiroyuki_msg: discord.Message = await ctx.channel.send(embed=embed)
        headers = {
            "authority": "tgeedx93af.execute-api.ap-northeast-1.amazonaws.com",
            "accept": "application/json, text/plain, */*"
        }
        json_data = {
            "coefont": "19d55439-312d-4a1d-a27b-28f0f31bedc5",
            "text": f"{text}",
        }
        response = requests.post("https://tgeedx93af.execute-api.ap-northeast-1.amazonaws.com/production/hiroyuki/text2speech", headers=headers, json=json_data)
        status = response.json()["statusCode"]
        if status == 200:
            key = response.json()["body"]["wav_key"]
            headers2 = {
                "authority": "johwruw0ic.execute-api.ap-northeast-1.amazonaws.com",
                "accept": "application/json, text/plain, */*"
            }
            json_data2 = {
                "voice_key": f"{key}",
            }
            response2 = requests.post("https://johwruw0ic.execute-api.ap-northeast-1.amazonaws.com/production/hiroyuki_video", headers=headers2, json=json_data2)
            url = response2.json()["body"]["url"]
            embed = discord.Embed(colour=0x4db56a, title=f"音声の生成に成功しました")
            await hiroyuki_msg.edit(embed=embed)
            response = requests.get(url)
            file = open("temp.mp4", "wb")
            for chunk in response.iter_content(100000):
                file.write(chunk)
            file.close()
            stream = ffmpeg.input("temp.mp4")
            stream = ffmpeg.output(stream, "hiroyuki.mp3")
            ffmpeg.run(stream)
            await ctx.channel.send(file=discord.File("hiroyuki.mp3"))
            embed0 = discord.Embed(colour=0x4db56a, title=f"動画 {gdshortener.ISGDShortener().shorten(url=url)[0]}")
            hiroyuki0_msg: discord.Message = await ctx.channel.send(embed=embed0)
            os.remove("temp.mp4")
            os.remove("hiroyuki.mp3")
            return
        else:
            embed = discord.Embed(colour=0xff0000, title="生成に失敗しました")
            await hiroyuki_msg.edit(embed=embed)
            return
    if not arg:
        embed = discord.Embed(colour=0xff0000, title=f"文字を入力してください")
        hiroyuki_msg: discord.Message = await ctx.channel.send(embed=embed)


# hiroyuki talk
@bot.command()
async def htalk(ctx, *arg):
    if arg:
        text = arg[0]
        embed = discord.Embed(colour=0xff00ff, title=f"{text}を生成中です...")
        hiroyuki_msg: discord.Message = await ctx.channel.send(embed=embed)
        headers = {
            "authority": "tgeedx93af.execute-api.ap-northeast-1.amazonaws.com",
            "accept": "application/json, text/plain, */*"
        }
        json_data = {
            "coefont": "19d55439-312d-4a1d-a27b-28f0f31bedc5",
            "text": f"{text}",
        }
        response = requests.post("https://tgeedx93af.execute-api.ap-northeast-1.amazonaws.com/production/hiroyuki/text2speech", headers=headers, json=json_data)
        status = response.json()["statusCode"]
        if status == 200:
            embed = discord.Embed(colour=0x4db56a, title=f"音声の生成に成功しました")
            await hiroyuki_msg.edit(embed=embed)
            key = response.json()["body"]["wav_key"]
            headers2 = {
                "authority": "johwruw0ic.execute-api.ap-northeast-1.amazonaws.com",
                "accept": "application/json, text/plain, */*"
            }
            json_data2 = {
                "voice_key": f"{key}",
            }
            response2 = requests.post("https://johwruw0ic.execute-api.ap-northeast-1.amazonaws.com/production/hiroyuki_video", headers=headers2, json=json_data2)
            url = response2.json()["body"]["url"]
            embed = discord.Embed(colour=0x4db56a, title=f"動画の生成に成功しました")
            await hiroyuki_msg.edit(embed=embed)
            response = requests.get(url)
            file = open("temp.mp4", "wb")
            for chunk in response.iter_content(100000):
                file.write(chunk)
            file.close()
            stream = ffmpeg.input("temp.mp4")
            stream = ffmpeg.output(stream, "temp.mp3")
            ffmpeg.run(stream)
            if ctx.author.voice is None:
                await ctx.channel.send("なんだろう")
                return
            # ボイスチャンネルに接続する
            if ctx.guild.voice_client is None:
                await ctx.author.voice.channel.connect()
            # 音声を再生する
            ctx.guild.voice_client.play(discord.FFmpegPCMAudio("temp.mp3"))
            # 音声が再生中か確認する
            while ctx.guild.voice_client.is_playing():
                await asyncio.sleep(1)
            # 切断する
            await ctx.guild.voice_client.disconnect()
            os.remove("temp.mp4")
            os.remove("temp.mp3")
            return
        else:
            embed = discord.Embed(colour=0xff0000, title="生成に失敗しました")
            await hiroyuki_msg.edit(embed=embed)
            return
    if not arg:
        embed = discord.Embed(colour=0xff0000, title=f"文字を入力してください")
        hiroyuki_msg: discord.Message = await ctx.channel.send(embed=embed)


# mp4
@bot.command()
async def mp4(ctx):
    if ctx.message.reference is None:
        await ctx.reply("動画にしたい音声に返信してください", mention_author=False)
        return

    mes = await ctx.channel.fetch_message(ctx.message.reference.message_id)

    if mes.attachments is None:
        await ctx.reply("返信元のメッセージにファイルが添付されていません", mention_author=False)
        return

    await mes.attachments[0].save("resources/temporary/wip_input.mp3")
    mes_pros = await ctx.reply("処理中です…", mention_author=False)
    command = "ffmpeg -y -loop 1 -i resources/wip_input.jpg -i resources/temporary/wip_input.mp3 -vcodec libx264 -vb 50k -acodec aac -strict experimental -ab 128k -ac 2 -ar 48000 -pix_fmt yuv420p -shortest resources/temporary/wip_output.mp4"
    proc = await asyncio.create_subprocess_exec(*command.split(" "), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    await mes_pros.delete()
    await ctx.channel.send(file=discord.File("resources/temporary/wip_output.mp4"))
    os.remove("resources/temporary/wip_input.mp3")
    os.remove("resources/temporary/wip_output.mp4")


# removebg
@bot.command()
async def removebg(ctx):
    removebg_apikey = os.getenv("REMOVEBG_APIKEY")

    if ctx.message.reference is None:
        await ctx.reply("加工したい画像に返信してください", mention_author=False)
        return

    mes = await ctx.channel.fetch_message(ctx.message.reference.message_id)

    if mes.attachments is None:
        await ctx.reply("返信元のメッセージにファイルが添付されていません", mention_author=False)
        return

    await mes.attachments[0].save("temp_removebg_input.png")

    mes_pros = await ctx.reply("処理中です…", mention_author=False)

    # RemoveBgAPI
    response = requests.post(
        "https://api.remove.bg/v1.0/removebg",
        files={"image_file": open("temp_removebg_input.png", "rb")},
        data={"size": "auto"},
        headers={"X-Api-Key": removebg_apikey},
    )
    await mes_pros.delete()

    if response.status_code == requests.codes.ok:
        with open("removebg_temp_output.png", "wb") as out:
            out.write(response.content)
            await ctx.send(file=discord.File("removebg_temp_output.png"))
            os.remove("temp_removebg_input.png")
            os.remove("removebg_temp_output.png")
    else:
        await ctx.send(f"Error:{response.status_code} {response.text}")


# サターニャを送信
@bot.command()
async def satanya(ctx):
    tweets = twapi.search_tweets(q="from:@satanya_gazobot", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


# おすしを送信
@bot.command(aliases=["osushi"])
async def sushi(ctx):
    tweets = twapi.search_tweets(q="from:@kasakioiba", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


# ファルコおもしろ画像を送信
@bot.command(aliases=["teiou", "teio", "teio-"])
async def toukaiteiou(ctx):
    guild = bot.get_guild(SEIBARI_GUILD_ID)

    channel = guild.get_channel(TEIOU_CHANNEL_ID)

    teiou_channel_messages = [message async for message in channel.history(limit=None)]

    random_teiou = random.choice(teiou_channel_messages)

    content = random_teiou.attachments[0].url if random_teiou.content == "" else random_teiou.content

    # メッセージが送られてきたチャンネルに送る
    await ctx.channel.send(content)


# https://zenn.dev/zakiii/articles/7ada80144c9db0
# https://qiita.com/soma_sekimoto/items/65c664f00573284b0b74
# TwitterのIDを指定して最新の画像を送信
@bot.command(aliases=["tw"])
async def twitter(ctx, *, arg):
    tweets = twapi.search_tweets(q=f"filter:images {arg}", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.extended_entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


@bot.command(aliases=["twdl"])
async def twitterdl(ctx, *, arg):
    tweet_url = f"{arg}"
    # URLからツイートIDを取得する正規表現
    # https://stackoverflow.com/questions/45282238/getting-a-tweet-id-from-a-tweet-link-using-tweepy
    tweet_id = tweet_url.split("/")[-1].split("?")[0]
    is_twitter = tweet_url.startswith("https://twitter.com")

    if is_twitter:
        tweet_status = twapi.get_status(id=int(tweet_id), tweet_mode="extended", include_entities=True)

        status = tweet_status
        for media in status.extended_entities.get("media", [{}]):
            if media.get("type", None) == "video":
                video = media["video_info"]["variants"]
                sorted_video = sorted(
                    video,
                    key=lambda x: x.get("bitrate", 0),  # bitrateの値がない場合にエラーが出るので0を代入して大きい順にソートする
                    reverse=True  # 降順にする
                )
                video_url = sorted_video[0]["url"]
        await ctx.channel.send(video_url)


    else:
        embed = discord.Embed(colour=0xff00ff, title="TwitterのURLを貼ってください")
        discord.Message = await ctx.channel.send(embed=embed)


# ウマ娘ガチャシミュレーター
@bot.command()
async def uma(ctx):
    async def send_uma(channel, author):
        class Chara:
            #アイコン画像の数字に一致
            id = 0
            rarity = 0
            is_pickup = 0

            def __init__(self, id, rarity, is_pickup):
                self.id = id
                self.rarity = rarity
                self.is_pickup = is_pickup

        class Gacha_Usage:
            user = ""
            chara_id_list = []
            exchange_point = 0

            def __init__(self, user, ids, exchange_point):
                self.user = user
                self.chara_id_list = ids
                self.exchange_point = exchange_point
        
        chara_list = []
        usage_list = []
        path_uma_gacha = "resources/uma_gacha"
        path_output = f"resources/temporary/uma_gacha_{channel.id}.png"
        path_csv = "resources/csv"
        path_font = ".fonts/rodin_wanpaku_eb.otf"
        fontsize = 32
        region_particle = modules.img.Region([modules.img.Rect(0, 30, 32, 236), modules.img.Rect(32, 30, 207, 56), modules.img.Rect(207, 30, 240, 236)])

        async with channel.typing():
            # CSVファイルからキャラ情報を読み込み
            with open(f"{path_csv}/uma_chara_info.csv") as f:
                reader = csv.reader(f)
                for row in reader:
                    chara = Chara(int(row[0]), int(row[1]), int(row[2]))
                    chara_list.append(chara)

            # CSVファイルからガチャ使用情報を読み込み
            with open(f"{path_csv}/uma_gacha_usage.csv") as f:
                reader = csv.reader(f)
                for row in reader:
                    u = Gacha_Usage(int(row[0]), [int(s) for s in row[1].split("/")], int(row[2]))
                    usage_list.append(u)

            # コマンド使用者がガチャ使用情報に載っているか確認
            chara_id_list = []
            exchange_point = 0
            for i, u in enumerate(usage_list):
                if author.id == u.user:
                    chara_id_list = u.chara_id_list
                    exchange_point = u.exchange_point
                    usage_list.pop(i)
                

            # 確率比[★1, ★2, ★3]
            weights = [79, 18, 3]
            # 確率比(10回目)
            weights_10 = [0, 97, 3]
            
            # 画像の初期化
            g_img = modules.img.Giratina_Image()
            g_img.load(f"{path_uma_gacha}/bg.png")

            for i in range(10):
                w = weights if i < 9 else weights_10

                chara_results_by_rarity = []

                # レア度1はピックアップが存在しないため等確率で選出
                chara_results_by_rarity.append(random.choice([ch for ch in chara_list if ch.rarity == 1]))

                # レア度2以降はピックアップの有無ごとに選出
                for r in range(2, 4):
                    list_pickup = [ch for ch in chara_list if ch.rarity == r and ch.is_pickup]
                    list_not_pickup = [ch for ch in chara_list if ch.rarity == r and not ch.is_pickup]
                    # ピックアップ1体ごとの確率
                    prob_pickup = 0.75 if r == 3 else 2.25
                    # ピックアップが存在する場合
                    if len(list_pickup):
                        chara_results_by_pickup = random.choices(
                            [list_pickup, list_not_pickup],
                            weights=[
                                len(list_pickup) * prob_pickup,
                                w[r - 1] - len(list_pickup) * prob_pickup
                            ]
                            )[0]
                        chara_results_by_rarity.append(random.choice(chara_results_by_pickup))
                    # ピックアップが存在しない場合
                    else:
                        chara_results_by_rarity.append(random.choice([ch for ch in chara_list if ch.rarity == r]))

                # 最終的な排出ウマ娘を決定
                chara_result = random.choices(chara_results_by_rarity, weights=w)[0]

                # アイコン画像をchara_iconフォルダから読み込み&貼り付け
                chara_icon = Image.open(f"{path_uma_gacha}/chara_icon/{chara_result.id}.png")

                x = 0
                y = 0
                # 3つ並びの行
                if i % 5 < 3:
                    x = 96 + 324 * (i % 5)
                    y = 157 + 724 * (i // 5)
                # 2つ並びの行
                else:
                    x = 258 + 324 * (i % 5 - 3)
                    y = 519 + 724 * (i // 5)

                g_img.composit(chara_icon, (x, y))

                piece_x = 0
                bonus_x = 0
                num_piece = 0
                num_megami = 0
                text_piece_x = 0
                
                if chara_result.rarity == 3:
                    num_megami = 20
                    if chara_result.is_pickup:
                        num_piece = 90
                    else:
                        num_piece = 60
                elif chara_result.rarity == 2:
                    num_megami = 3
                    num_piece = 10
                else:
                    num_megami = 1
                    num_piece = 5

                # 排出ウマ娘が獲得済みの場合
                if chara_result.id in chara_id_list:
                    adjust_x = -11 if chara_result.rarity == 2 else 0
                    # 女神像
                    megami = Image.open(f"{path_uma_gacha}/icon_megami.png")
                    megami_x = 4 if chara_result.rarity == 3 else 26
                    g_img.composit(megami, (x + megami_x + adjust_x, y + 300))

                    # ピース・おまけの位置
                    piece_x = 130 + adjust_x
                    bonus_x = 134 + adjust_x
                    text_piece_x = 182 + adjust_x

                    # テキスト(女神像)
                    text_megami_x = 54 if chara_result.rarity == 3 else 76
                    g_img.drawtext(f"x{num_megami}", (x + text_megami_x + adjust_x, y + 311), fill=(124, 63, 18), anchor="lt", fontpath=path_font, fontsize=fontsize, stroke_width=2, stroke_fill="white")

                # 未獲得の場合
                else:
                    chara_id_list.append(chara_result.id)
                    # NEW!
                    label_new = Image.open(f"{path_uma_gacha}/label_new.png")
                    g_img.composit(label_new, (x - 22, y))

                    adjust_x = 11 if chara_result.rarity == 1 else 0

                    # ピース・おまけの位置
                    piece_x = 65 + adjust_x
                    text_piece_x = 117 + adjust_x
                    bonus_x = 68 + adjust_x

                # テキスト(ピース)
                g_img.drawtext(f"x{num_piece}", (x + text_piece_x, y + 311), fill=(124, 63, 18), anchor="lt", fontpath=path_font, fontsize=fontsize, stroke_width=2, stroke_fill="white")

                # ピース
                piece = Image.open(f"{path_uma_gacha}/piece_icon/{chara_result.id}.png")
                g_img.composit(piece, (x + piece_x, y + 300))

                # おまけ
                label_bonus = Image.open(f"{path_uma_gacha}/label_bonus.png")
                g_img.composit(label_bonus, (x + bonus_x, y + 286))

                # レア度が3の場合枠を描画
                if chara_result.rarity == 3:
                    frame = Image.open(f"{path_uma_gacha}/frame.png")
                    g_img.composit(frame, (x - 8, y))

                # パーティクルを描画
                if chara_result.rarity > 1:
                    num_stars = 7 if chara_result.rarity == 3 else 5
                    particle = Image.open(f"{path_uma_gacha}/particle_{chara_result.rarity}.png")
                    particle_pos = None
                    for _ in range(num_stars):
                        scale = random.uniform(1, 3)
                        particle_resize = particle.resize((int(particle.width // scale) ,int(particle.height // scale)))
                        particle_pos = region_particle.randompos()
                        g_img.composit(particle_resize, (x - (particle_resize.width // 2) + particle_pos[0], y - (particle_resize.height // 2) + particle_pos[1]))

                # 星マークを貼り付け
                stars = Image.open(f"{path_uma_gacha}/stars_{chara_result.rarity}.png")
                g_img.composit(stars, (x + 46, y + 243))

            # 育成ウマ娘交換ポイント書き込み
            g_img.drawtext(str(exchange_point), (732, 1611), fill=(124, 63, 18), anchor="rt", fontpath=path_font, fontsize=fontsize)
            exchange_point += 10
            g_img.drawtext(str(exchange_point), (860, 1611), fill=(255, 145, 21), anchor="rt", fontpath=path_font, fontsize=fontsize)

            # リザルト画面の保存&読み込み
            g_img.write(path_output)
            gacha_result_image = discord.File(path_output)
            
            # ボタンのサブクラス
            class Button_Uma(discord.ui.Button):
                async def callback(self, interaction):
                    response = interaction.response
                    await response.edit_message(view=None)
                    await send_uma(interaction.channel, interaction.user)

            button = Button_Uma(style=discord.ButtonStyle.success, label="もう一回引く")

            view = discord.ui.View()
            view.timeout = None
            view.add_item(button)

            # メッセージを送信
            await channel.send(content=f"<@{author.id}>", file=gacha_result_image, view=view)

        # 生成した画像を削除
        if os.path.isfile(path_output):
            os.remove(path_output)

        # ガチャ使用情報を更新
        usage = Gacha_Usage(author.id, chara_id_list, exchange_point)
        usage_list.append(usage)

        with open(f"{path_csv}/uma_gacha_usage.csv", "w") as f:
            writer = csv.writer(f)
            for u in usage_list:
                writer.writerow([u.user, "/".join([str(n) for n in u.chara_id_list]), u.exchange_point])

    await send_uma(ctx.channel, ctx.author)


# ゆるゆりを送信
@bot.command()
async def yuruyuri(ctx):
    tweets = twapi.search_tweets(q="from:@YuruYuriBot1", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


bot.add_cog(Music(bot_arg=bot))
bot.run(DISCORD_BOT_TOKEN)
