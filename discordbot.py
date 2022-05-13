import asyncio
import random
from asyncio import sleep
from os import getenv
import sys
import MeCab

import discord
import yt_dlp
from discord.ext import commands

from googleapiclient.discovery import build
import tweepy

consumer_key = getenv("CONSUMER_KEY")
consumer_secret = getenv("CONSUMER_SECRET")
access_token = getenv("ACCESS_TOKEN_KEY")
access_token_secret = getenv("ACCESS_TOKEN_SECRET")
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)    

# https://qiita.com/sizumita/items/cafd00fe3e114d834ce3
# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda: ""

ytdl_format_options = {
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

ffmpeg_options = {
    "options": "-vn"
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

token = getenv("DISCORD_BOT_TOKEN")

developerKey = getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=developerKey)

# botの接頭辞を!にする
bot = commands.Bot(command_prefix="!")

# 聖バリ鯖のサーバーID
SEIBARI_GUILD_ID = 889049222152871986
# 検索欄のチャンネルID
TWITTER_SEARCH_CHANNEL = 974430034691498034
# ギラティナのチャンネルのID
GIRATINA_CHANNEL_ID = 940610524415144036
# mp3tomp4のチャンネルのID
WIP_CHANNEL_ID = 940966825087361025
# ファル子☆おもしろ画像集のID
FALCON_CAHNNEL_ID = 955809774849646603
# あるくおすしのユーザーID
walkingsushibox = 575588255647399958


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")
        self.original_url = data.get("original_url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# もしniconicoDLをいれるなら参考になるかも
# https://github.com/akomekagome/SmileMusic/blob/dd94c342fed5301c790ce64360ad33f7c0d46208/python/smile_music.py

client = discord.Client()

# Cog とは? コマンドとかの機能をひとまとめにできる
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.player = None
        self.queue = []

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.channel.send("あなたはボイスチャンネルに接続していません。")
            return
        # ボイスチャンネルに接続する
        await ctx.author.voice.channel.connect()
        await ctx.channel.send("接続しました。")


    @commands.command()
    async def leave(self, ctx):
        if ctx.guild.voice_client is None:
            await ctx.channel.send("接続していません。")
            return
        # 切断する
        await ctx.guild.voice_client.disconnect()
        await ctx.channel.send("切断しました。")


    @commands.command(aliases=["p"])
    async def play(self, ctx, *, url):
        if ctx.author.voice is None:
            await ctx.channel.send("接続していません。")
            return
            # ボイスチャンネルに接続する
        if ctx.guild.voice_client is None:
            await ctx.author.voice.channel.connect()

        self.player = await YTDLSource.from_url(url, loop=client.loop)

        if ctx.guild.voice_client.is_playing():
            self.queue.append(self.player)
            await ctx.channel.send(f"{self.player.title} をキューに追加しました。")
            return

        else :
            # 再生する
            ctx.guild.voice_client.play(self.player, after=lambda e: print(f"has error: {e}") if e else self.after_played(ctx.guild))
            await ctx.channel.send(f"{self.player.title} を再生します。")

    def after_played(self, guild):
        if len(self.queue) <= 0:
            return

        self.player = self.queue.pop(0)
        guild.voice_client.play(self.player, after=lambda e: print(f"has error: {e}") if e else self.after_played(guild))

    @commands.command(aliases=["q"])
    async def queue(self,ctx):
        # 再生中ではない場合は実行しない
        if not ctx.guild.voice_client.is_playing():
            await ctx.send("再生していません。")
            return

    @commands.command(aliases=["np"])
    async def nowplaying(self, ctx):
        
        # 再生中ではない場合は実行しない
        if not ctx.guild.voice_client.is_playing():
            await ctx.send("再生していません。")
            return

        embed = discord.Embed(title=self.player.original_url,description=f"{self.player.title} を再生中です。")
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def skip(self, ctx):
        if ctx.guild.voice_client is None:
            await ctx.send("接続していません。")
            return

        # 再生中ではない場合は実行しない
        if not ctx.guild.voice_client.is_playing():
            await ctx.send("再生していません。")
            return

        ctx.guild.voice_client.stop()
        await ctx.send("次の曲を再生します。")

    @commands.command()
    async def stop(self, ctx):
        if ctx.guild.voice_client is None:
            await ctx.send("接続していません。")
            return

        # 再生中ではない場合は実行しない
        if not ctx.guild.voice_client.is_playing():
            await ctx.send("再生していません。")
            return

        self.queue.clear()
        ctx.guild.voice_client.stop()
        await ctx.send("停止しました。")        



# 起動時のメッセージの関数
async def ready_greet():
    channel = bot.get_channel(GIRATINA_CHANNEL_ID)
    await channel.send("ギラティナ、オォン！")


# Bot起動時に実行される関数
@bot.event
async def on_ready():
    await ready_greet()


# ピンポン
@bot.command()
async def ping(ctx):
    await ctx.send("pong")


@bot.event
async def on_message(ctx):
    # 送信者がBotである場合は弾く
    if ctx.author.bot:
        return

    # ドナルドの言葉狩り - https://qiita.com/sizumita/items/9d44ae7d1ce007391699
    # メッセージの本文が ドナルド だった場合
    if "ドナルド" in str(ctx.content):
        # 送信するメッセージをランダムで決める
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://tenor.com/view/ronald-mcdonald-insanity-ronald-mcdonald-gif-21974293")

    # メッセージの本文が 死んだ だった場合
    if "死んだ" in str(ctx.content) or "しんだ" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/941239897400950794/newdance-min.gif")

    # メッセージの本文が ゆるゆり だった場合
    if "ゆるゆり" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("ラブライブです")

    # メッセージの本文が 一週間 だった場合
    if "一週間" in str(ctx.content) or "1週間" in str(ctx.content):
        # サムネイルをAPIで取得する構文
        yamadahouse_videoId = []
        response = youtube.search().list(channelId="UCmEG6Kw9z2PJM2yjQ1VQouw", part="snippet", maxResults=50).execute()
        for item in response.get("items", []):
            yamadahouse_videoId.append(item["snippet"]["thumbnails"]["high"]["url"])

        random_yamadahouse = random.choice(yamadahouse_videoId)

        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send(random_yamadahouse)

    # メッセージの本文が バキ だった場合
    if "バキ" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/934792442178306108/942106647927595008/unknown.png")

    # メッセージの本文が big brother だった場合
    if "big brother" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942107244349247488/9BD8903B-74D1-4740-8EC8-13110C0D943C.jpg")

    # メッセージの本文が DJ だった場合
    if "DJ" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942107858496000010/a834912b8c8f9739.jpg")

    # メッセージの本文が メタ だった場合
    if "メタ" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942109742782889994/GWHiBiKi_StYle_9_-_YouTube_1.png")

    # メッセージの本文が 風呂 だった場合
    if "風呂" in str(ctx.content) or "ふろ" in str(ctx.content):
        # あるくおすしの場合
        if ctx.author.id == walkingsushibox:
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942389072117256192/19ffe7f2e7464263.png")
        # あるくおすし以外の場合
        # 俺か俺以外か（by あるくおすし）   
        else:
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/943155933343785040/d9ce03af4958b0b7.png")

    # メッセージの本文が ランキング だった場合
    if "ランキング" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942109619243864085/E8sV781VIAEtwZq.png")

    # メッセージの本文が おはよう だった場合
    if "おはよう" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942108884275982426/FJxaIJIaMAAlFYc.png")

    # メッセージの本文が いい曲 だった場合
    if "いい曲" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942071776815480832/unknown.png")

    # メッセージの本文が やんぱ だった場合
    if "やんぱ" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("やんぱ2")

    if ctx.attachments and ctx.channel.id == WIP_CHANNEL_ID:
        for attachment in ctx.attachments:
            # Attachmentの拡張子がmp3, wavのどれかだった場合
            # https://discordpy.readthedocs.io/ja/latest/api.html#attachment
            if "audio" in attachment.content_type:
                await attachment.save("input.mp3")
                command = "ffmpeg -y -loop 1 -i input.jpg -i input.mp3 -vcodec libx264 -vb 50k -acodec aac -strict experimental -ab 128k -ac 2 -ar 48000 -pix_fmt yuv420p -shortest output.mp4"
                proc = await asyncio.create_subprocess_exec(*command.split(" "), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                stdout, stderr = await proc.communicate()
                await ctx.channel.send(file=discord.File("output.mp4"))
    await bot.process_commands(ctx)

    # n575
    # https://gist.github.com/4geru/46f300e561374833646ffd8f4b916672
    m = MeCab.Tagger ("-Ochasen")
    print(m.parse (ctx.content))
    check = [5, 7, 5] # 5, 7, 5
    check_index = 0
    word_cnt = 0
    node = m.parseToNode(word)
    # suggestion文の各要素の品詞を確認
    while node:
        feature = node.feature.split(",")[0]
        surface = node.surface.split(",")[0]
        # 記号, BOS/EOSはスルー
        if feature == '記号' or feature == 'BOS/EOS':
            node = node.next
            continue
        # 文字数をカウント
        word_cnt += len(surface)
        
        # 字数チェック
        if word_cnt == check[check_index]:
            check_index += 1
            word_cnt = 0
            continue
        # 字余りチェック
        elif word_cnt > check[check_index]:
            return False
            
        # [5, 7, 5] の長さになっているか
        if check_index == len(check) - 1:
            return True
            await ctx.channel.send("575を見つけました!")
        node = node.next
        
    return False
        
#    print(sys.argv[1], len(sys.argv))
#    print(judge_five_seven_five(sys.argv[1]))


    # 検索欄チャンネルに投稿されたメッセージから、TwitterAPIを通してそのメッセージを検索して、チャンネルに画像を送信する    
#    if ctx.content and ctx.channel.id == TWITTER_SEARCH_CHANNEL:
#        tweets = api.search_tweets(q=f"filter:images {arg}", tweet_mode='extended', include_entities=True, count=1)
#        for tweet in tweets:
#            media = tweet.extended_entities["media"]
#            for m in media:
#                origin = m["media_url"]
#        await ctx.channel.send(origin)


# ファルコおもしろ画像を送信
@bot.command(aliases=["syai","faruko"])
async def falco(ctx):
    # 送信者がBotである場合は弾く
    if ctx.author.bot:
        return
    
    guild = bot.get_guild(SEIBARI_GUILD_ID)

    channel = guild.get_channel(FALCON_CAHNNEL_ID)

    falco_cahnnel_messages = [message async for message in channel.history(limit=None)]
    # falco_cahnnel_message = await channel.messages.fetch({ limit: 100 })

    random_falco = random.choice(falco_cahnnel_messages)

    # print(random_falco)
    content = random_falco.content
    if content == "":
        content = random_falco.attachments[0].url

    # メッセージが送られてきたチャンネルに送る
    await ctx.channel.send(content)

# Raika
@bot.command()
async def raika(ctx):
    await ctx.send("Twitterをやってるときの指の動作またはスマートフォンを凝視するという行動が同じだけなのであって容姿がこのような姿であるという意味ではありません")

# チーバくんの、なのはな体操
@bot.command()
async def chiibakun(ctx):
    await ctx.send("https://www.youtube.com/watch?v=dC0eie-WQss")

# https://zenn.dev/zakiii/articles/7ada80144c9db0
# https://qiita.com/soma_sekimoto/items/65c664f00573284b0b74

# TwitterのIDを指定して最新の画像を送信
@bot.command()
async def twitter(ctx, *, arg):
    tweets = api.search_tweets(q=f"filter:images {arg}", tweet_mode='extended', include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.extended_entities["media"]
        for m in media:
            origin = m["media_url"]
        await ctx.send(origin)

# こまちゃんを送信
@bot.command()
async def komachan(ctx):
    tweets = api.search_tweets(q="from:@komachan_pic", tweet_mode='extended', include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities['media']
        for m in media:
            origin = m['media_url']
        await ctx.send(origin)

# かおすちゃんを送信
@bot.command()
async def kaosu(ctx):
    tweets = api.search_tweets(q="from:@kaosu_pic", tweet_mode='extended', include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities['media']
        for m in media:
            origin = m['media_url']
        await ctx.send(origin)

# ゆるゆりを送信
@bot.command()
async def yuruyuri(ctx):
    tweets = api.search_tweets(q="from:@YuruYuriBot1", tweet_mode='extended', include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities['media']
        for m in media:
            origin = m['media_url']
        await ctx.send(origin)

# らきすたを送信
#https://ja.stackoverflow.com/questions/56894/twitter-api-%e3%81%a7-%e5%8b%95%e7%94%bb%e3%83%84%e3%82%a4%e3%83%bc%e3%83%88-%e3%82%921%e4%bb%b6%e5%8f%96%e5%be%97%e3%81%97%e3%81%a6html%e4%b8%8a%e3%81%a7%e8%a1%a8%e7%a4%ba%e3%81%95%e3%81%9b%e3%81%9f%e3%81%84%e3%81%ae%e3%81%a7%e3%81%99%e3%81%8c-m3u8-%e5%bd%a2%e5%bc%8f%e3%81%a8-mp4-%e5%bd%a2%e5%bc%8f%e3%81%ae%e9%96%a2%e4%bf%82%e6%80%a7%e3%81%af
@bot.command()
async def lucky(ctx):
    tweets = api.search_tweets(q="from:@LuckyStarPicBot", tweet_mode='extended', include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.extended_entities["media"]
        for m in media:
            if m["type"] =="video":
                for video_info in m:
                    for variants in video_info:
                        for url in variants[0]:
                            origin = url
            else:
                origin = m["media_url"]
        await ctx.send(origin)


# イキス
@bot.command()
async def inm(ctx):
    await ctx.send("聖バリ「イキスギィイクイク！！！ンアッー！！！マクラがデカすぎる！！！」\n\n"
                   f"{ctx.author.name}「聖なるバリア －ミラーフォース－、淫夢はもうやめてよ！淫夢ごっこは恥ずかしいよ！」\n\n"
                   f"聖バリ「{ctx.author.name}、おっ大丈夫か大丈夫か〜？？？バッチェ冷えてるぞ〜淫夢が大好きだってはっきりわかんだね」")


# ギラティナの画像を送る
@bot.command()
async def giratina(ctx):
    await ctx.send("https://img.gamewith.jp/article/thumbnail/rectangle/36417.png")


# bokuseku.mp3 流し逃げ - https://qiita.com/sizumita/items/cafd00fe3e114d834ce3
@bot.command()
async def bokuseku(ctx):
    if ctx.author.voice is None:
        await ctx.channel.send("望月くん・・・ボイスチャンネルに来なさい")
        return
    else:
        # ボイスチャンネルに接続する
        await ctx.author.voice.channel.connect()
        # 音声を再生する
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio("bokuseku.mp3"))
    # 音声が再生中か確認する
        while ctx.guild.voice_client.is_playing():
            await sleep(1)
        # 切断する
        await ctx.guild.voice_client.disconnect()



bot.add_cog(Music(bot=bot))
bot.run(token)
