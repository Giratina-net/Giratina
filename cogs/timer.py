import math
import discord
from discord.ext import commands
import asyncio
import modules.timer


class Timer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def timer(self, ctx, hunbyou):
        embed = discord.Embed(colour=0x5865F2, title="99:99")
        t_msg: discord.Message = await ctx.channel.send(embed=embed)
        if hunbyou:
            try:
                hunbyou = list(map(int, hunbyou.split(":")))
                timer_task = asyncio.create_task(modules.timer.timer(hunbyou[0], hunbyou[1], t_msg))
                await timer_task
                await ctx.channel.send("時間です！")
            except Exception as e:
                await ctx.channel.send("値がおかしいです！たぶん！")
                raise e
        if not hunbyou:
            embed = discord.Embed(colour=0xFF0000, title=f"時間を入力してください")
            t_msg: discord.Message = await ctx.channel.send(embed=embed)






##############################################################################################################
#
 
# 涼風青葉「こんにちは」
# 涼風青葉「今日は何をするの？」
# 涼風青葉「あ、そうだ！今日はゲームの日だよね！」
# 涼風青葉「ゲームの日にはゲームをするんだよ！」
# 涼風青葉「ゲームの日にゲームをしないなんて、ゲームの日を祝ってないのと同じだよ！」
# 飯島ゆん「ゲームの日って何？」
# 涼風青葉「ゲームの日は、ゲームをする日だよ！」
# 涼風青葉「ゲームの日にゲームをしないなんて、ゲームの日を祝ってないのと同じだよ！」


# 

# Discord Server -> [message] -> Giratina
# 
# message = 文字列 "!timer 2:00"
# message.startwith("!")
# たぶんコマンドだろう
# "timer" ← Giratina「timerコマンドを探す」
# timer.timer(コンテキスト, "2:00")
