import discord
import asyncio
import os
import math


async def timer(minutes, seconds, t_msg):
    total_seconds = minutes * 60 + seconds
    embed = discord.Embed(
        colour=0x5865F2, title=str(minutes) + ":" + str(seconds).zfill(2)
    )
    await t_msg.edit(embed=embed)
    for i in range(0, total_seconds)[::-1]:
        await asyncio.sleep(1)
        minutes_remains = math.floor(i / 60)
        embed = discord.Embed(
            colour=0x5865F2, title=str(minutes_remains) + ":" + str(i % 60).zfill(2)
        )
        await t_msg.edit(embed=embed)
