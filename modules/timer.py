import discord
import asyncio
from datetime import datetime, timedelta

def format_time(minutes, seconds):
    """時間を分:秒形式の文字列にフォーマットする"""
    return f"{minutes}:{str(seconds).zfill(2)}"

async def timer(minutes, seconds, t_msg):
    """Discordメッセージを使用してカウントダウンを表示するタイマー"""
    total_seconds = minutes * 60 + seconds

    # 初期表示
    embed = discord.Embed(colour=0x5865F2, title=format_time(minutes, seconds))
    await t_msg.edit(embed=embed)

    # タイマー開始時刻
    end_time = datetime.now() + timedelta(seconds=total_seconds)

    while total_seconds > 0:
        now = datetime.now()
        remaining_time = (end_time - now).total_seconds()

        if remaining_time <= 0:
            break

        # 残り時間の計算
        remains_minutes = int(remaining_time) // 60
        remains_seconds = int(remaining_time) % 60

        # Embed更新
        embed = discord.Embed(
            colour=0x5865F2, title=format_time(remains_minutes, remains_seconds)
        )
        await t_msg.edit(embed=embed)

        # 次の更新まで待機（実際の経過時間に基づき補正）
        await asyncio.sleep(min(1, remaining_time)) 