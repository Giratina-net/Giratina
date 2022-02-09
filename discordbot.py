import traceback
from os import getenv
import discord
from discord.ext import commands
import time

client = discord.Client()

# botの接頭辞を!にする
bot = commands.Bot(command_prefix='!')

# ギラティナのチャンネルのID
GIRATINA_CHANNNEL_ID = 940610524415144036


@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(
        traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)

# 起動時のメッセージの関数


async def ready_greet():
    channel = bot.get_channel(GIRATINA_CHANNNEL_ID)
    await channel.send('ギラティナ、オォン！')

# 起動時に挨拶をする


@bot.event
async def on_ready():
    await ready_greet()

# ピンポン


@bot.command()
async def ping(ctx):
    await ctx.send('pong')

# ドナルドの言葉狩り
# https://qiita.com/sizumita/items/9d44ae7d1ce007391699


@bot.event
async def on_message(message):
    # 送信者がbotである場合は弾く
    if message.author.bot:
        return
    # メッセージの本文が ドナルド だった場合
    if 'ドナルド' in str(message.content):
        # 送信するメッセージをランダムで決める
        # メッセージが送られてきたチャンネルに送る
        await message.channel.send('https://tenor.com/view/ronald-mcdonald-insanity-ronald-mcdonald-gif-21974293')
    await bot.process_commands(message)

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
    await ctx.send('聖バリ「イキスギィイクイク！！！ンアッー！！！マクラがデカすぎる！！！」\n\n'
                   f'{ctx.author.name}「聖なるバリア －ミラーフォース－、淫夢はもうやめてよ！淫夢ごっこは恥ずかしいよ！」\n\n聖バリ「{ctx.author.name}'
                   '、おっ大丈夫か大丈夫か〜？？？バッチェ冷えてるぞ〜淫夢が大好きだってはっきりわかんだね」')

# ギラティナの画像を送る


@bot.command()
async def giratina(ctx):
    await ctx.send('https://images-ext-2.discordapp.net/external/tlYUDsXqoCwJa6TnXCp6V2EnfB9ziojMGuOb_rt1XuU/https/img.gamewith.jp/article/thumbnail/rectangle/36417.png')

# https://qiita.com/sizumita/items/cafd00fe3e114d834ce3


@bot.command()
async def bokuseku(ctx):
    if ctx.author.voice is None:
        await ctx.channel.send("望月くん・・・ボイスチャンネルに来なさい")
        return
    # ボイスチャンネルに接続する
    await ctx.author.voice.channel.connect()
    # 音声を再生する
    ctx.guild.voice_client.play(discord.FFmpegPCMAudio("bokuseku.mp3"))
    # 接続して110秒経つと切断する
    time.sleep(110) # 110秒待機させる 
    ctx.guild.voice_client.disconnect()


token = getenv('DISCORD_BOT_TOKEN')
bot.run(token)
