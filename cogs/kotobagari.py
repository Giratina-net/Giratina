import asyncio
import discord
from discord.ext import commands
from googleapiclient.discovery import build
import os
from os import getenv
import random
from yt_dlp import YoutubeDL

from constants import PASOJIN_GUILD_ID, WALKINGSUSHIBOX_USER_ID, WIP_CHANNEL_ID


# google-api-python-client / YouTube Data API v3
YOUTUBE_API_KEY = getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


class Kotobagari(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, ctx):
        # 送信者がBotである場合は弾く
        # ここで弾けば以降は書かなくて良さそう
        if ctx.author.bot:
            return

        if ctx.guild.id == PASOJIN_GUILD_ID:
            return

        await self.bot.process_commands(ctx)

        # メッセージの本文が big brother だった場合
        if "big brother" in str(ctx.content):
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942107244349247488/9BD8903B-74D1-4740-8EC8-13110C0D943C.jpg")

        # メッセージの本文が somunia だった場合
        if "somunia" in str(ctx.content):
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("https://twitter.com/aaruaika/status/1518874935024054272")

        # メッセージの本文が アーメン だった場合
        if "アーメン" in str(ctx.content):
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("https://media.discordapp.net/attachments/964831309627289620/1012764896900956281/unknown.png")

        # メッセージの本文が いい曲 だった場合
        if "いい曲" in str(ctx.content):
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942071776815480832/unknown.png")

        # メッセージの本文が おはよう だった場合
        if "おはよう" in str(ctx.content):
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942108884275982426/FJxaIJIaMAAlFYc.png")

        # メッセージの本文が カニ だった場合
        if "かに" in str(ctx.content) or "カニ" in str(ctx.content):
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("https://media.discordapp.net/attachments/964831309627289620/1006257985846263808/6C4D7AD5-ADBA-4BC7-824C-5A118E09A43A.png")

        # メッセージの本文が クワガタ だった場合
        if "くわがた" in str(ctx.content) or "クワガタ" in str(ctx.content):
            # メッセージが送られてきたチャンネルに送る
            images_kuwagata = [
                "https://cdn.discordapp.com/attachments/959475816209739796/1000340129703006218/14C3BEA6-F0E3-4046-97E7-2D37732A3F75.png",
                "https://media.discordapp.net/attachments/991551726308048896/1012775482955145347/Fa_-bj2aUAALUIr.png"
            ]
            image_pickup = random.choice(images_kuwagata)
            await ctx.channel.send(image_pickup)

        # ドナルドの言葉狩り - https://qiita.com/sizumita/items/9d44ae7d1ce007391699
        # メッセージの本文が ドナルド だった場合
        if "ドナルド" in str(ctx.content):
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("https://tenor.com/view/ronald-mcdonald-insanity-ronald-mcdonald-gif-21974293")

        # メッセージの本文が バキ だった場合
        if "バキ" in str(ctx.content):
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("https://cdn.discordapp.com/attachments/934792442178306108/942106647927595008/unknown.png")

        # メッセージの本文が メタ だった場合
        if "メタ" in str(ctx.content):
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942109742782889994/GWHiBiKi_StYle_9_-_YouTube_1.png")

        # メッセージの本文が やんぱ だった場合
        if "やんぱ" in str(ctx.content):
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("やんぱ2")

        # メッセージの本文が ライカ だった場合
        if "ライカ" in str(ctx.content):
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("はぁ、どちら様ですか？")

        # メッセージの本文が ランキング だった場合
        if "ランキング" in str(ctx.content):
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942109619243864085/E8sV781VIAEtwZq.png")

        # メッセージの本文が 一週間 だった場合
        if "一週間" in str(ctx.content) or "1週間" in str(ctx.content):
            yamadahouse_thumbnails = []

            # サムネイルをAPIで取得
            yamadahouse_response = youtube.search().list(channelId="UCmEG6Kw9z2PJM2yjQ1VQouw", part="snippet", maxResults=50).execute()

            for item in yamadahouse_response.get("items", []):
                # 一番高画質なサムネイルのキーを取得
                yamadahouse_highres_thumb = list(item["snippet"]["thumbnails"].keys())[-1]
                # サムネイルのURLだけを抽出して配列に突っ込む
                yamadahouse_thumbnails.append(item["snippet"]["thumbnails"][yamadahouse_highres_thumb]["url"])

            # サムネイルURLの配列内から1つランダムで選ぶ
            yamadahouse_random_thumb = random.choice(yamadahouse_thumbnails)

            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send(yamadahouse_random_thumb)

        # メッセージの本文が 君しかいないんだよ だった場合
        if "君しかいないんだよ" in str(ctx.content):
            # メッセージが送られてきたチャンネルに送る
            ydl_opts_you = {
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "outtmpl": "you.mp3",
            }
            with YoutubeDL(ydl_opts_you) as ydl:
                ydl.download(["https://soundcloud.com/kejiramikitanai/h9jsjiorr7ln"])
            # ボイスチャンネルに接続する
            if ctx.author.voice is None:
                return
            if ctx.guild.voice_client is None:
                await ctx.author.voice.channel.connect()
            # 音声を再生する
            ctx.guild.voice_client.play(discord.FFmpegPCMAudio("you.mp3"))
            # 音声が再生中か確認する
            while ctx.guild.voice_client.is_playing():
                await asyncio.sleep(1)
            # 切断する
            await ctx.guild.voice_client.disconnect()

        # メッセージの本文が 死んだ だった場合
        if "死んだ" in str(ctx.content) or "しんだ" in str(ctx.content):
            # メッセージが送られてきたチャンネルに送る
            await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/941239897400950794/newdance-min.gif")

        # メッセージの本文が 昼 だった場合
        if "昼" in str(ctx.content) or "おひる" in str(ctx.content):
            images = [
                "https://cdn.discordapp.com/attachments/1002875196522381325/1003699645458944011/FTakxQUaIAAoyn3CUnetnoise_scaleLevel2x4.000000.png",
                "https://cdn.discordapp.com/attachments/1002875196522381325/1008245051077443664/FZmJ06EUIAAcZNi.jpg"
            ]
            image_pickup = random.choice(images)
            await ctx.channel.send(image_pickup)

        # メッセージの本文が 風呂 だった場合
        if "風呂" in str(ctx.content) or "ふろ" in str(ctx.content):
            # あるくおすしの場合
            if ctx.author.id == WALKINGSUSHIBOX_USER_ID:
                # メッセージが送られてきたチャンネルに送る
                await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/942389072117256192/19ffe7f2e7464263.png")
            # あるくおすし以外の場合
            # 俺か俺以外か（by あるくおすし）   
            else:
                # メッセージが送られてきたチャンネルに送る
                await ctx.channel.send("https://cdn.discordapp.com/attachments/889054561170522152/943155933343785040/d9ce03af4958b0b7.png")

        if ctx.attachments and ctx.channel.id == WIP_CHANNEL_ID:
            for attachment in ctx.attachments:
                # Attachmentの拡張子がmp3, wavのどれかだった場合
                # https://discordpy.readthedocs.io/ja/latest/api.html#attachment
                if "audio" in attachment.content_type:
                    await attachment.save("resources/temporary/wip_input.mp3")
                    command = "ffmpeg -y -loop 1 -i resources/wip_input.jpg -i resources/temporary/wip_input.mp3 -vcodec libx264 -vb 50k -acodec aac -strict experimental -ab 128k -ac 2 -ar 48000 -pix_fmt yuv420p -shortest resources/temporary/wip_output.mp4"
                    proc = await asyncio.create_subprocess_exec(*command.split(" "), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                    stdout, stderr = await proc.communicate()
                    await ctx.channel.send(file=discord.File("resources/temporary/wip_output.mp4"))
                    os.remove("resources/temporary/wip_input.mp3")
                    os.remove("resources/temporary/wip_output.mp4")
