import random

from discord.ext import commands

import modules.funcs
from constants import FALCO_CHANNEL_ID, SEIBARI_GUILD_ID, TEIOU_CHANNEL_ID


class Uma(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ウマ娘ガチャシミュレーター
    @commands.command()
    async def uma(self, ctx, *args):
        try:
            if len(args) > 2:
                custom_weights = [int(i) for i in args[:3]]
                weights_sum = sum(custom_weights)
                custom_weights = [i / weights_sum * 100 for i in custom_weights]
            else:
                custom_weights = None
        except:
            custom_weights = None
        await modules.funcs.send_uma(ctx.channel, ctx.author, custom_weights)

    # ファルコおもしろ画像を送信
    @commands.command(aliases=["teiou", "teio", "teio-"])
    async def toukaiteiou(self, ctx):
        guild = self.bot.get_guild(SEIBARI_GUILD_ID)

        channel = guild.get_channel(TEIOU_CHANNEL_ID)

        teiou_channel_messages = [
            message async for message in channel.history(limit=None)
        ]

        random_teiou = random.choice(teiou_channel_messages)

        content = (
            random_teiou.attachments[0].url
            if random_teiou.content == ""
            else random_teiou.content
        )

        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send(content)

    # ファルコおもしろ画像を送信
    @commands.command(aliases=["syai", "faruko"])
    async def falco(self, ctx):
        guild = self.bot.get_guild(SEIBARI_GUILD_ID)

        channel = guild.get_channel(FALCO_CHANNEL_ID)

        falco_channel_messages = [
            message async for message in channel.history(limit=None)
        ]

        random_falco = random.choice(falco_channel_messages)

        content = (
            random_falco.attachments[0].url
            if random_falco.content == ""
            else random_falco.content
        )

        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send(content)
