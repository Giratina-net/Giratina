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


# メッセージ取得時に実行される関数
@bot.event
async def on_message(ctx):
    # 送信者がBotである場合は弾く
    # ここで弾けば以降は書かなくて良さそう
    if ctx.author.bot:
        return


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
