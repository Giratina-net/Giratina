#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import csv
import datetime
import gdshortener
import glob
import MeCab
from nltk import ngrams
from ntpath import join
import os
import random
import re
# import sys
import ffmpeg
import time
import discord
import modules.funcs
import requests
import tweepy
from collections import Counter, defaultdict
from discord.ext import commands
from os import getenv

from cogs.music import Music
from cogs.kotobagari import Kotobagari

from constants import VOICECHAT_NOTIFICATION_CHANNEL_ID, SEIBARI_GUILD_ID, SIRONEKO_GUILD_ID, FALCO_CHANNEL_ID, MACHITAN_CHANNEL_ID, NO_CONTEXT_HENTAI_IMG_CHANNEL_ID, TEIOU_CHANNEL_ID

# DiscordBot
DISCORD_BOT_TOKEN = getenv("DISCORD_BOT_TOKEN")
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
# Botの接頭辞を ! にする
bot = commands.Bot(command_prefix="!", intents=intents)

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

    await bot.change_presence(activity=discord.Game(name=f"{now_time.strftime('%Y/%m/%d %H:%M:%S')} - オォン"))


# https://techblog.cartaholdings.co.jp/entry/archives/6412
# チャンネル入退室時の通知処理
@bot.event
async def on_voice_state_update(member, before, after):
    # チャンネルへの入室ステータスが変更されたとき（ミュートON、OFFに反応しないように分岐）
    if before.channel != after.channel:
        # 通知メッセージを書き込むテキストチャンネル（チャンネルIDを指定）
        notification_channel = bot.get_channel(VOICECHAT_NOTIFICATION_CHANNEL_ID)

        # 入退室を監視する対象のボイスチャンネル（チャンネルIDを指定）
        SEIBARI_VOICE_CHANNEL_IDs = [889049222152871990, 889251836312309800, 938212082363539526, 889312365466775582, 934783864226844682, 934783998935302214, 938212160075628624, 956176543850311700,
                                     988470466249359461, 1005195693465538591, 1001860023917477908, 937319677162565672, 890539305276174357]

        # 終了通知
        if before.channel is not None and before.channel.id in SEIBARI_VOICE_CHANNEL_IDs:
            if len(before.channel.members) == 0:
                embed = discord.Embed(colour=0xff00ff, title="通知", description="**" + before.channel.name + "** の通話が終了しました")
                await notification_channel.send(embed=embed)
        # 開始通知
        if after.channel is not None and after.channel.id in SEIBARI_VOICE_CHANNEL_IDs:
            if len(after.channel.members) == 1:
                embed = discord.Embed(colour=0xff00ff, title="通知", description="**" + after.channel.name + "** の通話が開始しました")
                await notification_channel.send(embed=embed)


# アニクトから取得したアニメをランダムで表示
@bot.command(aliases=["ani"])
async def anime(ctx):
    random_id = random.randint(1, 9669)
    # エンドポイント
    annict_url = f"https://api.annict.com/v1/works?access_token={ANNICT_API_KEY}&filter_ids={random_id}"
    # リクエスト
    annict_res = requests.get(annict_url)
    # 取得したjsonから必要な情報を取得
    annict_works = annict_res.json()["works"][0]
    annict_works_title = annict_works["title"]
    annict_works_season_name_text = annict_works["season_name_text"]
    annict_works_episodes_count = annict_works["episodes_count"]
    annict_works_images_recommended_url = annict_works["images"]["recommended_url"]
    await ctx.channel.send(f"{annict_works_title}({annict_works_season_name_text}-{annict_works_episodes_count}話)\nhttps://annict.com/works/{random_id}")


# bokuseku.mp3 流し逃げ - https://qiita.com/sizumita/items/cafd00fe3e114d834ce3
@bot.command()
async def bokuseku(ctx):
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
@bot.command()
async def chiibakun(ctx):
    await ctx.channel.send("https://www.youtube.com/watch?v=dC0eie-WQss")


# ファルコおもしろ画像を送信
@bot.command(aliases=["syai", "faruko"])
async def falco(ctx):
    guild = bot.get_guild(SEIBARI_GUILD_ID)

    channel = guild.get_channel(FALCO_CHANNEL_ID)

    falco_channel_messages = [message async for message in channel.history(limit=None)]

    random_falco = random.choice(falco_channel_messages)

    content = random_falco.attachments[0].url if random_falco.content == "" else random_falco.content

    # メッセージが送られてきたチャンネルに送る
    await ctx.channel.send(content)


