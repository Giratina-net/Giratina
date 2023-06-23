from time import sleep
import math
import discord
from discord.ext import commands
import asyncio
class timer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.command()
    async def t(self, ctx, *arg):
        if arg:
            input = arg[0]
            try:
                global t
                input = list(map(int,input.split(":")))
                input2 = input
                if len(input) == 2 and input[1] < 60:
                    input = input[0] * 60 + input[1]
                    t=math.floor(((input-1))/60)
                    embed = discord.Embed(colour=0x5865f2, title=str(input2[0])+":"+str(input2[1]).zfill(2))
                    t_msg: discord.Message = await ctx.channel.send(embed=embed) 
                    input3 = input
                    for i in range(0,input-1)[::-1]:
                        if not t == math.floor((i+1)/60):
                            await ctx.channel.send("残り"+str(t)+"分です！")
                        sleep(1)
                        t=math.floor((i+1)/60)
                        j=math.floor(100*(1-(i/input3)))
                        j2=int(str(j).zfill(2)[-2])
                        prog=f"　　［{'＃' * j2}{'　' * ( 10 - j2)}］  {j}%"
                        embed = discord.Embed(colour=0x5865f2, title=str(t)+":"+str((i+1)%60).zfill(2)+prog+"\n")
                        await t_msg.edit(embed=embed)
                    sleep(1)
                    embed = discord.Embed(colour=0x5865f2, title="0:00")
                    await t_msg.edit(embed=embed)
                    await ctx.channel.send("時間です！")
            except:
                await ctx.channel.send("値がおかしいです！たぶん！")
        if not arg:
            embed = discord.Embed(colour=0xFF0000, title=f"時間を入力してください")
            t_msg: discord.Message = await ctx.channel.send(embed=embed)
