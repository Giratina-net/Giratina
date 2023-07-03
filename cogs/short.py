import mod
import discord
from discord.ext import commands

class Short(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.command()
    async def short(self, ctx, *arg):
        url = mod.short(arg[0])
        await ctx.channel.send(url)