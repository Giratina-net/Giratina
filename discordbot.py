# -*- coding: utf-8 -*-
import asyncio
import datetime
import glob
import os
import random
import typing
from os import getenv

import discord
import requests
import tweepy
import yt_dlp
from PIL import Image, ImageFont, ImageDraw
from discord.ext import commands
from googleapiclient.discovery import build
from niconico import NicoNico

# DiscordBot
DISCORD_BOT_TOKEN = getenv("DISCORD_BOT_TOKEN")
# Botの接頭辞を ! にする
bot = commands.Bot(command_prefix="!")

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

FFMPEG_OPTIONS = {
    "options": "-vn"
}

# https://qiita.com/sizumita/items/cafd00fe3e114d834ce3
# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda: ""

ytdl = yt_dlp.YoutubeDL(YTDL_FORMAT_OPTIONS)

# 定数 - 基本的に大文字
# 聖バリ鯖のサーバーID
SEIBARI_GUILD_ID = 889049222152871986
# 検索欄のチャンネルID
TWITTER_SEARCH_CHANNEL_ID = 974430034691498034
# ギラティナのチャンネルID
GIRATINA_CHANNEL_ID = 940610524415144036
# mp3tomp4のチャンネルID
WIP_CHANNEL_ID = 940966825087361025
# ファル子☆おもしろ画像集のチャンネルID
FALCON_CHANNEL_ID = 955809774849646603
# あるくおすしのユーザーID
WALKINGSUSHIBOX_USER_ID = 575588255647399958
# 野獣先輩のユーザーID
TADOKOROKOUJI_USER_ID = 1145141919810364364

client = discord.Client()


# NicoNicoDLSourceのためにちゃんと閉じる必要があるので、Sourceのあと voice_client.play の最後にこれを実行してやってください
def after_play_niconico(source, e, guild, f):
    if type(source) == NicoNicoDLSource:
        source.close_connection()

    if e:
        print(f"has error: {e}")
    else:
        f(guild)


