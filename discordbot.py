from discord.ext import commands
from os import getenv
import traceback

bot = commands.Bot(command_prefix='!')


@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)


@bot.command()
async def ping(ctx):
    await ctx.send('pong')


@bot.command()
async def kaosu(ctx):
    await ctx.send('https://pbs.twimg.com/media/E512yaSVIAQxfNn?format=jpg&name=large')


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

token = getenv('DISCORD_BOT_TOKEN')
bot.run(token)
