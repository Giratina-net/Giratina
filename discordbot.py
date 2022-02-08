from asyncore import read
import discord
from discord.ext import commands
from os import getenv
import traceback
import discord

client = discord.Client()

# botの接頭辞を!にする
bot = commands.Bot(command_prefix='!')

# ボイスチャンネルの聖なるバリア-－ミラーフォース－のチャンネルのID
SEIBARI_CHANNNEL_ID = 889054561170522152


@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(
        traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)

# 起動時のメッセージの関数


async def ready_greet():
    channel = bot.get_channel(SEIBARI_CHANNNEL_ID)
    await channel.send('ギラティナ、オォン！')

# 起動時に挨拶をする


@bot.event
async def on_ready():
    await ready_greet()

# ピンポン


@bot.command()
async def ping(ctx):
    await ctx.send('pong')

# チーバくんの、なのはな体操


@bot.command()
async def chiibakun(ctx):
    await ctx.send('https://youtu.be/dC0eie-WQss')

# かおすちゃんを送信


@bot.command()
async def kaosu(ctx):
    await ctx.send('https://pbs.twimg.com/media/E512yaSVIAQxfNn?format=jpg&name=large')

# イキス


@bot.command()
async def inm(ctx):
    await ctx.send('イキスギィイクイク！！！\nンアッー！！！\nマクラがデカすぎる！！！\n\n'
                   f'聖なるバリア －ミラーフォース－、淫夢はもうやめてよ！\n淫夢ごっこは恥ずかしいよ！\n\n{str(ctx.author).split("#")[0]}'
                   '、おっ大丈夫か大丈夫か〜？？？\nバッチェ冷えてるぞ〜\n淫夢が大好きだってはっきりわかんだね')

# ギラティナの画像を送る


@bot.command()
async def giratina(ctx):
    await ctx.send('https://images-ext-2.discordapp.net/external/tlYUDsXqoCwJa6TnXCp6V2EnfB9ziojMGuOb_rt1XuU/https/img.gamewith.jp/article/thumbnail/rectangle/36417.png')

<<<<<<< HEAD
=======

# https://qiita.com/sizumita/items/cafd00fe3e114d834ce3

@bot.command()
async def bokuseku(ctx):
    if ctx.author.voice is None:
        await ctx.channel.send("あなたはボイスチャンネルに接続していません。")
        return
    # ボイスチャンネルに接続する
    await ctx.author.voice.channel.connect()
    # 音声を再生する
    ctx.guild.voice_client.play(discord.FFmpegPCMAudio("bokuseku.mp3"))

>>>>>>> 4ac5ab49c9ed33548c8a110e5590cc10cb08105a
token = getenv('DISCORD_BOT_TOKEN')
bot.run(token)
