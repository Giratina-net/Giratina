import traceback
from os import getenv
import discord
from discord import Message
from discord.ext import commands
from discord.ext.commands import Context
from asyncio import sleep
import asyncio

client = discord.Client()

# botの接頭辞を!にする
bot = commands.Bot(command_prefix='!')

# ギラティナのチャンネルのID
GIRATINA_CHANNEL_ID = 940610524415144036
WIP_CHANNEL_ID = 940966825087361025


@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, 'original', error)
    error_msg = ''.join(
        traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)


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
    # メッセージに場合

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


# オンモコスブのツイートを送信
@bot.command()
async def on(ctx):
    await ctx.send('https://twitter.com/onmokosub/status/1491369057354149889?s=20&t=D2p9TZ8np-s4a3L-zXwM3Q')


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
