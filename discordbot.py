import asyncio
import traceback
from asyncio import sleep
from os import getenv
import random

import discord
from discord.ext import commands
import youtube_dl

client = discord.Client()



yamadahouse_videoID = [
    "Xpr3vMjgPu4", #ゾンサガ
    "YV4Q_c0BuwM", #規則正しい生活
    "0ktLlgm5ChQ", #ぼっち系youtuber
    "FITOm27RaSQ", #財布にお金入れ続ける
    "XtKPLTaRYt8", #無職転生
]

randam_yamadahouse = random.choice(yamadahouse_videoID)

yamadahouse_thumbnail = 'http://img.youtube.com/vi/' + (random_yamadahouse) + '/sddefault.jpg'

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# botの接頭辞を!にする
bot = commands.Bot(command_prefix='!')

# ギラティナのチャンネルのID
GIRATINA_CHANNEL_ID = 940610524415144036
# mp3tomp4のチャンネルのID
WIP_CHANNEL_ID = 940966825087361025

# あるくおすしのユーザーID
walkingsushibox = 575588255647399958

# https://qiita.com/sizumita/items/cafd00fe3e114d834ce3
# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@client.event
async def on_message(message: discord.Message):
    # メッセージの送信者がbotだった場合は無視する
    if message.author.bot:
        return

    if message.content == "!join":
        if message.author.voice is None:
            await message.channel.send("あなたはボイスチャンネルに接続していません。")
            return
        # ボイスチャンネルに接続する
        await message.author.voice.channel.connect()
        await message.channel.send("接続しました。")

    elif message.content == "!leave":
        if message.guild.voice_client is None:
            await message.channel.send("接続していません。")
            return

        # 切断する
        await message.guild.voice_client.disconnect()

        await message.channel.send("切断しました。")
    elif message.content.startswith("!play "):
        if message.guild.voice_client is None:
            await message.channel.send("接続していません。")
            return
        # 再生中の場合は再生しない
        if message.guild.voice_client.is_playing():
            await message.channel.send("再生中です。")
            return

        url = message.content[6:]
        # youtubeから音楽をダウンロードする
        player = await YTDLSource.from_url(url, loop=client.loop)

        # 再生する
        await message.guild.voice_client.play(player)

        await message.channel.send('{} を再生します。'.format(player.title))

    elif message.content == "!stop":
        if message.guild.voice_client is None:
            await message.channel.send("接続していません。")
            return

        # 再生中ではない場合は実行しない
        if not message.guild.voice_client.is_playing():
            await message.channel.send("再生していません。")
            return

        message.guild.voice_client.stop()

        await message.channel.send("ストップしました。")



# 起動時のメッセージの関数
async def ready_greet():
    channel = bot.get_channel(GIRATINA_CHANNEL_ID)
    await channel.send('ギラティナ、オォン！')


# Bot起動時に実行される関数
@bot.event
async def on_ready():
    await ready_greet()


# ピンポン
@bot.command()
async def ping(ctx):
    await ctx.send('pong')


