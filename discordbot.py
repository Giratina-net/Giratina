#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import time
from ntpath import join
from os import getenv

import discord
import tweepy
from discord.ext import commands
from googleapiclient.discovery import build
from spotdl import Spotdl

from cogs.annict import Annict
from cogs.hiroyuki import Hiroyuki
from cogs.kotobagari import Kotobagari
from cogs.music import Music
from cogs.others import Others
from cogs.raika import Raika
from cogs.twitter import Twitter
from cogs.uma import Uma
from cogs.utility import Utility
from constants import VOICECHAT_NOTIFICATION_CHANNEL_ID

# DiscordBot
DISCORD_BOT_TOKEN = getenv("DISCORD_BOT_TOKEN")
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
# Botの接頭辞を ! にする
bot = commands.Bot(command_prefix="!", intents=intents)


# spotdl
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET")
spotdl = Spotdl(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)

# google-api-python-client / YouTube Data API v3
YOUTUBE_API_KEY = getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Annict
ANNICT_API_KEY = getenv("ANNICT_API_KEY")

# Tweepy
TWITTER_CONSUMER_KEY = getenv("CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = getenv("CONSUMER_SECRET")
TWITTER_ACCESS_TOKEN_KEY = getenv("ACCESS_TOKEN_KEY")
TWITTER_ACCESS_TOKEN_SECRET = getenv("ACCESS_TOKEN_SECRET")

twauth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
twauth.set_access_token(TWITTER_ACCESS_TOKEN_KEY, TWITTER_ACCESS_TOKEN_SECRET)
twapi = tweepy.API(twauth)

client = discord.Client()


# Bot起動時に実行される関数
@bot.event
async def on_ready():
    now_time = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    await bot.change_presence(activity=discord.Game(name="ギラティナ、オォン！"))

    time.sleep(5)

    await bot.change_presence(
        activity=discord.Game(name=f"{now_time.strftime('%Y/%m/%d %H:%M:%S')} - オォン")
    )


# https://techblog.cartaholdings.co.jp/entry/archives/6412
# チャンネル入退室時の通知処理
@bot.event
async def on_voice_state_update(member, before, after):
    # チャンネルへの入室ステータスが変更されたとき（ミュートON、OFFに反応しないように分岐）
    if before.channel != after.channel:
        # 通知メッセージを書き込むテキストチャンネル（チャンネルIDを指定）
        notification_channel = bot.get_channel(VOICECHAT_NOTIFICATION_CHANNEL_ID)

        # 入退室を監視する対象のボイスチャンネル（チャンネルIDを指定）
        SEIBARI_VOICE_CHANNEL_IDs = [
            889049222152871990,
            889251836312309800,
            938212082363539526,
            889312365466775582,
            934783864226844682,
            934783998935302214,
            938212160075628624,
            956176543850311700,
            988470466249359461,
            1005195693465538591,
            1001860023917477908,
            937319677162565672,
            890539305276174357,
        ]

        # 終了通知
        if (
            before.channel is not None
            and before.channel.id in SEIBARI_VOICE_CHANNEL_IDs
        ):
            if len(before.channel.members) == 0:
                embed = discord.Embed(
                    colour=0xFF00FF,
                    title="通知",
                    description="**" + before.channel.name + "** の通話が終了しました",
                )
                await notification_channel.send(embed=embed)
        # 開始通知
        if after.channel is not None and after.channel.id in SEIBARI_VOICE_CHANNEL_IDs:
            if len(after.channel.members) == 1:
                embed = discord.Embed(
                    colour=0xFF00FF,
                    title="通知",
                    description="**" + after.channel.name + "** の通話が開始しました",
                )
                await notification_channel.send(embed=embed)


bot.add_cog(Annict(bot, ANNICT_API_KEY))
bot.add_cog(Music(bot, youtube, spotdl))
bot.add_cog(Twitter(bot, twapi))
bot.add_cog(Kotobagari(bot, youtube))
bot.add_cog(Uma(bot))
bot.add_cog(Hiroyuki(bot))
bot.add_cog(Raika(bot))
bot.add_cog(Utility(bot))
bot.add_cog(Others(bot))
bot.run(DISCORD_BOT_TOKEN)
