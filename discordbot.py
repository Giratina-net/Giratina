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
async def chiibakun(ctx):
    await ctx.send('https://twitter.com/chi_bakun_chiba')

@bot.command()
async def kaosu(ctx):
    await ctx.send('https://pbs.twimg.com/media/E512yaSVIAQxfNn?format=jpg&name=large')

@bot.command()
async def inm(ctx):
    await ctx.send('イキスギィイクイク！！！\nンアッー！！！\nマクラがデカすぎる！！！\n\n'
                   f'聖なるバリア －ミラーフォース－、淫夢はもうやめてよ！\n淫夢ごっこは恥ずかしいよ！\n\n{ctx.author.split("#")[0]}'
                   '、おっ大丈夫か大丈夫か〜？？？\nバッチェ冷えてるぞ〜\n淫夢が大好きだってはっきりわかんだね')

@bot.command()
async def giratina(ctx):
    await ctx.send('https://images-ext-2.discordapp.net/external/tlYUDsXqoCwJa6TnXCp6V2EnfB9ziojMGuOb_rt1XuU/https/img.gamewith.jp/article/thumbnail/rectangle/36417.png')


token = getenv('DISCORD_BOT_TOKEN')
bot.run(token)
