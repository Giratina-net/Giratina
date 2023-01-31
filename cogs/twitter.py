import discord
from discord.ext import commands
import random

class Twitter(commands.Cog):
    def __init__(self, bot, twapi):
        self.bot = bot
        self.twapi = twapi

    # ファミ通
    @commands.command(aliases=["fami", "famitu", "fami2"])
    async def famitsu(self, ctx):
        texts = []
        tweets = self.twapi.search_tweets(q="from:@fami2repo_bot", count=10)
        for tweet in tweets:
            text = tweet.text
            texts.append(text)
        text_pickup = random.choice(texts)
        await ctx.channel.send(text_pickup)

    # Twitterから#GenshinImpactの1000いいね以上を探して送信
    @commands.command(aliases=["gennshinn", "gensin", "gennsinn", "gs"])
    async def genshin(self, ctx):
        tweets = self.twapi.search_tweets(q=f"filter:images min_faves:1000 #GenshinImpact", tweet_mode="extended", include_entities=True, count=1)
        for tweet in tweets:
            media = tweet.extended_entities["media"]
            for m in media:
                origin = m["media_url"]
                await ctx.channel.send(origin)

    # Twitterから#胡桃の1000いいね以上を探して送信
    @commands.command(aliases=["kisshutao"])
    async def hutao(self, ctx):
        tweets = self.twapi.search_tweets(q=f"filter:images min_faves:1000 #胡桃", tweet_mode="extended", include_entities=True, count=1)
        for tweet in tweets:
            media = tweet.extended_entities["media"]
            for m in media:
                origin = m["media_url"]
                await ctx.channel.send(origin)

    # かおすちゃんを送信
    @commands.command()
    async def kaosu(self, ctx):
        tweets = self.twapi.search_tweets(q="from:@kaosu_pic", tweet_mode="extended", include_entities=True, count=1)
        for tweet in tweets:
            media = tweet.entities["media"]
            for m in media:
                origin = m["media_url"]
                await ctx.channel.send(origin)

    # こまちゃんを送信
    @commands.command()
    async def komachan(self, ctx):
        tweets = self.twapi.search_tweets(q="from:@komachan_pic", tweet_mode="extended", include_entities=True, count=1)
        for tweet in tweets:
            media = tweet.entities["media"]
            for m in media:
                origin = m["media_url"]
                await ctx.channel.send(origin)

    # らきすたを送信
    # https://ja.stackoverflow.com/questions/56894/twitter-api-%e3%81%a7-%e5%8b%95%e7%94%bb%e3%83%84%e3%82%a4%e3%83%bc%e3%83%88-%e3%82%921%e4%bb%b6%e5%8f%96%e5%be%97%e3%81%97%e3%81%a6html%e4%b8%8a%e3%81%a7%e8%a1%a8%e7%a4%ba%e3%81%95%e3%81%9b%e3%81%9f%e3%81%84%e3%81%ae%e3%81%a7%e3%81%99%e3%81%8c-m3u8-%e5%bd%a2%e5%bc%8f%e3%81%a8-mp4-%e5%bd%a2%e5%bc%8f%e3%81%ae%e9%96%a2%e4%bf%82%e6%80%a7%e3%81%af
    # https://syncer.jp/Web/API/Twitter/REST_API/Object/Entity/#:~:text=Filter-,%E3%83%84%E3%82%A4%E3%83%BC%E3%83%88%E3%82%AA%E3%83%96%E3%82%B8%E3%82%A7%E3%82%AF%E3%83%88%20(%E5%8B%95%E7%94%BB),-%E5%8B%95%E7%94%BB%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB%E3%82%92
    @commands.command()
    async def lucky(self, ctx):
        tweets = self.twapi.search_tweets(q="from:@LuckyStarPicBot", tweet_mode="extended", include_entities=True, count=1)
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

    # サターニャを送信
    @commands.command()
    async def satanya(self, ctx):
        tweets = self.twapi.search_tweets(q="from:@satanya_gazobot", tweet_mode="extended", include_entities=True, count=1)
        for tweet in tweets:
            media = tweet.entities["media"]
            for m in media:
                origin = m["media_url"]
                await ctx.channel.send(origin)

    # おすしを送信
    @commands.command(aliases=["osushi"])
    async def sushi(self, ctx):
        tweets = self.twapi.search_tweets(q="from:@kasakioiba", tweet_mode="extended", include_entities=True, count=1)
        for tweet in tweets:
            media = tweet.entities["media"]
            for m in media:
                origin = m["media_url"]
                await ctx.channel.send(origin)

    # https://zenn.dev/zakiii/articles/7ada80144c9db0
    # https://qiita.com/soma_sekimoto/items/65c664f00573284b0b74
    # TwitterのIDを指定して最新の画像を送信
    @commands.command(aliases=["tw"])
    async def twitter(self, ctx, *, arg):
        tweets = self.twapi.search_tweets(q=f"filter:images {arg}", tweet_mode="extended", include_entities=True, count=1)
        for tweet in tweets:
            media = tweet.extended_entities["media"]
            for m in media:
                origin = m["media_url"]
                await ctx.channel.send(origin)

    # ゆるゆりを送信
    @commands.command()
    async def yuruyuri(self, ctx):
        tweets = self.twapi.search_tweets(q="from:@YuruYuriBot1", tweet_mode="extended", include_entities=True, count=1)
        for tweet in tweets:
            media = tweet.entities["media"]
            for m in media:
                origin = m["media_url"]
                await ctx.channel.send(origin)

    @commands.command(aliases=["twdl"])
    async def twitterdl(self, ctx, *, arg):
        tweet_url = f"{arg}"
        # URLからツイートIDを取得する正規表現
        # https://stackoverflow.com/questions/45282238/getting-a-tweet-id-from-a-tweet-link-using-tweepy
        tweet_id = tweet_url.split("/")[-1].split("?")[0]
        is_twitter = tweet_url.startswith("https://twitter.com")

        if is_twitter:
            tweet_status = self.twapi.get_status(id=int(tweet_id), tweet_mode="extended", include_entities=True)

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

