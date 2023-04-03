import asyncio
import random
import re
import typing
from collections import defaultdict

import discord
import requests
import yt_dlp
from discord.ext import commands
from googleapiclient.errors import HttpError
from niconico import NicoNico
from spotdl import Spotdl

from constants import PASOJIN_GUILD_ID, OTOMAD_CHANNEL_ID

# コマンドを送ったユーザーがボイスチャンネルに居ない場合
EMBED_USER_NOT_JOIN = discord.Embed(
    colour=0xFF0000,
    title="エラーが発生しました",
    description="操作する前にボイスチャンネルに接続してください",
)

# Botがボイスチャンネルに居ない場合
EMBED_BOT_NOT_JOIN = discord.Embed(
    colour=0xFF0000, title="エラーが発生しました", description="Botがボイスチャンネルに接続していません"
)

# 再生中ではない場合
EMBED_NOT_PLAYING = discord.Embed(
    colour=0xFF0000, title="エラーが発生しました", description="再生していません"
)

# yt_dlp
YTDL_FORMAT_OPTIONS = {
    "format": "bestaudio/best*[acodec=aac]",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

# before_optionsではなくoptionsで指定されてました。修正。様子見でお願いします。
# https://stackoverflow.com/questions/58892635/discord-py-and-youtube-dl-read-error-and-the-session-has-been-invalidated-fo
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_at_eof 1 -reconnect_delay_max 5",
    "options": "-vn",
}

# https://qiita.com/sizumita/items/cafd00fe3e114d834ce3
# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda: ""
ytdl = yt_dlp.YoutubeDL(YTDL_FORMAT_OPTIONS)


class NicoNicoDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, url, original_url, video, volume=0.5):
        super().__init__(source, volume)

        self.url = url
        self.original_url = original_url
        self.video = video
        self.title = video.video.title

    # 再生成する。生成後、このインスタンスは使用不可となる。
    # 経緯は以下のissueを参照。
    # see also: https://github.com/Giratina-net/Giratina/issues/161
    def regenerate(self):
        self.close_connection()

        niconico_client = NicoNico()
        video = niconico_client.video.get_video(self.original_url)
        # 必ずあとでコネクションを切る
        video.connect()

        data = ytdl.extract_info(self.original_url, download=False)

        filename = data["url"]

        source = discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS)
        return self.__class__(source, data=data)

    @classmethod
    async def from_url(cls, url):
        # とりあえず毎回clientを作っておく
        niconico_client = NicoNico()
        video = niconico_client.video.get_video(url)
        # 必ずあとでコネクションを切る
        video.connect()

        source = discord.FFmpegPCMAudio(video.download_link, **FFMPEG_OPTIONS)
        return cls(source, video.download_link, url, video)

    def close_connection(self):
        self.video.close()


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data
        self.id = data.get("id")
        self.original_url = data.get("original_url")
        self.title = data.get("title")
        self.url = data.get("url")

    # 再生成する。生成後、このインスタンスは使用不可となる。
    # 経緯は以下のissueを参照。
    # see also: https://github.com/Giratina-net/Giratina/issues/161
    def regenerate(self):
        data = ytdl.extract_info(self.original_url, download=False)

        filename = data["url"]

        source = discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS)
        return self.__class__(source, data=data)

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )

        # もしプレイリストだった場合
        if "entries" in data:
            # プレイリストの1曲目をとる
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)

        source = discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS)
        return cls(source, data=data)


