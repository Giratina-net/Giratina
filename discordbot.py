import asyncio
import random
from asyncio import sleep
from os import getenv

import discord
import yt_dlp
from niconico import NicoNico as niconico_dl
from discord.ext import commands

from googleapiclient.discovery import build

# https://qiita.com/sizumita/items/cafd00fe3e114d834ce3
# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda: ""

ytdl_format_options = {
    "format": "bestaudio/best*[acodec=opus]",
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

class NicoNicoDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, url, volume=0.1):
        super().__init__(source, volume)

        self.url = url

    @classmethod
    async def from_url(cls, url, *, log=False, volume=0.1):
        nico_id = url.split("/")[-1]
        niconico = niconico_dl(nico_id)
        stream_url = await niconico.get_download_link()

        source = OriginalFFmpegPCMAudio(stream_url, **ffmpeg_options)
        return (cls(source, url=stream_url, volume=volume), niconico)

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
    async def play(self, ctx, url):
        if ctx.author.voice is None:
            await ctx.channel.send("接続していません。")
            return
            # ボイスチャンネルに接続する
        if ctx.guild.voice_client is None:
            await ctx.author.voice.channel.connect()

        # youtubeから音楽をダウンロードする
        is_niconico = url.startswith("https://www.nicovideo.jp/")
        if is_niconico:
            player, niconico = await NicoNicoDLSource.from_url(url, log=True)
        else:
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

    # メッセージの本文が 精液 だった場合
    if "精液" in str(ctx.content):
        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send("https://cdn.discordapp.com/attachments/395580207970648064/944945500874997841/unknown.png")

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

## ファルコおもしろ画像を送信
#@bot.command(aliases=["syai","faruko"])
#async def falco(ctx):
    ## 送信者がBotである場合は弾く
    #if ctx.author.bot:
    #    return
    
    #falco_cahnnel_message = await channel.messages.fetch({ limit: 100 })

    #random_falco = random.choice(falco_cahnnel_message)

    ## メッセージが送られてきたチャンネルに送る
    #await ctx.channel.send(random_falco)

# Raika
@bot.command()
async def raika(ctx):
    await ctx.send("Twitterをやってるときの指の動作またはスマートフォンを凝視するという行動が同じだけなのであって容姿がこのような姿であるという意味ではありません")

# チーバくんの、なのはな体操
@bot.command()
async def chiibakun(ctx):
    await ctx.send("https://www.youtube.com/watch?v=dC0eie-WQss")


# かおすちゃんを送信
@bot.command()
async def kaosu(ctx):
    await ctx.send("https://pbs.twimg.com/media/E512yaSVIAQxfNn?format=jpg&name=large")


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