# ファミ通
@bot.command(aliases=["fami", "famitu", "fami2"])
async def famitsu(ctx):
    texts = []
    tweets = twapi.search_tweets(q="from:@fami2repo_bot", count=10)
    for tweet in tweets:
        text = tweet.text
        texts.append(text)
    text_pickup = random.choice(texts)
    await ctx.channel.send(text_pickup)


# Twitterから#GenshinImpactの1000いいね以上を探して送信
@bot.command(aliases=["gennshinn", "gensin", "gennsinn", "gs"])
async def genshin(ctx):
    tweets = twapi.search_tweets(q=f"filter:images min_faves:1000 #GenshinImpact", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.extended_entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


# ギラティナの画像を送る
@bot.command()
async def giratina(ctx):
    await ctx.channel.send("https://img.gamewith.jp/article/thumbnail/rectangle/36417.png")


# no context hentai imgの画像を送信
@bot.command()
async def hentai(ctx):
    guild = bot.get_guild(SIRONEKO_GUILD_ID)

    channel = guild.get_channel(NO_CONTEXT_HENTAI_IMG_CHANNEL_ID)

    hentai_channel_messages = [message async for message in channel.history(limit=None)]

    random_hentai = random.choice(hentai_channel_messages)

    content = random_hentai.attachments[0].url if random_hentai.content == "" else random_hentai.content

    # メッセージが送られてきたチャンネルに送る
    await ctx.channel.send(content)


# Twitterから#胡桃の1000いいね以上を探して送信
@bot.command(aliases=["kisshutao"])
async def hutao(ctx):
    tweets = twapi.search_tweets(q=f"filter:images min_faves:1000 #胡桃", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.extended_entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


# イキス
@bot.command()
async def inm(ctx):
    await ctx.channel.send(
        "聖バリ「イキスギィイクイク！！！ンアッー！！！マクラがデカすぎる！！！」\n\n"
        f"{ctx.author.name}「聖なるバリア －ミラーフォース－、淫夢はもうやめてよ！淫夢ごっこは恥ずかしいよ！」\n\n"
        f"聖バリ「{ctx.author.name}、おっ大丈夫か大丈夫か〜？？？バッチェ冷えてるぞ〜淫夢が大好きだってはっきりわかんだね」"
    )


# かおすちゃんを送信
@bot.command()
async def kaosu(ctx):
    tweets = twapi.search_tweets(q="from:@kaosu_pic", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


# こまちゃんを送信
@bot.command()
async def komachan(ctx):
    tweets = twapi.search_tweets(q="from:@komachan_pic", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


# らきすたを送信
# https://ja.stackoverflow.com/questions/56894/twitter-api-%e3%81%a7-%e5%8b%95%e7%94%bb%e3%83%84%e3%82%a4%e3%83%bc%e3%83%88-%e3%82%921%e4%bb%b6%e5%8f%96%e5%be%97%e3%81%97%e3%81%a6html%e4%b8%8a%e3%81%a7%e8%a1%a8%e7%a4%ba%e3%81%95%e3%81%9b%e3%81%9f%e3%81%84%e3%81%ae%e3%81%a7%e3%81%99%e3%81%8c-m3u8-%e5%bd%a2%e5%bc%8f%e3%81%a8-mp4-%e5%bd%a2%e5%bc%8f%e3%81%ae%e9%96%a2%e4%bf%82%e6%80%a7%e3%81%af
# https://syncer.jp/Web/API/Twitter/REST_API/Object/Entity/#:~:text=Filter-,%E3%83%84%E3%82%A4%E3%83%BC%E3%83%88%E3%82%AA%E3%83%96%E3%82%B8%E3%82%A7%E3%82%AF%E3%83%88%20(%E5%8B%95%E7%94%BB),-%E5%8B%95%E7%94%BB%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB%E3%82%92
@bot.command()
async def lucky(ctx):
    tweets = twapi.search_tweets(q="from:@LuckyStarPicBot", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)

    # 動画も取得して送信できるようにしたかったけど、うまくいってません
    # for tweet in tweets:
    #     media = tweet.extended_entities["media"]
    #     for m in media:
    #         if m["type"] == "video":
    #             for video_info in m:
    #                 for variants in video_info:
    #                     for url in variants[0]:
    #                         origin = url
    #                         await ctx.channel.send(origin)
    #         else:
    #             origin = m["media_url"]
    #             await ctx.channel.send(origin)


@bot.command()
async def ma(ctx):
    await ctx.channel.send("https://cdn.discordapp.com/attachments/964831309627289620/982691239025598494/long_ver.___feat._0s_screenshot.png")


# マチカネタンホイザの画像を送信
@bot.command(aliases=["matitan", "matikanetanhoiza"])
async def machitan(ctx):
    guild = bot.get_guild(SEIBARI_GUILD_ID)

    channel = guild.get_channel(MACHITAN_CHANNEL_ID)

    machitan_channel_messages = [message async for message in channel.history(limit=None)]

    random_machitan = random.choice(machitan_channel_messages)

    content = random_machitan.attachments[0].url if random_machitan.content == "" else random_machitan.content

    # メッセージが送られてきたチャンネルに送る
    await ctx.channel.send(content)


# マノム
@bot.command(aliases=["mano"])
async def manomu(ctx):
    await ctx.channel.send(
        "家で飼ってるピーちゃんを\n" +
        "　　　　使ったお料理も好きです。\n\n" +
        "　　　　　あ　ら　ま\n\n" +
        "動物性たんぱくパク　たべるルル\n\n" +
        "　　　　＼内臓もっと／\n\n" +
        "頂戴な　　　　　　　　　頂戴な\n" +
        "ねぇ　　　　　　　　　　　ねぇ\n\n" +
        "　　灯織ちゃんもおいでって"
    )


# アニクトから取得したキャラクターをランダムで表示
@bot.command()
async def odai(ctx):
    while 1:
        # 10個のランダムな数を生成
        random_ids = [str(random.randint(1, 41767)) for _ in range(10)]
        # リストの中の要素を結合する
        filter_ids = ",".join(random_ids)
        # エンドポイント
        annict_url = f"https://api.annict.com/v1/characters?access_token={ANNICT_API_KEY}&filter_ids={filter_ids}"
        # リクエスト
        annict_res = requests.get(annict_url)
        # 変数
        annict_characters = annict_res.json()["characters"]
        # シャッフルする
        random.shuffle(annict_characters)
        # お気に入り数が5以上の要素のみ抽出
        annict_characters_favorite_count = list(filter(lambda e: e["favorite_characters_count"] > 4, annict_characters))
        # 要素が0個では無い場合にループを解除
        if len(annict_characters_favorite_count) > 0:
            target_character = annict_characters_favorite_count[0]
            break

    # 共通の要素
    annict_character_name = target_character["name"]
    annict_character_id = target_character["id"]
    annict_character_fan = target_character["favorite_characters_count"]

    # 送信するメッセージの変数の宣言
    annict_character_msg = f"{annict_character_name} - ファン数{annict_character_fan}人\nhttps://annict.com/characters/{annict_character_id}"

    # シリーズの記載がある場合
    if target_character["series"] is not None:
        annict_character_series = target_character["series"]["name"]
        # 送信するメッセージの変数にシリーズを入れたテキストを代入
        annict_character_msg = f"{annict_character_name}({annict_character_series}) - ファン数{annict_character_fan}人\nhttps://annict.com/characters/{annict_character_id}"

    await ctx.channel.send(annict_character_msg)


# ピンポン
@bot.command()
async def ping(ctx):
    latency = bot.latency
    latency_milli = round(latency * 1000)
    await ctx.channel.send(f"Pong!: {latency_milli}ms")


# Raika
@bot.command()
async def raika(ctx):
    txtfile = open("resources/Wonderful_Raika_Tweet.txt", "r", encoding="utf-8")
    word = ",".join(list(map(lambda s: s.rstrip("\n"), random.sample(txtfile.readlines(), 1)))).replace("["", "").replace(""]", "")
    url = [word]
    pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    for url in url:
        if re.match(pattern, url):
            await ctx.channel.send(requests.get(url).url)
        else:
            await ctx.channel.send(word)


# raikaマルコフ
# https://monachanpapa-scripting.com/marukofu-python/ほぼ丸コピですすみません...
@bot.command()
async def mraika(ctx):
    def parse_words(test_data):
        with open("resources/Wonderful_Raika_Tweet.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        t = MeCab.Tagger("-Owakati")
        datas = []
        for line in lines:
            data = t.parse(line).strip()
            datas.append(data)
        datas = [f"__BEGIN__ {data} __END__" for data in datas]
        datas = [data.split() for data in datas]
        return datas

    def create_words_cnt_dic(datas):
        words = []
        for data in datas:
            words.extend(list(ngrams(data, 3)))
        words_cnt_dic = Counter(words)
        return words_cnt_dic

    def create_m_dic(words_cnt_dic):
        m_dic = {}
        for k, v in words_cnt_dic.items():
            two_words, next_word = k[:2], k[2]
            if two_words not in m_dic:
                m_dic[two_words] = {"words": [], "weights": []}
            m_dic[two_words]["words"].append(next_word)
            m_dic[two_words]["weights"].append(v)
        return m_dic

    def create_begin_words_weights(words_cnt_dic):
        begin_words_dic = defaultdict(int)
        for k, v in words_cnt_dic.items():
            if k[0] == "__BEGIN__":
                next_word = k[1]
                begin_words_dic[next_word] = v
        begin_words = [k for k in begin_words_dic.keys()]
        begin_weights = [v for v in begin_words_dic.values()]
        return begin_words, begin_weights

    def create_sentences(m_dic, begin_words, begin_weights):
        begin_word = random.choices(begin_words, weights=begin_weights, k=1)[0]
        sentences = ["__BEGIN__", begin_word]
        while True:
            back_words = tuple(sentences[-2:])
            words, weights = m_dic[back_words]["words"], m_dic[back_words]["weights"]
            next_word = random.choices(words, weights=weights, k=1)[0]
            if next_word == "__END__":
                break
            sentences.append(next_word)
        return "".join(sentences[1:])

    datas = parse_words("osake.txt")
    words_cnt_dic = create_words_cnt_dic(datas)
    m_dic = create_m_dic(words_cnt_dic)
    begin_words, begin_weights = create_begin_words_weights(words_cnt_dic)
    for i in range(1):
        text = create_sentences(m_dic, begin_words, begin_weights)
        await ctx.channel.send(text)


# おしゃべりひろゆきメーカーの実装。リリース半日クオリティーなので許してください
@bot.command()
async def hiroyuki(ctx, *arg):
    if arg:
        text = arg[0]
        embed = discord.Embed(colour=0xff00ff, title=f"{text}を生成中です...")
        hiroyuki_msg: discord.Message = await ctx.channel.send(embed=embed)
        headers = {
            "authority": "tgeedx93af.execute-api.ap-northeast-1.amazonaws.com",
            "accept": "application/json, text/plain, */*"
        }
        json_data = {
            "coefont": "19d55439-312d-4a1d-a27b-28f0f31bedc5",
            "text": f"{text}",
        }
        response = requests.post("https://tgeedx93af.execute-api.ap-northeast-1.amazonaws.com/production/hiroyuki/text2speech", headers=headers, json=json_data)
        status = response.json()["statusCode"]
        if status == 200:
            key = response.json()["body"]["wav_key"]
            headers2 = {
                "authority": "johwruw0ic.execute-api.ap-northeast-1.amazonaws.com",
                "accept": "application/json, text/plain, */*"
            }
            json_data2 = {
                "voice_key": f"{key}",
            }
            response2 = requests.post("https://johwruw0ic.execute-api.ap-northeast-1.amazonaws.com/production/hiroyuki_video", headers=headers2, json=json_data2)
            url = response2.json()["body"]["url"]
            embed = discord.Embed(colour=0x4db56a, title=f"音声の生成に成功しました")
            await hiroyuki_msg.edit(embed=embed)
            response = requests.get(url)
            file = open("temp.mp4", "wb")
            for chunk in response.iter_content(100000):
                file.write(chunk)
            file.close()
            stream = ffmpeg.input("temp.mp4")
            stream = ffmpeg.output(stream, "hiroyuki.mp3")
            ffmpeg.run(stream)
            await ctx.channel.send(file=discord.File("hiroyuki.mp3"))
            embed0 = discord.Embed(colour=0x4db56a, title=f"動画 {gdshortener.ISGDShortener().shorten(url=url)[0]}")
            hiroyuki0_msg: discord.Message = await ctx.channel.send(embed=embed0)
            os.remove("temp.mp4")
            os.remove("hiroyuki.mp3")
            return
        else:
            embed = discord.Embed(colour=0xff0000, title="生成に失敗しました")
            await hiroyuki_msg.edit(embed=embed)
            return
    if not arg:
        embed = discord.Embed(colour=0xff0000, title=f"文字を入力してください")
        hiroyuki_msg: discord.Message = await ctx.channel.send(embed=embed)


# hiroyuki talk
@bot.command()
async def htalk(ctx, *arg):
    if arg:
        text = arg[0]
        embed = discord.Embed(colour=0xff00ff, title=f"{text}を生成中です...")
        hiroyuki_msg: discord.Message = await ctx.channel.send(embed=embed)
        headers = {
            "authority": "tgeedx93af.execute-api.ap-northeast-1.amazonaws.com",
            "accept": "application/json, text/plain, */*"
        }
        json_data = {
            "coefont": "19d55439-312d-4a1d-a27b-28f0f31bedc5",
            "text": f"{text}",
        }
        response = requests.post("https://tgeedx93af.execute-api.ap-northeast-1.amazonaws.com/production/hiroyuki/text2speech", headers=headers, json=json_data)
        status = response.json()["statusCode"]
        if status == 200:
            embed = discord.Embed(colour=0x4db56a, title=f"音声の生成に成功しました")
            await hiroyuki_msg.edit(embed=embed)
            key = response.json()["body"]["wav_key"]
            headers2 = {
                "authority": "johwruw0ic.execute-api.ap-northeast-1.amazonaws.com",
                "accept": "application/json, text/plain, */*"
            }
            json_data2 = {
                "voice_key": f"{key}",
            }
            response2 = requests.post("https://johwruw0ic.execute-api.ap-northeast-1.amazonaws.com/production/hiroyuki_video", headers=headers2, json=json_data2)
            url = response2.json()["body"]["url"]
            embed = discord.Embed(colour=0x4db56a, title=f"動画の生成に成功しました")
            await hiroyuki_msg.edit(embed=embed)
            response = requests.get(url)
            file = open("temp.mp4", "wb")
            for chunk in response.iter_content(100000):
                file.write(chunk)
            file.close()
            stream = ffmpeg.input("temp.mp4")
            stream = ffmpeg.output(stream, "temp.mp3")
            ffmpeg.run(stream)
            if ctx.author.voice is None:
                await ctx.channel.send("なんだろう")
                return
            # ボイスチャンネルに接続する
            if ctx.guild.voice_client is None:
                await ctx.author.voice.channel.connect()
            # 音声を再生する
            ctx.guild.voice_client.play(discord.FFmpegPCMAudio("temp.mp3"))
            # 音声が再生中か確認する
            while ctx.guild.voice_client.is_playing():
                await asyncio.sleep(1)
            # 切断する
            await ctx.guild.voice_client.disconnect()
            os.remove("temp.mp4")
            os.remove("temp.mp3")
            return
        else:
            embed = discord.Embed(colour=0xff0000, title="生成に失敗しました")
            await hiroyuki_msg.edit(embed=embed)
            return
    if not arg:
        embed = discord.Embed(colour=0xff0000, title=f"文字を入力してください")
        hiroyuki_msg: discord.Message = await ctx.channel.send(embed=embed)


# mp4
@bot.command()
async def mp4(ctx):
    if ctx.message.reference is None:
        await ctx.reply("動画にしたい音声に返信してください", mention_author=False)
        return

    mes = await ctx.channel.fetch_message(ctx.message.reference.message_id)

    if mes.attachments is None:
        await ctx.reply("返信元のメッセージにファイルが添付されていません", mention_author=False)
        return

    await mes.attachments[0].save("resources/temporary/wip_input.mp3")
    mes_pros = await ctx.reply("処理中です…", mention_author=False)
    command = "ffmpeg -y -loop 1 -i resources/wip_input.jpg -i resources/temporary/wip_input.mp3 -vcodec libx264 -vb 50k -acodec aac -strict experimental -ab 128k -ac 2 -ar 48000 -pix_fmt yuv420p -shortest resources/temporary/wip_output.mp4"
    proc = await asyncio.create_subprocess_exec(*command.split(" "), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    await mes_pros.delete()
    await ctx.channel.send(file=discord.File("resources/temporary/wip_output.mp4"))
    os.remove("resources/temporary/wip_input.mp3")
    os.remove("resources/temporary/wip_output.mp4")

        
        
# 背景を除去(RemoveBG)
@bot.command()
async def removebg(ctx):
    removebg_apikey = os.getenv("REMOVEBG_APIKEY")

    filename_input = f"resources/temporary/temp_input_{ctx.channel.id}.png"
    filename_output = f"resources/temporary/temp_output_{ctx.channel.id}.png"

    if not await modules.funcs.attachments_proc(ctx, filename_input, "image"):
        return

    async with ctx.typing():
        #RemoveBgAPI
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": open(filename_input, "rb")},
            data={"size": "auto"},
            headers={"X-Api-Key": removebg_apikey},
        )

        if response.status_code == requests.codes.ok:
            with open(filename_output, "wb") as out:
                out.write(response.content)
                await ctx.send(file=discord.File(filename_output))
                for filename in [filename_input, filename_output]:
                    if os.path.isfile(filename):
                        os.remove(filename)
        else:
            await ctx.send(f"```Error:{response.status_code} {response.text}```")


# サターニャを送信
@bot.command()
async def satanya(ctx):
    tweets = twapi.search_tweets(q="from:@satanya_gazobot", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


# おすしを送信
@bot.command(aliases=["osushi"])
async def sushi(ctx):
    tweets = twapi.search_tweets(q="from:@kasakioiba", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


# ファルコおもしろ画像を送信
@bot.command(aliases=["teiou", "teio", "teio-"])
async def toukaiteiou(ctx):
    guild = bot.get_guild(SEIBARI_GUILD_ID)

    channel = guild.get_channel(TEIOU_CHANNEL_ID)

    teiou_channel_messages = [message async for message in channel.history(limit=None)]

    random_teiou = random.choice(teiou_channel_messages)

    content = random_teiou.attachments[0].url if random_teiou.content == "" else random_teiou.content

    # メッセージが送られてきたチャンネルに送る
    await ctx.channel.send(content)


# https://zenn.dev/zakiii/articles/7ada80144c9db0
# https://qiita.com/soma_sekimoto/items/65c664f00573284b0b74
# TwitterのIDを指定して最新の画像を送信
@bot.command(aliases=["tw"])
async def twitter(ctx, *, arg):
    tweets = twapi.search_tweets(q=f"filter:images {arg}", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.extended_entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


@bot.command(aliases=["twdl"])
async def twitterdl(ctx, *, arg):
    tweet_url = f"{arg}"
    # URLからツイートIDを取得する正規表現
    # https://stackoverflow.com/questions/45282238/getting-a-tweet-id-from-a-tweet-link-using-tweepy
    tweet_id = tweet_url.split("/")[-1].split("?")[0]
    is_twitter = tweet_url.startswith("https://twitter.com")

    if is_twitter:
        tweet_status = twapi.get_status(id=int(tweet_id), tweet_mode="extended", include_entities=True)

        status = tweet_status
        for media in status.extended_entities.get("media", [{}]):
            if media.get("type", None) == "video":
                video = media["video_info"]["variants"]
                sorted_video = sorted(
                    video,
                    key=lambda x: x.get("bitrate", 0),  # bitrateの値がない場合にエラーが出るので0を代入して大きい順にソートする
                    reverse=True  # 降順にする
                )
                video_url = sorted_video[0]["url"]
        await ctx.channel.send(video_url)


    else:
        embed = discord.Embed(colour=0xff00ff, title="TwitterのURLを貼ってください")
        discord.Message = await ctx.channel.send(embed=embed)


# ウマ娘ガチャシミュレーター
@bot.command()
async def uma(ctx, *args):
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

    
# ゆるゆりを送信
@bot.command()
async def yuruyuri(ctx):
    tweets = twapi.search_tweets(q="from:@YuruYuriBot1", tweet_mode="extended", include_entities=True, count=1)
    for tweet in tweets:
        media = tweet.entities["media"]
        for m in media:
            origin = m["media_url"]
            await ctx.channel.send(origin)


bot.add_cog(Music(bot_arg=bot))
bot.add_cog(Kotobagari(bot=bot))
bot.run(DISCORD_BOT_TOKEN)