# Cog とは: コマンドとかの機能をひとまとめにできる
class Music(commands.Cog):
    def __init__(self, bot_arg):
        self.bot = bot_arg
        self.player: typing.Union[YTDLSource, NicoNicoDLSource, None] = None
        self.queue: typing.List[typing.Union[YTDLSource, NicoNicoDLSource]] = []

    def after_play(self, guild):
        if len(self.queue) <= 0:
            return

        self.player = self.queue.pop(0)
        guild.voice_client.play(self.player, after=lambda e: after_play_niconico(self.player, e, guild, self.after_play))

    @commands.command()
    async def join(self, ctx):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            await ctx.channel.send("操作する前にボイスチャンネルに接続してください。")
            return

        # ボイスチャンネルに接続する
        await ctx.author.voice.channel.connect()
        await ctx.channel.send("接続しました。")

    @commands.command()
    async def leave(self, ctx):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            await ctx.channel.send("操作する前にボイスチャンネルに接続してください。")
            return

        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            await ctx.channel.send("Botがボイスチャンネルに接続していません。")
            return

        # 切断する
        await ctx.guild.voice_client.disconnect()
        await ctx.channel.send("切断しました。")

    @commands.command(aliases=["np"])
    async def nowplaying(self, ctx):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            await ctx.channel.send("操作する前にボイスチャンネルに接続してください。")
            return

        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            await ctx.channel.send("Botがボイスチャンネルに接続していません。")
            return

        # 再生中ではない場合は実行しない
        if not ctx.guild.voice_client.is_playing():
            await ctx.channel.send("再生していません。")
            return

        embed = discord.Embed(colour=0xff00ff, title=self.player.title, url=self.player.original_url)
        embed.set_author(name="現在再生中")

        # YouTube再生時にサムネイルも一緒に表示できるであろう構文
        # if "youtube.com" in self.player.original_url or "youtu.be" in self.player.original_url:
        #     np_youtube_video = youtube.videos().list(part="snippet", id=id).execute()
        #     np_thumbnail = np_youtube_video["items"][0]["snippet"]["thumbnails"]
        #     np_highres_thumbnail = list(np_thumbnail.keys())[-1]
        # 
        #     embed.set_image(url=np_thumbnail[np_highres_thumbnail]["url"])

        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, url):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            await ctx.channel.send("操作する前にボイスチャンネルに接続してください。")
            return

        # ボイスチャンネルにBotが未接続の場合はボイスチャンネルに接続する
        if ctx.guild.voice_client is None:
            await ctx.author.voice.channel.connect()

        embed = discord.Embed(colour=0xff00ff)
        embed.set_author(name="処理中です...")
        play_msg: discord.Message = await ctx.channel.send(embed=embed)

        # niconico.py は短縮URLも取り扱えるっぽいので信じてみる
        # https://github.com/tasuren/niconico.py/blob/b4d9fcb1d0b80e83f2d8635dd85987d1fa2d84fc/niconico/video.py#L367
        is_niconico = url.startswith("https://www.nicovideo.jp/") or url.startswith("https://nico.ms/")
        if is_niconico:
            source = await NicoNicoDLSource.from_url(url)
        else:
            source = await YTDLSource.from_url(url, loop=client.loop, stream=True)

        if ctx.guild.voice_client.is_playing():  # 他の曲を再生中の場合
            # self.playerに追加すると再生中の曲と衝突する
            self.queue.append(source)
            embed = discord.Embed(colour=0xff00ff, title=source.title, url=source.original_url)
            embed.set_author(name="キューに追加しました")
            await play_msg.edit(embed=embed)

        else:  # 他の曲を再生していない場合
            # self.playerにURLを追加し再生する
            self.player = source
            ctx.guild.voice_client.play(self.player, after=lambda e: after_play_niconico(self.player, e, ctx.guild, self.after_play))
            embed = discord.Embed(colour=0xff00ff, title=self.player.title, url=self.player.original_url)
            embed.set_author(name="再生を開始します")
            await play_msg.edit(embed=embed)

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            await ctx.channel.send("操作する前にボイスチャンネルに接続してください。")
            return

        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            await ctx.channel.send("Botがボイスチャンネルに接続していません。")
            return

        # 再生中ではない場合は実行しない
        if not ctx.guild.voice_client.is_playing():
            embed = discord.Embed(colour=0xff00ff, title="現在のキュー", description="再生されていません")
            await ctx.channel.send(embed=embed)
            return

        queue_embed = [f"__現在再生中__:\n[{self.player.title}]({self.player.original_url})"]

        if len(self.queue) > 0:
            for i in range(min(len(self.queue), 10)):
                if i == 0:
                    queue_embed.append(f"__次に再生__:\n`{i + 1}.` [{self.queue[i].title}]({self.queue[i].original_url})")
                else:
                    queue_embed.append(f"`{i + 1}.` [{self.queue[i].title}]({self.queue[i].original_url})")

        queue_embed.append(f"**残りのキュー: {len(self.queue) + 1} 個**")

        embed = discord.Embed(colour=0xff00ff, title="現在のキュー", description="\n\n".join(queue_embed))
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["s"])
    async def skip(self, ctx):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            await ctx.channel.send("操作する前にボイスチャンネルに接続してください。")
            return

        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            await ctx.channel.send("Botがボイスチャンネルに接続していません。")
            return

        # 再生中ではない場合は実行しない
        if not ctx.guild.voice_client.is_playing():
            await ctx.channel.send("再生していません。")
            return

        ctx.guild.voice_client.stop()
        await ctx.channel.send("次の曲を再生します。")

    @commands.command()
    async def shuffle(self, ctx):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            await ctx.channel.send("操作する前にボイスチャンネルに接続してください。")
            return

        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            await ctx.channel.send("Botがボイスチャンネルに接続していません。")
            return

        # 再生中ではない場合は実行しない
        if not ctx.guild.voice_client.is_playing():
            await ctx.channel.send("再生していません。")
            return

        random.shuffle(self.queue)
        await ctx.channel.send("キューをシャッフルしました。")

    @commands.command()
    async def stop(self, ctx):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            await ctx.channel.send("操作する前にボイスチャンネルに接続してください。")
            return

        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            await ctx.channel.send("Botがボイスチャンネルに接続していません。")
            return

        # 再生中ではない場合は実行しない
        if not ctx.guild.voice_client.is_playing():
            await ctx.channel.send("再生していません。")
            return

        self.queue.clear()
        ctx.guild.voice_client.stop()
        await ctx.channel.send("再生を停止し、キューをリセットしました。")


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


# もしniconicoDLをいれるなら参考になるかも
# https://github.com/akomekagome/SmileMusic/blob/dd94c342fed5301c790ce64360ad33f7c0d46208/python/smile_music.py
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

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)

        source = discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS)
        return cls(source, data=data)


