import aiohttp
import discord
import json
import os
import random
import urllib.parse

from discord.ext import commands
from PIL import Image
from io import BytesIO

from constants import FALCO_CHANNEL_ID, SEIBARI_GUILD_ID, TEIOU_CHANNEL_ID


class Uma(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ウマ娘ガチャシミュレーター
    @commands.command()
    async def uma(self, ctx, *args):
        async def send_uma(channel: discord.TextChannel, author: discord.Member, id: int, custom_weights=None):
            JSON_PATH = "resources/json/uma_userdata.json"

            class ButtonDrawAgain(discord.ui.Button):
                async def callback(self, inter: discord.Interaction):
                    response = inter.response
                    await response.edit_message(view=None)
                    await send_uma(inter.channel, inter.guild.get_member(inter.user.id), inter.id, custom_weights)

            async with channel.typing():
                with open(JSON_PATH, "r") as f:
                    user_info = json.load(f)

                for userdata in user_info["userdata"]:
                    if userdata["user_id"] == author.id:
                        my_chara_ids = userdata["my_chara_ids"]
                        ex_point = userdata["ex_point"]
                        user_info["userdata"] = [u for u in user_info["userdata"] if u["user_id"] != author.id]
                        break
                else:
                    my_chara_ids = []
                    ex_point = 0

                async with aiohttp.ClientSession() as session:
                    query = f"?c={urllib.parse.quote(','.join([str(id) for id in my_chara_ids]))}&p={ex_point}"
                    if custom_weights:
                        query += f"&w={urllib.parse.quote(','.join([str(w) for w in custom_weights]))}"
                    async with session.get(f"https://api.giratina.net/v1/uma{query}") as resp:
                        data = await resp.json()
                    my_chara_ids = data["my_charas"]
                    ex_point = data["ex_point"]
                    async with session.get(data["result_img_url"]) as resp:
                        image_path = f"resources/temporary/uma_{id}.png"
                        image = Image.open(BytesIO(await resp.read()))
                        image.save(image_path)

                user_info["userdata"].append({
                    "user_id": author.id,
                    "my_chara_ids": my_chara_ids,
                    "ex_point": ex_point
                })

            button = ButtonDrawAgain(style=discord.ButtonStyle.success, label="もう一回引く")
            view = discord.ui.View(timeout=None)
            view.add_item(button)
            embed = discord.Embed(
                title=f"{author.display_name} さんのガチャ結果",
                description=f"総獲得キャラ数 : **{len(my_chara_ids)}** 体",
                color=0x18bb59
            )
            file = discord.File(fp=image_path, filename="image.png")
            embed.set_image(url=f"attachment://image.png")

            await channel.send(embed=embed, file=file, view=view)
            del file
            os.remove(image_path)

            with open(JSON_PATH, "w") as f:
                json.dump(user_info, f, indent=4)

        # argsの処理
        try:
            if len(args) > 2:
                custom_weights = [float(arg) for arg in args[:3]]
                custom_weights = [i / sum(custom_weights) for i in custom_weights]
            else:
                custom_weights = None
        except:
            custom_weights = None

        await send_uma(ctx.channel, ctx.author, ctx.message.id, custom_weights)

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
