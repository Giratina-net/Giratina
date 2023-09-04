import discord
from discord.ext import commands
import requests
import json
from os import getenv

G2YDL_HOST = getenv("G2YDL_HOST")+"/v1/ydl"
G2YDL_API_KEY = getenv("G2YDL_API_KEY")

def ydl(type, url):
    headers={"Authorization": "Bearer "+G2YDL_API_KEY, "Content-Type": "application/json","type": type, "url": url}
    r=requests.get(G2YDL_HOST , headers=headers)
    d =json.loads(r.text)
    if r.status_code == requests.codes.ok:
        return d["url"]
    else:
        return "エラーーなのです"

class Ydl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ydl(self, ctx, url):
        await ctx.send("ダウンロードを開始します")
        url=ydl("mp4", url)
        await ctx.send(url)

    @commands.command()
    async def ydl3(self, ctx, url):
        await ctx.send("ダウンロードを開始します")
        url=ydl("mp3", url)
        await ctx.send(url)
        
    @commands.command()
    async def ydla(self, ctx, url):
        await ctx.send("ダウンロードを開始します")
        url=ydl("mp3_album", url)
        await ctx.send(url)