@bot.event
async def on_message(message):
    # 送信者がBotである場合は弾く
    if message.author.bot:
        return

    # ドナルドの言葉狩り - https://qiita.com/sizumita/items/9d44ae7d1ce007391699
    # メッセージの本文が ドナルド だった場合
    if 'ドナルド' in str(message.content):
        # 送信するメッセージをランダムで決める
        # メッセージが送られてきたチャンネルに送る
        await message.channel.send('https://tenor.com/view/ronald-mcdonald-insanity-ronald-mcdonald-gif-21974293')

    # メッセージの本文が 死んだ だった場合
    if '死んだ' in str(message.content) or 'しんだ' in str(message.content):
        # メッセージが送られてきたチャンネルに送る
        await message.channel.send('https://cdn.discordapp.com/attachments/889054561170522152/941239897400950794/newdance-min.gif')

    # メッセージの本文が 一週間 だった場合
    if '一週間' in str(message.content) or '1週間' in str(message.content) or '1週間' in str(message.content):
        # メッセージが送られてきたチャンネルに送る
            await message.channel.send(yamadahouse_thumbnail)

    # メッセージの本文が バキ だった場合
    if 'バキ' in str(message.content):
        # メッセージが送られてきたチャンネルに送る
        await message.channel.send('https://cdn.discordapp.com/attachments/934792442178306108/942106647927595008/unknown.png')

    # メッセージの本文が big brother だった場合
    if 'big brother' in str(message.content):
        # メッセージが送られてきたチャンネルに送る
        await message.channel.send('https://cdn.discordapp.com/attachments/889054561170522152/942107244349247488/9BD8903B-74D1-4740-8EC8-13110C0D943C.jpg')

    # メッセージの本文が DJ だった場合
    if 'DJ' in str(message.content):
        # メッセージが送られてきたチャンネルに送る
        await message.channel.send('https://cdn.discordapp.com/attachments/889054561170522152/942107858496000010/a834912b8c8f9739.jpg')

    # メッセージの本文が メタ だった場合
    if 'メタ' in str(message.content):
        # メッセージが送られてきたチャンネルに送る
        await message.channel.send('https://media.discordapp.net/attachments/889054561170522152/942109742782889994/GWHiBiKi_StYle_9_-_YouTube_1.png')

    # メッセージの本文が 風呂 だった場合
    if '風呂' in str(message.content) or 'ふろ' in str(message.content):
        # あるくおすしの場合
        if message.author.id == walkingsushibox:
            # メッセージが送られてきたチャンネルに送る
            await message.channel.send('https://media.discordapp.net/attachments/889054561170522152/942389072117256192/19ffe7f2e7464263.png')
        # あるくおすし以外の場合
        # 俺か俺以外か（by あるくおすし）   
        else:
            # メッセージが送られてきたチャンネルに送る
            await message.channel.send('https://media.discordapp.net/attachments/889054561170522152/943155933343785040/d9ce03af4958b0b7.png')
    
    # メッセージの本文が ランキング だった場合
    if 'ランキング' in str(message.content):
        # メッセージが送られてきたチャンネルに送る
        await message.channel.send('https://media.discordapp.net/attachments/889054561170522152/942109619243864085/E8sV781VIAEtwZq.png')

    # メッセージの本文が おはよう だった場合
    if 'おはよう' in str(message.content):
        # メッセージが送られてきたチャンネルに送る
        await message.channel.send('https://media.discordapp.net/attachments/889054561170522152/942108884275982426/FJxaIJIaMAAlFYc.png')

    # メッセージの本文が いい曲 だった場合
    if 'いい曲' in str(message.content):
        # メッセージが送られてきたチャンネルに送る
        await message.channel.send('https://media.discordapp.net/attachments/889054561170522152/942071776815480832/unknown.png')
    
    # メッセージの本文が やんぱ だった場合
    if 'やんぱ' in str(message.content):
        # メッセージが送られてきたチャンネルに送る
        await message.channel.send('やんぱ2')
        
    # メッセージの本文が 精液 だった場合
    if '精液' in str(message.content):
        # メッセージが送られてきたチャンネルに送る
        await message.channel.send('https://cdn.discordapp.com/attachments/395580207970648064/944945500874997841/unknown.png')


    if message.attachments and message.channel.id == WIP_CHANNEL_ID:
        for attachment in message.attachments:
            # Attachmentの拡張子がmp3, wavのどれかだった場合
            # https://discordpy.readthedocs.io/ja/latest/api.html#attachment
            if "audio" in attachment.content_type:
                await attachment.save("input.mp3")
                command = "ffmpeg -y -loop 1 -i input.jpg -i input.mp3 -vcodec libx264 -vb 50k -acodec aac -strict experimental -ab 128k -ac 2 -ar 48000 -pix_fmt yuv420p -shortest output.mp4"
                proc = await asyncio.create_subprocess_exec(
                    *command.split(" "),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)

                stdout, stderr = await proc.communicate()
                await message.channel.send(file=discord.File("output.mp4"))
    await bot.process_commands(message)


# チーバくんの、なのはな体操
@bot.command()
async def chiibakun(ctx):
    await ctx.send('https://www.youtube.com/watch?v=dC0eie-WQss')


# かおすちゃんを送信
@bot.command()
async def kaosu(ctx):
    await ctx.send('https://pbs.twimg.com/media/E512yaSVIAQxfNn?format=jpg&name=large')


# イキス
@bot.command()
async def inm(ctx):
    await ctx.send('聖バリ「イキスギィイクイク！！！ンアッー！！！マクラがデカすぎる！！！」\n\n'
                   f'{ctx.author.name}「聖なるバリア －ミラーフォース－、淫夢はもうやめてよ！淫夢ごっこは恥ずかしいよ！」\n\n聖バリ「{ctx.author.name}'
                   '、おっ大丈夫か大丈夫か〜？？？バッチェ冷えてるぞ〜淫夢が大好きだってはっきりわかんだね」')


# ギラティナの画像を送る
@bot.command()
async def giratina(ctx):
    await ctx.send('https://img.gamewith.jp/article/thumbnail/rectangle/36417.png')


# bokuseku.mp3 流し逃げ - https://qiita.com/sizumita/items/cafd00fe3e114d834ce3
@bot.command()
async def bokuseku(ctx):
    if ctx.author.voice is None:
        await ctx.channel.send('望月くん・・・ボイスチャンネルに来なさい')
        return
    # ボイスチャンネルに接続する
    await ctx.author.voice.channel.connect()
    # 音声を再生する
    ctx.guild.voice_client.play(discord.FFmpegPCMAudio('bokuseku.mp3'))
    # 音声が再生中か確認する
    while ctx.guild.voice_client.is_playing():
        await sleep(1)
    # 切断する
    await ctx.guild.voice_client.disconnect()


token = getenv('DISCORD_BOT_TOKEN')
bot.run(token)
