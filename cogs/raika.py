import random
import re
import json
import requests
from discord.ext import commands

class Raika(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Raika
    @commands.command()
    async def raika(self, ctx):
        txtfile = open("resources/Wonderful_Raika_Tweet.txt", "r", encoding="utf-8")
        word = ",".join(
            list(map(lambda s: s.rstrip("\n"), random.sample(txtfile.readlines(), 1)))
        ).replace("[" ", " ").replace(" "]", "")
        url = [word]
        pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
        for url in url:
            if re.match(pattern, url):
                await ctx.channel.send(requests.get(url).url)
            else:
                await ctx.channel.send(word)

    # raikaマルコフ
    # https://monachanpapa-scripting.com/marukofu-python/ほぼ丸コピですすみません...
    @commands.command()
    async def mraika(self, ctx):
        text = json.loads(requests.get('https://api.giratina.net/v1/raika').text)['text']
        await ctx.channel.send(text)