# Cog とは: コマンドとかの機能をひとまとめにできる
class Music(commands.Cog):
    def __init__(self, bot, youtube, spotdl):
        self.bot = bot
        self.loop: bool = False
        self.player: typing.Union[YTDLSource, NicoNicoDLSource, None] = None
        self.queue: defaultdict[
            typing.List[typing.Union[YTDLSource, NicoNicoDLSource]]
        ] = defaultdict(lambda: [])

        self.youtube = youtube
        self.spotdl: Spotdl = spotdl

    # coroutineの再帰で実装しようとすると結構複雑になるので一旦あきらめてる
    # 再帰でプレイヤーを実現するんじゃなくて、別のクラスを実装したほうがよさそう
    # いい感じの参考 https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34
    def after_play(self, guild, err):
        if type(self.player) == NicoNicoDLSource:
            self.player.close_connection()

        if err:
            return print(f"has error: {err}")

        if len(self.queue[guild.id]) <= 0:
            return

        self.player = self.queue[guild.id].pop(0).regenerate()

        guild.voice_client.play(self.player, after=lambda e: self.after_play(guild, e))

    @commands.command()
    async def join(self, ctx):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            return await ctx.channel.send(embed=EMBED_USER_NOT_JOIN)

        # ボイスチャンネルに接続する
        await ctx.author.voice.channel.connect()

        embed = discord.Embed(colour=0xFF00FF, title="接続しました")
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def leave(self, ctx):
        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            return await ctx.channel.send(embed=EMBED_BOT_NOT_JOIN)

        # 切断する
        await ctx.guild.voice_client.disconnect()

        embed = discord.Embed(colour=0xFF00FF, title="切断しました")
        await ctx.channel.send(embed=embed)

    # @commands.command(aliases=["l"])
    # async def loop(self, ctx):
    #     # コマンドを送ったユーザーがボイスチャンネルに居ない場合
    #     if ctx.author.voice is None:
    #         return await ctx.channel.send(embed=EMBED_USER_NOT_JOIN)
    #
    #     # Botがボイスチャンネルに居ない場合
    #     if ctx.guild.voice_client is None:
    #         return await ctx.channel.send(embed=EMBED_BOT_NOT_JOIN)
    #
    #     self.loop = not self.loop
    #
    #     embed = discord.Embed(colour=0xFF00FF, title=f"ループを {"`有効`" if self.loop else "`無効`"} にしました")
    #     await ctx.channel.send(embed=embed)

    @commands.command(aliases=["np"])
    async def nowplaying(self, ctx):
        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            return await ctx.channel.send(embed=EMBED_BOT_NOT_JOIN)

        embed = discord.Embed(
            colour=0xFF00FF,
            title="現在再生中",
            description=f"[{self.player.title}]({self.player.original_url})"
            if ctx.guild.voice_client.is_playing()
            else "再生していません",
        )

        embed.set_footer(text=f"残りキュー: {len(self.queue[ctx.guild.id])}")

        # サムネイルをAPIで取得
        if ctx.guild.voice_client.is_playing() and (
            "youtube.com" in self.player.original_url
            or "youtu.be" in self.player.original_url
        ):
            np_youtube_video = (
                self.youtube.videos().list(part="snippet", id=self.player.id).execute()
            )
            np_thumbnail = np_youtube_video["items"][0]["snippet"]["thumbnails"]
            np_highres_thumbnail = list(np_thumbnail.keys())[-1]
            embed.set_thumbnail(url=np_thumbnail[np_highres_thumbnail]["url"])

        await ctx.channel.send(embed=embed)

    async def url_to_source(self, url) -> typing.Union[NicoNicoDLSource, YTDLSource]:
        if url.startswith("https://www.nicovideo.jp/watch/") or url.startswith(
            "https://nico.ms/"
        ):
            return await NicoNicoDLSource.from_url(url)
        else:
            return await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)

    async def queue_urls(self, ctx, urls: typing.List[str], play_msg):
        first_source = None
        while True:
            try:
                first_source = await self.url_to_source(urls.pop(0))
                print(first_source)
                break
            except IndexError:
                embed = discord.Embed(
                    colour=0xFF0000,
                    title="エラーが発生しました",
                    description="指定したURLが見つかりませんでした",
                )
                return await play_msg.edit(embed=embed)
            except Exception as e:
                print(e)
                continue

        # キューへの追加
        if ctx.guild.voice_client.is_playing():  # 他の曲を再生中の場合
            # self.playerに追加すると再生中の曲と衝突する
            self.queue[ctx.guild.id].append(first_source)

            embed = discord.Embed(
                colour=0xFF00FF,
                title="キューに追加しました",
                description=f"[{first_source.title}]({first_source.original_url})",
            )

            embed.set_footer(text=f"残りキュー: {len(self.queue[ctx.guild.id])}")

            await play_msg.edit(embed=embed)

        else:  # 他の曲を再生していない場合
            # self.playerにURLを追加し再生する
            self.player = first_source

            ctx.guild.voice_client.play(
                self.player, after=lambda e: self.after_play(ctx.guild, e)
            )

            embed = discord.Embed(
                colour=0xFF00FF,
                title="再生を開始します",
                description=f"[{first_source.title}]({first_source.original_url})",
            )

            if type(first_source) == YTDLSource and (
                "youtube.com" in first_source.original_url
                or "youtu.be" in first_source.original_url
            ):
                # サムネイルをAPIで取得
                try:
                    np_youtube_video = (
                        self.youtube.videos()
                        .list(part="snippet", id=first_source.id)
                        .execute()
                    )
                    if np_youtube_video["items"]:
                        np_thumbnail = np_youtube_video["items"][0]["snippet"][
                            "thumbnails"
                        ]
                        np_highres_thumbnail = list(np_thumbnail.keys())[-1]
                        embed.set_thumbnail(
                            url=np_thumbnail[np_highres_thumbnail]["url"]
                        )
                # APIキーの有効期限が切れてるとここに来る
                except HttpError:
                    pass

            await play_msg.edit(embed=embed)

        for url in urls:
            try:
                self.queue[ctx.guild.id].append(await self.url_to_source(url))
            except Exception as e:
                print(e)

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, url):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            await ctx.channel.send(embed=EMBED_USER_NOT_JOIN)

        # ボイスチャンネルにBotが未接続の場合はボイスチャンネルに接続する
        if ctx.guild.voice_client is None:
            await ctx.author.voice.channel.connect()

        embed = discord.Embed(colour=0xFF00FF, title="処理中です...")
        play_msg: discord.Message = await ctx.channel.send(embed=embed)

        # niconico.py は短縮URLも取り扱えるっぽいので信じてみる
        # https://github.com/tasuren/niconico.py/blob/b4d9fcb1d0b80e83f2d8635dd85987d1fa2d84fc/niconico/video.py#L367
        is_niconico_mylist = (
            url.startswith("https://www.nicovideo.jp/mylist")
            or url.startswith("https://nico.ms/mylist")
            or re.match(r"https://www.nicovideo.jp/user/\d+/mylist", url)
        )
        is_niconico = url.startswith("https://www.nicovideo.jp/") or url.startswith(
            "https://nico.ms/"
        )
        is_spotify = url.startswith("https://open.spotify.com/")

        target_urls: typing.List[str] = []

        # 各サービスごとに振り分け
        if is_niconico_mylist:
            niconico_client = NicoNico()
            items = []

            # 100件ごとに分割されているので全て取得してひとつのリストにまとめる
            for mylist_page in niconico_client.video.get_mylist(url):
                items.extend(mylist_page.items)

            target_urls = [item.video.url for item in items]

        elif is_niconico:
            target_urls = [url]

        elif is_spotify:
            # プレイリストの場合はsongsの結果が複数返ってくる
            # その場合は2曲目以降も存在する
            songs = self.spotdl.search([url])
            urls = self.spotdl.get_download_urls(songs)
            target_urls = urls

        else:
            try:
                data = await self.bot.loop.run_in_executor(
                    None, lambda: ytdl.extract_info(url, download=False, process=False)
                )
            except Exception as e:
                embed = discord.Embed(
                    colour=0xFF0000,
                    title="エラーが発生しました",
                    description="指定したURLが見つかりませんでした",
                )
                return await play_msg.edit(embed=embed)

            # もしプレイリストだった場合
            if "entries" in data:
                for item in data["entries"]:
                    original_url = item.get("url") or item.get("original_url")
                    target_urls.append(original_url)
            else:
                original_url = data.get("url") or data.get("original_url")
                target_urls.append(original_url)

        await self.queue_urls(ctx, target_urls, play_msg)

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        embed = discord.Embed(colour=0xFF00FF, title="キュー")

        if not ctx.guild.voice_client.is_playing():
            embed.description = "再生していません"

        else:
            queue_embed = [
                f"__現在再生中__:\n[{self.player.title}]({self.player.original_url})"
            ]

            for i in range(min(len(self.queue[ctx.guild.id]), 10)):
                queue_embed.append(
                    ("__次に再生__:\n" if i == 0 else "")
                    + f"`{i + 1}.` [{self.queue[ctx.guild.id][i].title}]({self.queue[ctx.guild.id][i].original_url})"
                )

            embed.description = "\n\n".join(queue_embed)

        embed.set_footer(text=f"残りキュー: {len(self.queue[ctx.guild.id])}")

        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["s"])
    async def skip(self, ctx):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            return await ctx.channel.send(embed=EMBED_USER_NOT_JOIN)

        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            return await ctx.channel.send(embed=EMBED_BOT_NOT_JOIN)

        # 再生中ではない場合は実行しない
        if not ctx.guild.voice_client.is_playing():
            return await ctx.channel.send(embed=EMBED_NOT_PLAYING)

        ctx.guild.voice_client.stop()
        embed = discord.Embed(colour=0xFF00FF, title="スキップします")
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def shuffle(self, ctx):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            return await ctx.channel.send(embed=EMBED_USER_NOT_JOIN)

        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            return await ctx.channel.send(embed=EMBED_BOT_NOT_JOIN)

        # 再生中ではない場合は実行しない
        if not ctx.guild.voice_client.is_playing():
            return await ctx.channel.send(embed=EMBED_NOT_PLAYING)

        random.shuffle(self.queue[ctx.guild.id])

        embed = discord.Embed(colour=0xFF00FF, title="キューをシャッフルしました")
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def stop(self, ctx):
        # コマンドを送ったユーザーがボイスチャンネルに居ない場合
        if ctx.author.voice is None:
            return await ctx.channel.send(embed=EMBED_USER_NOT_JOIN)

        # Botがボイスチャンネルに居ない場合
        if ctx.guild.voice_client is None:
            return await ctx.channel.send(embed=EMBED_BOT_NOT_JOIN)

        # 再生中ではない場合は実行しない
        if not ctx.guild.voice_client.is_playing():
            return await ctx.channel.send(embed=EMBED_NOT_PLAYING)

        self.queue[ctx.guild.id].clear()
        ctx.guild.voice_client.stop()

        embed = discord.Embed(colour=0xFF00FF, title="再生を停止します")
        await ctx.channel.send(embed=embed)

    @commands.command(aliases=["mad"])
    async def otomad(self, ctx):
        guild = self.bot.get_guild(PASOJIN_GUILD_ID)

        channel = guild.get_channel(OTOMAD_CHANNEL_ID)

        otomad_channel_messages = [
            message async for message in channel.history(limit=None)
        ]

        message_contents = []

        for otomad_channel_message in otomad_channel_messages:
            message_content = otomad_channel_message.content
            message_contents.append(message_content)

        # ここチャットGPTに正規表現してもらった
        # URLと一緒に投稿されたコメントを除外して純粋なURLだけにするために、改行文字以降のテキストを除外するように頼みました
        pattern = r"(?P<url>https?://[^\n\s]+)"
        otomad_urls = []

        for message_content in message_contents:
            match = re.search(pattern, message_content)
            if match:
                otomad_urls.append(match.group("url"))

        random_otomad = random.choice(otomad_urls)

        # メッセージが送られてきたチャンネルに送る
        await ctx.channel.send(random_otomad)
