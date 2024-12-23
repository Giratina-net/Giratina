import asyncio
import random

import discord
from discord.ext import commands

from constants import (
    MACHITAN_CHANNEL_ID,
    NO_CONTEXT_HENTAI_IMG_CHANNEL_ID,
    SEIBARI_GUILD_ID,
    SIRONEKO_GUILD_ID,
)


class Others(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # bokuseku.mp3 流し逃げ - https://qiita.com/sizumita/items/cafd00fe3e114d834ce3
    @commands.command()
    async def bokuseku(self, ctx):
        # 実行したユーザーがボイスチャンネルに居ない場合は拒否
        if ctx.author.voice is None:
            await ctx.channel.send("望月くん・・・ボイスチャンネルに来なさい")
            return

        # ボイスチャンネルに接続する
        if ctx.guild.voice_client is None:
            await ctx.author.voice.channel.connect()

        # 音声を再生する
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio("resources/bokuseku.mp3"))

        # 音声が再生中か確認する
        while ctx.guild.voice_client.is_playing():
            await asyncio.sleep(1)

        # 切断する
        await ctx.guild.voice_client.disconnect()

    # チーバくんの、なのはな体操
    @commands.command()
    async def chiibakun(self, ctx):
        await ctx.channel.send("https://www.youtube.com/watch?v=dC0eie-WQss")

    # ギラティナの画像を送る
    @commands.command()
    async def giratina(self, ctx):
        await ctx.channel.send(
            "https://img.gamewith.jp/article/thumbnail/rectangle/36417.png"
        )

    # no context hentai imgの画像を送信
    @commands.command()
    async def hentai(self, ctx):
        guild = self.bot.get_guild(SIRONEKO_GUILD_ID)

        channel = guild.get_channel(NO_CONTEXT_HENTAI_IMG_CHANNEL_ID)

        hentai_channel_messages = [
            message async for message in channel.history(limit=None)
        ]

        random_hentai = random.choice(hentai_channel_messages)

        content = (
            random_hentai.attachments[0].url
            if random_hentai.content == ""
            else random_hentai.content
        )

        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send(content)

    # イキス
    @commands.command()
    async def inm(self, ctx):
        await ctx.channel.send(
            "聖バリ「イキスギィイクイク！！！ンアッー！！！マクラがデカすぎる！！！」\n\n"
            f"{ctx.author.name}「聖なるバリア －ミラーフォース－、淫夢はもうやめてよ！淫夢ごっこは恥ずかしいよ！」\n\n"
            f"聖バリ「{ctx.author.name}、おっ大丈夫か大丈夫か〜？？？バッチェ冷えてるぞ〜淫夢が大好きだってはっきりわかんだね」"
        )

    @commands.command()
    async def ma(self, ctx):
        await ctx.channel.send(
            "https://cdn.discordapp.com/attachments/964831309627289620/982691239025598494/long_ver.___feat._0s_screenshot.png"
        )

    # マノム
    @commands.command(aliases=["mano"])
    async def manomu(self, ctx):
        await ctx.channel.send(
            "家で飼ってるピーちゃんを\n"
            + "　　　　使ったお料理も好きです。\n\n"
            + "　　　　　あ　ら　ま\n\n"
            + "動物性たんぱくパク　たべるルル\n\n"
            + "　　　　＼内臓もっと／\n\n"
            + "頂戴な　　　　　　　　　頂戴な\n"
            + "ねぇ　　　　　　　　　　　ねぇ\n\n"
            + "　　灯織ちゃんもおいでって"
        )
