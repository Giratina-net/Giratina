import asyncio
from collections import defaultdict
import discord
from discord.ext import commands
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from niconico import NicoNico
from os import getenv
import random
import re
import requests
from spotdl import Spotdl
import typing
import yt_dlp


# spotdl
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET")
spotdl = Spotdl(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)

# google-api-python-client / YouTube Data API v3
YOUTUBE_API_KEY = getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


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
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_at_eof 1 -reconnect_delay_max 5",
    "options": "-vn"
}

# https://qiita.com/sizumita/items/cafd00fe3e114d834ce3
# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda: ""

ytdl = yt_dlp.YoutubeDL(YTDL_FORMAT_OPTIONS)


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
        self.queue: defaultdict[typing.List[typing.Union[YTDLSource, NicoNicoDLSource]]] = defaultdict(lambda: [])

    def after_play(self, guild, err):
        if type(self.player) == NicoNicoDLSource:
            self.player.close_connection()

        if err:
            return print(f"has error: {err}")

        if len(self.queue[guild.id]) <= 0:
            return

        self.player = self.queue[guild.id].pop(0)

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
        embed.set_footer(text=f"残りキュー: {len(self.queue[ctx.guild.id])}")
        # embed.set_footer(text=f"残りキュー: {len(self.queue[ctx.guild.id])} | ループ: {"有効" if self.loop else "無効"}")

        # サムネイルをAPIで取得
        if ctx.guild.voice_client.is_playing() and ("youtube.com" in self.player.original_url or "youtu.be" in self.player.original_url):
            np_youtube_video = youtube.videos().list(part="snippet", id=self.player.id).execute()
            np_thumbnail = np_youtube_video["items"][0]["snippet"]["thumbnails"]
            np_highres_thumbnail = list(np_thumbnail.keys())[-1]
            embed.set_thumbnail(url=np_thumbnail[np_highres_thumbnail]["url"])

        await ctx.channel.send(embed=embed)

    async def queue_sources(self, ctx, sources: list, play_msg):
        first_source = sources.pop(0)

        # キューへの追加
        if ctx.guild.voice_client.is_playing():  # 他の曲を再生中の場合
            # self.playerに追加すると再生中の曲と衝突する
            self.queue[ctx.guild.id].append(first_source)
            embed = discord.Embed(colour=0xff00ff, title="キューに追加しました", description=f"[{first_source.title}]({first_source.original_url})")
            await play_msg.edit(embed=embed)

        else:  # 他の曲を再生していない場合
            # self.playerにURLを追加し再生する
            self.player = first_source
            ctx.guild.voice_client.play(self.player, after=lambda e: self.after_play(ctx.guild, e))
            embed = discord.Embed(colour=0xff00ff, title="再生を開始します", description=f"[{first_source.title}]({first_source.original_url})")
            if type(first_source) == YTDLSource and ("youtube.com" in first_source.original_url or "youtu.be" in first_source.original_url):
                # サムネイルをAPIで取得
                try:
                    np_youtube_video = youtube.videos().list(part="snippet", id=first_source.id).execute()
                    if np_youtube_video["items"]:
                        np_thumbnail = np_youtube_video["items"][0]["snippet"]["thumbnails"]
                        np_highres_thumbnail = list(np_thumbnail.keys())[-1]
                        embed.set_thumbnail(url=np_thumbnail[np_highres_thumbnail]["url"])
                # APIキーの有効期限が切れてるとここに来る
                except HttpError:
                    pass
            await play_msg.edit(embed=embed)

        self.queue[ctx.guild.id].extend(sources)

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
        is_niconico_mylist = url.startswith("https://www.nicovideo.jp/mylist") or url.startswith("https://nico.ms/mylist") or re.match(r"https://www.nicovideo.jp/user/\d+/mylist", url)
        is_niconico = url.startswith("https://www.nicovideo.jp/") or url.startswith("https://nico.ms/")
        is_spotify = url.startswith("https://open.spotify.com/")

        target_sources = []

        # 各サービスごとに振り分け
        if is_niconico_mylist:
            niconico_client = NicoNico()
            items = []

            # 100件ごとに分割されているので全て取得してひとつのリストにまとめる
            for mylist_page in niconico_client.video.get_mylist(url):
                items.extend(mylist_page.items)

            for item in items:
                try:
                    source = await NicoNicoDLSource.from_url(item.video.url)
                    target_sources.append(source)
                # 400エラーだったら無視する
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 400:
                        continue
                    else:
                        raise e

        elif is_niconico:
            source = await NicoNicoDLSource.from_url(url)
            target_sources.append(source)

        elif is_spotify:
            # プレイリストの場合はsongsの結果が複数返ってくる
            # その場合は2曲目以降も存在する
            songs = spotdl.search([url])
            urls = spotdl.get_download_urls(songs)

            # それぞれURLを変換してtarget_sourcesに入れる
            for url in urls:
                target_sources.append(await YTDLSource.from_url(url, loop=self.bot.loop, stream=True))

        else:
            data = await self.bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

            # もしプレイリストだった場合
            if "entries" in data:
                for item in data["entries"]:
                    original_url = item.get("original_url")
                    target_sources.append(await YTDLSource.from_url(original_url, loop=self.bot.loop, stream=True))
            else:
                original_url = data.get("original_url")
                source = await YTDLSource.from_url(original_url, loop=self.bot.loop, stream=True)
                target_sources.append(source)

        await self.queue_sources(ctx, target_sources, play_msg)

    @commands.command(aliases=["q"])
    async def queue(self, ctx):

        embed = discord.Embed(colour=0xff00ff, title="キュー")

        if not ctx.guild.voice_client.is_playing():
            embed.description = "再生していません"

        else:
            queue_embed = [f"__現在再生中__:\n[{self.player.title}]({self.player.original_url})"]

            for i in range(min(len(self.queue[ctx.guild.id]), 10)):
                queue_embed.append(("__次に再生__:\n" if i == 0 else "") + f"`{i + 1}.` [{self.queue[ctx.guild.id][i].title}]({self.queue[ctx.guild.id][i].original_url})")

            embed.description = "\n\n".join(queue_embed)

        embed.set_footer(text=f"残りキュー: {len(self.queue[ctx.guild.id])}")
        # embed.set_footer(text=f"残りキュー: {len(self.queue[ctx.guild.id])} | ループ: {"有効" if self.loop else "無効"}")
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

        random.shuffle(self.queue[ctx.guild.id])
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

        self.queue[ctx.guild.id].clear()
        ctx.guild.voice_client.stop()
        embed = discord.Embed(colour=0xff00ff, title="再生を停止します")
        await ctx.channel.send(embed=embed)
