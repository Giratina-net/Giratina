import discord
import asyncio
import os
import math
from datetime import datetime, timedelta


async def timer(minutes, seconds, t_msg):
    total_seconds = minutes * 60 + seconds
    embed = discord.Embed(colour=0x5865F2, title=f"{minutes}:{str(seconds).zfill(2)}")
    await t_msg.edit(embed=embed)
    start_time = datetime.now()
    while True:
        await asyncio.sleep(0.7)
        duration = (datetime.now() - start_time).seconds
        remains = total_seconds - duration
        if remains < 0: #embedの表示
            remains = 0
        remains_minutes = remains // 60  # // は切り捨て除算
        remains_seconds = remains % 60  # % はあまり
        embed = discord.Embed(
            colour=0x5865F2, title=f"{remains_minutes}:{str(remains_seconds).zfill(2)}"
        )
        await t_msg.edit(embed=embed)
        if remains <= 0: #終了条件
            break

    # for i in range(0, total_seconds)[::-1]:
    #     await asyncio.sleep(1)
    #     remains_minutes = i // 60 # // は切り捨て除算
    #     remains_seconds = i % 60 # % はあまり
    #     embed = discord.Embed(
    #         colour=0x5865F2, title=f"{remains_minutes}:{str(remains_seconds).zfill(2)}"
    #     )
    #     await t_msg.edit(embed=embed)
