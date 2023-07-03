import requests
import discord
from discord.ext import commands
from os import getenv
#envから取得
KUTT_HOST = getenv("KUTT_HOST")+"/api/v2/links"
KUTT_API_KEY = getenv("KUTT_API_KEY")
def gen(url):
    try:
        r = requests.post(KUTT_HOST, data={"target": url}, headers={'X-API-KEY': KUTT_API_KEY}).json()
        return r['link']
    except:
        return "False"
class Short(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.command()
    async def short(self, ctx, *arg):
        url = gen(arg[0])
        await ctx.channel.send(url)