# Bot起動時に実行される関数
@bot.event
async def on_ready():
    now_time = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    await bot.change_presence(activity=discord.Game(name=now_time.strftime("%Y/%m/%d %H:%M:%S")))

    channel = bot.get_channel(GIRATINA_CHANNEL_ID)
    await channel.send("ギラティナ、オォン！")


# メッセージ送信時に実行される関数
@bot.event
async def on_message(ctx):
    # 送信者がBotである場合は弾く
    # ここで弾けば以降は書かなくて良さそう
    if ctx.author.bot:
        return

    # メッセージの本文が big brother だった場合
    if "big brother" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942107244349247488/9BD8903B-74D1-4740-8EC8-13110C0D943C.jpg")

    # メッセージの本文が DJ だった場合
    if "DJ" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942107858496000010/a834912b8c8f9739.jpg")

    # メッセージの本文が somunia だった場合
    if "somunia" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://twitter.com/aaruaika/status/1518874935024054272")

    # メッセージの本文が いい曲 だった場合
    if "いい曲" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942071776815480832/unknown.png")

    # メッセージの本文が おはよう だった場合
    if "おはよう" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942108884275982426/FJxaIJIaMAAlFYc.png")

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

    # メッセージの本文が ゆるゆり だった場合
    if "ゆるゆり" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("ラブライブです")

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

    # メッセージの本文が 死んだ だった場合
    if "死んだ" in str(ctx.content) or "しんだ" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/941239897400950794/newdance-min.gif")

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
                await attachment.save("resources/temporally/wip_input.mp3")
                command = "ffmpeg -y -loop 1 -i resources/wip_input.jpg -i resources/temporally/wip_input.mp3 -vcodec libx264 -vb 50k -acodec aac -strict experimental -ab 128k -ac 2 -ar 48000 -pix_fmt yuv420p -shortest resources/temporally/wip_output.mp4"
                proc = await asyncio.create_subprocess_exec(*command.split(" "), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                stdout, stderr = await proc.communicate()
                await ctx.channel.send(file=discord.File("resources/temporally/wip_output.mp4"))
                os.remove("resources/temporally/wip_input.mp3")
                os.remove("resources/temporally/wip_output.mp4")

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
    # m = MeCab.Tagger ("-Ochasen")
    # print(m.parse (ctx.content))
    # check = [5, 7, 5] # 5, 7, 5
    # check_index = 0
    # word_cnt = 0
    # node = m.parseToNode(word)
    # # suggestion文の各要素の品詞を確認
    # while node:
    #     feature = node.feature.split(",")[0]
    #     surface = node.surface.split(",")[0]
    #     # 記号, BOS/EOSはスルー
    #     if feature == "記号" or feature == "BOS/EOS":
    #         node = node.next
    #         continue
    #     # 文字数をカウント
    #     word_cnt += len(surface)
    #
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
    #         await ctx.channel.send("575を見つけました!")
    #     node = node.next
    # return False
    #
    # print(sys.argv[1], len(sys.argv))
    # print(judge_five_seven_five(sys.argv[1]))

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
    await ctx.send(f"{annict_works_title}({annict_works_season_name_text}-{annict_works_episodes_count}話)\nhttps://annict.com/works/{random_id}")


# bokuseku.mp3 流し逃げ - https://qiita.com/sizumita/items/cafd00fe3e114d834ce3
@bot.command()
async def bokuseku(ctx):
    if ctx.author.voice is None:
        await ctx.channel.send("望月くん・・・ボイスチャンネルに来なさい")
        return

    # ボイスチャンネルに接続する
    await ctx.author.voice.channel.connect()
    # 音声を再生する
    ctx.guild.voice_client.play(discord.FFmpegPCMAudio("resources/bokuseku.mp3"), after=lambda e: ctx.guild.voice_client.disconnect())
    # 切断する
    await ctx.guild.voice_client.disconnect()


# チーバくんの、なのはな体操
@bot.command()
async def chiibakun(ctx):
    await ctx.send("https://www.youtube.com/watch?v=dC0eie-WQss")


# ファルコおもしろ画像を送信
@bot.command(aliases=["syai", "faruko"])
async def falco(ctx):
    guild = bot.get_guild(SEIBARI_GUILD_ID)

    channel = guild.get_channel(FALCON_CHANNEL_ID)

    falco_channel_messages = [message async for message in channel.history(limit=None)]
    # falco_channel_messages = await channel.messages.fetch({ limit: 100 })

    random_falco = random.choice(falco_channel_messages)

    # print(random_falco)
    content = random_falco.content
    if content == "":
        content = random_falco.attachments[0].url

    # メッセージが送られてきたチャンネルに送る
    await ctx.channel.send(content)


# Twitterから#GenshinImpactの1000いいね以上を探して送信
@bot.command(aliases=["gennshinn", "gensin", "gennsinn", "gs"])
async def genshin(ctx):
    tweets = twapi.search_tweets(q=f"filter:images min_faves:1000 #GenshinImpact", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.extended_entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.send(origin)


# ギラティナの画像を送る
@bot.command()
async def giratina(ctx):
    await ctx.send("https://img.gamewith.jp/article/thumbnail/rectangle/36417.png")


# Twitterから#胡桃の1000いいね以上を探して送信
@bot.command(aliases=["kisshutao"])
async def hutao(ctx):
    tweets = twapi.search_tweets(q=f"filter:images min_faves:1000 #胡桃", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.extended_entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.send(origin)


# イキス
@bot.command()
async def inm(ctx):
    await ctx.send(
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
            await ctx.send(origin)


# こまちゃんを送信
@bot.command()
async def komachan(ctx):
    tweets = twapi.search_tweets(q="from:@komachan_pic", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.send(origin)


# らきすたを送信
# https://ja.stackoverflow.com/questions/56894/twitter-api-%e3%81%a7-%e5%8b%95%e7%94%bb%e3%83%84%e3%82%a4%e3%83%bc%e3%83%88-%e3%82%921%e4%bb%b6%e5%8f%96%e5%be%97%e3%81%97%e3%81%a6html%e4%b8%8a%e3%81%a7%e8%a1%a8%e7%a4%ba%e3%81%95%e3%81%9b%e3%81%9f%e3%81%84%e3%81%ae%e3%81%a7%e3%81%99%e3%81%8c-m3u8-%e5%bd%a2%e5%bc%8f%e3%81%a8-mp4-%e5%bd%a2%e5%bc%8f%e3%81%ae%e9%96%a2%e4%bf%82%e6%80%a7%e3%81%af
# https://syncer.jp/Web/API/Twitter/REST_API/Object/Entity/#:~:text=Filter-,%E3%83%84%E3%82%A4%E3%83%BC%E3%83%88%E3%82%AA%E3%83%96%E3%82%B8%E3%82%A7%E3%82%AF%E3%83%88%20(%E5%8B%95%E7%94%BB),-%E5%8B%95%E7%94%BB%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB%E3%82%92
@bot.command()
async def lucky(ctx):
    tweets = twapi.search_tweets(q="from:@LuckyStarPicBot", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.extended_entities["media"]
        for m in media:
            if m["type"] == "video":
                for video_info in m:
                    for variants in video_info:
                        for url in variants[0]:
                            origin = url
                            await ctx.send(origin)
            else:
                origin = m["media_url"]
                await ctx.send(origin)


@bot.command()
async def ma(ctx):
    await ctx.send("https://cdn.discordapp.com/attachments/964831309627289620/982691239025598494/long_ver.___feat._0s_screenshot.png")


# アニクトから取得したキャラクターをランダムで表示
@bot.command()
async def odai(ctx):
    while 1:
        # リスト
        random_ids = []
        # 10個のランダムな数を生成
        for i in range(10):
            random_id = random.randint(1, 41767)
            random_ids.append(str(random_id))
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
        target_character = None
        # 配列の中を先頭から順に舐めていく
        for annict_character in annict_characters:
            # お気に入り数が5以上あるときループを解除する
            if annict_character["favorite_characters_count"] > 4:
                target_character = annict_character
                break
        if target_character is not None:
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

    await ctx.send(annict_character_msg)


# ピンポン
@bot.command()
async def ping(ctx):
    latency = bot.latency
    latency_milli = round(latency * 1000)
    await ctx.send(f"Pong!: {latency_milli}ms")


# Raika
@bot.command()
async def raika(ctx):
    await ctx.send("Twitterをやってるときの指の動作またはスマートフォンを凝視するという行動が同じだけなのであって容姿がこのような姿であるという意味ではありません")


# サターニャを送信
@bot.command()
async def satanya(ctx):
    tweets = twapi.search_tweets(q="from:@satanya_gazobot", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.send(origin)


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
            await ctx.send(origin)


# ウマ娘ガチャシミュレーター
@bot.command()
async def uma(ctx):
    uma_list = [
        # [ウマ娘の名称, レア度(ピックアップは+10)]
        # ガチャ詳細サイト
        # https://umamusume.cygames.jp/#/gacha
        ["[スペシャルドリーマー]スペシャルウィーク", 3],
        ["[サイレントイノセンス]サイレンススズカ", 3],
        ["[トップ・オブ・ジョイフル]トウカイテイオー", 3],
        ["[フォーミュラオブルージュ]マルゼンスキー", 3],
        ["[スターライトビート]オグリキャップ", 3],
        ["[ワイルド・フロンティア]タイキシャトル", 3],
        ["[エレガンス・ライン]メジロマックイーン", 3],
        ["[ロード・オブ・エンペラー]シンボリルドルフ", 3],
        ["[ローゼスドリーム]ライスシャワー", 3],
        ["[レッドストライフ]ゴールドシップ", 2],
        ["[ワイルドトップギア]ウオッカ", 2],
        ["[トップ・オブ・ブルー]ダイワスカーレット", 2],
        ["[石穿つ者]グラスワンダー", 2],
        ["[エル☆Número１]エルコンドルパサー", 2],
        ["[エンプレスロード]エアグルーヴ", 2],
        ["[すくらんぶる☆ゾーン]マヤノトップガン", 2],
        ["[マーマリングストリーム]スーパークリーク", 2],
        ["[ストレート・ライン]メジロライアン", 1],
        ["[tach-nology]アグネスタキオン", 1],
        ["[Go To Winning]ウイニングチケット", 1],
        ["[サクラ、すすめ！]サクラバクシンオー", 1],
        ["[うららん一等賞♪]ハルウララ", 1],
        ["[運気上昇☆幸福万来]マチカネフクキタル", 1],
        ["[ポインセチア・リボン]ナイスネイチャ", 1],
        ["[キング・オブ・エメラルド]キングヘイロー", 1],
        ["[オー・ソレ・スーオ！]テイエムオペラオー", 3],
        ["[MB-19890425]ミホノブルボン", 3],
        ["[pf.Victory formula...]ビワハヤヒデ", 3],
        ["[ビヨンド・ザ・ホライズン]トウカイテイオー", 3],
        ["[エンド・オブ・スカイ]メジロマックイーン", 3],
        ["[フィーユ・エクレール]カレンチャン", 3],
        ["[Nevertheless]ナリタタイシン", 3],
        ["[あぶそりゅーと☆LOVE]スマートファルコン", 3],
        ["[Maverick]ナリタブライアン", 3],
        ["[サンライト・ブーケ]マヤノトップガン", 3],
        ["[クエルクス・キウィーリス]エアグルーヴ", 3],
        ["[あおぐもサミング]セイウンスカイ", 3],
        ["[アマゾネス・ラピス]ヒシアマゾン", 3],
        ["[ククルカン・モンク]エルコンドルパサー", 3],
        ["[セイントジェード・ヒーラー]グラスワンダー", 3],
        ["[シューティングスタァ・ルヴュ]フジキセキ", 3],
        ["[オーセンティック/1928]ゴールドシチー", 3],
        ["[ほっぴん♪ビタミンハート]スペシャルウィーク", 3],
        ["[ぶっとび☆さまーナイト]マルゼンスキー", 3],
        ["[ブルー/レイジング]メイショウドトウ", 3],
        ["[Meisterscaft]エイシンフラッシュ", 3],
        ["[吉兆・初あらし]マチカネフクキタル", 3],
        ["[ボーノ☆アラモーダ]ヒシアケボノ", 3],
        ["[超特急！フルカラー特殊PP]アグネスデジタル", 3],
        ["[Make up Vampire!]ライスシャワー", 3],
        ["[シフォンリボンマミー]スーパークリーク", 3],
        ["[プリンセス・オブ・ピンク]カワカミプリンセス", 3],
        ["[Creeping Black]マンハッタンカフェ", 3],
        ["[皓月の弓取り]シンボリルドルフ", 3],
        ["[秋桜ダンツァトリーチェ]ゴールドシチー", 3],
        ["[ポップス☆ジョーカー]トーセンジョーダン", 3],
        ["[ツイステッド・ライン]メジロドーベル", 3],
        ["[キセキの白星]オグリキャップ", 3],
        ["[ノエルージュ・キャロル]ビワハヤヒデ", 3],
        ["[Noble Seamair]ファインモーション", 3],
        ["[疾風迅雷]タマモクロス", 3],
        ["[初うらら♪さくさくら]ハルウララ", 3],
        ["[初晴・青き絢爛]テイエムオペラオー", 3],
        ["[日下開山・花あかり]サクラチヨノオー", 3],
        ["[CODE：グラサージュ]ミホノブルボン", 3],
        ["[コレクト・ショコラティエ]エイシンフラッシュ", 3],
        ["[クリノクロア・ライン]メジロアルダン", 3],
        ["[Starry Nocturne]アドマイヤベガ", 3],
        ["[錦上・大判御輿]キタサンブラック", 3],
        ["[ぱんぱかティルトット]マチカネタンホイザ", 2],
        ["[Natural Brilliance]サトノダイヤモンド", 3],
        ["[ブリュニサージュ・ライン]メジロブライト", 3],
        ["[ソワレ・ド・シャトン]セイウンスカイ", 3],
        ["[シュクセ・エトワーレ]フジキセキ", 3],
        ["[ティアード・ペタル]ニシノフラワー", 3],
        ["[四白流星の襲]ヤエノムテキ", 3],
        ["[RUN&WIN]ナイスネイチャ", 3],
        ["[白く気高き激励の装]キングヘイロー", 3],
        ["[オールタイム・フィーバー]アイネスフウジン", 3],
        ["[Like Breakthrough]メジロパーマー", 3],
        ["[朔月のマ・シェリ]カレンチャン", 3],
        ["[Titania]ファインモーション", 3],
        ["[稲荷所縁江戸紫]イナリワン", 13]
    ]

    # 確率比[★1, ★2, ★3, ピックアップ]
    weights = [79, 18, 2.25, 0.75]
    # 確率比(10回目)
    weights_10 = [0, 97, 2.25, 0.75]

    # 画像サイズ
    width = 400
    height = 222
    # 項目の間隔
    margin = 46
    # 画像の背景色
    bg = (54, 57, 63)
    # 画像の初期化
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(".fonts/meiryo.ttf", 16)

    for i in range(10):
        if i < 9:
            w = weights
        else:
            w = weights_10
        # レア度ごとに選出
        uma_results_by_rarity = [
            random.choice([i for i in uma_list if i[1] == 1]),
            random.choice([i for i in uma_list if i[1] == 2]),
            random.choice([i for i in uma_list if i[1] == 3]),
            random.choice([i for i in uma_list if i[1] > 10])
        ]
        # 最終的な排出ウマ娘を決定
        uma_result = random.choices(uma_results_by_rarity, weights=w)[0]
        # レア度が3なら文字色を変える
        if uma_result[1] % 10 == 3:
            color = (214, 204, 107)
        else:
            color = (255, 255, 255)
        # 原寸で表示される最大の画像サイズが400x300(10連だと見切れる)なので5連ずつ2枚の画像に分ける
        if i == 5:
            draw.rectangle((0, 0, width, height), fill=bg)
        # アイコン画像をuma_iconフォルダから読み込み&貼り付け(URLから読み込むと遅かった)
        uma_image = Image.open(f"resources/uma_icon/i_{uma_list.index(uma_result) + 1}.png")
        img.paste(uma_image, (0, margin * (i % 5)))
        # テキストを描画(星マーク)
        draw.text((40, -4 + margin * (i % 5)), "★" * (uma_result[1] % 10) + "　" * (3 - uma_result[1] % 10), color, font=font)
        # テキストを描画(ウマ娘名称)
        draw.text((40, 12 + margin * (i % 5)), uma_result[0], color, font=font)

        # 5連ごとに画像を書き出し
        if i % 5 == 4:
            img.save(f"resources/temporally/uma_gacha_{ctx.channel.id}_{int(i / 5) + 1}.png")

    uma_gacha_images = []
    get_uma_gacha_images = glob.glob(f"resources/temporally/uma_gacha_{ctx.channel.id}_*.png")

    for file in get_uma_gacha_images:
        uma_gacha_images.append(discord.File(file))

    await ctx.send(files=uma_gacha_images)

    for file in get_uma_gacha_images:
        if os.path.isfile(file):
            os.remove(file)


# ゆるゆりを送信
@bot.command()
async def yuruyuri(ctx):
    tweets = twapi.search_tweets(q="from:@YuruYuriBot1", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.send(origin)


bot.add_cog(Music(bot_arg=bot))
bot.run(DISCORD_BOT_TOKEN)
