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
                    for i in range(0,input-1)[::-1]:
                        if not t == math.floor((i+1)/60):
                            await ctx.channel.send("残り"+str(t)+"分です！")
                        sleep(1)
                        t=math.floor((i+1)/60)
                        embed = discord.Embed(colour=0x5865f2, title=str(t)+":"+str((i+1)%60).zfill(2))
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

    @commands.command()
    async def st(self, ctx, *arg):
        if arg:
            input = arg[0]

            global t
            input = list(map(int,input.split(":")))
            input2 = input
            if len(input) == 2 and input[1] < 60:
                input = input[0] * 60 + input[1]
                t=math.floor(((input-1))/60)
                embed = discord.Embed(colour=0x5865f2, title=str(input2[0])+":"+str(input2[1]).zfill(2))
                t_msg: discord.Message = await ctx.channel.send(embed=embed) 
                for i in range(0,input-1)[::-1]:
                    if not t == math.floor((i+1)/60):
                        await ctx.channel.send("残り"+str(t)+"分です！")
                    sleep(1)
                    t=math.floor((i+1)/60)
                    embed = discord.Embed(colour=0x5865f2, title=str(t)+":"+str((i+1)%60).zfill(2))
                    await t_msg.edit(embed=embed)
                sleep(1)
                embed = discord.Embed(colour=0x5865f2, title="0:00")
                await t_msg.edit(embed=embed)
                await ctx.channel.send("時間です！")

                if ctx.author.voice is None:
                    await ctx.channel.send("ボイスチャンネルに入ってください")
                    await ctx.author.voice.channel.connect()
                ctx.guild.voice_client.play(discord.FFmpegPCMAudio("resources/Alarm.mp3"))
                while ctx.guild.voice_client.is_playing():
                    await asyncio.sleep(1)
                await ctx.guild.voice_client.disconnect()

        if not arg:
            embed = discord.Embed(colour=0xFF0000, title=f"時間を入力してください")
            t_msg: discord.Message = await ctx.channel.send(embed=embed)
    
    