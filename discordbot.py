import asyncio
import traceback
from asyncio import sleep
from os import getenv

import discord
from discord.ext import commands

client = discord.Client()

# botの接頭辞を!にする
bot = commands.Bot(command_prefix='!')

# ギラティナのチャンネルのID
GIRATINA_CHANNEL_ID = 940610524415144036
WIP_CHANNEL_ID = 940966825087361025


@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, 'original', error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
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

    # メッセージの本文が 死んだ だった場合
    if '死んだ' in str(message.content) or 'しんだ' in str(message.content):
        # メッセージが送られてきたチャンネルに送る
        await message.channel.send('https://cdn.discordapp.com/attachments/889054561170522152/941239897400950794/newdance-min.gif')

    # メッセージの本文が 一週間 だった場合
    if '一週間' in str(message.content) or '1週間' in str(message.content) or '1週間' in str(message.content):
        # メッセージが送られてきたチャンネルに送る
            await message.channel.send('https://cdn.discordapp.com/attachments/889054561170522152/942114480152801361/1641506349_maxresdefault-768x432.png')

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

    # メッセージの本文が めし だった場合
    if '飯' in str(message.content) or 'めし' in str(message.content):
    # メッセージが送られてきたチャンネルに送る
        await message.channel.send('https://cdn.discordapp.com/attachments/889054561170522152/942113269034938368/09EEE9A4-03B9-471A-A7D4-372FB51EEE80.jpg')
    
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
    await ctx.send('https://twitter.com/onmokosub/status/1491369057354149889')


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
