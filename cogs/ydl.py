import time
import datetime
import discord
import requests
from os import getenv
from zoneinfo import ZoneInfo
from discord.ext import commands


G2YDL_API_KEY = getenv("G2YDL_API_KEY")
G2YDL_HOST = getenv("G2YDL_HOST")+"/v1/ydl"
timeout = 300

#タスク作成
def task_create(url, request_type):
    headers = {'X-API-KEY': G2YDL_API_KEY}
    if request_type not in ["mp4", "mp3", "mp3_album"]:
        return False
    try:
        params = {'url': url, 'type': request_type}
        response = requests.get(G2YDL_HOST + "/create", headers=headers, params=params)
        return response.json()
    except Exception as e:
        return False
#タスクのステータスを取得
def task_status(task_id):
    headers = {'X-API-KEY': G2YDL_API_KEY}
    try:
        params = {'task_id': task_id}
        response = requests.get(G2YDL_HOST + "/status", headers=headers, params=params)
        return response.json()
    except Exception as e:
        return False

async def download(ctx, url, request_type):
    #msgの定義
    msg:  discord.Message = await ctx.channel.send(embed=discord.Embed(colour=0xEE7800, title=f"データの取得中です"))
    #値の初期化
    title_flag = False
    error_count = 0
    #タスクの作成
    task_info = task_create(url, request_type)
    #タスクの作成に失敗した場合
    if task_info is False:
        await msg.edit(embed=discord.Embed(colour=0xFF0000, title=f"サーバーエラー"))
        return False
    #タスクの作成に成功した場合
    task_id = task_info.get("task_id")
    #"""""この下のコードを消すと動かない"""""
    time.sleep(3)
    
    while True:
        #タスクのステータスを取得
        d = task_status(task_id)
        #3回までのエラーを許容
        if d is False:
            error_count += 1
            if error_count > 3:
                await msg.edit(embed=discord.Embed(colour=0xFF0000, title=f"サーバーエラー"))
                return False
            else:
                continue
        #タイトルを取得してたらタイトルを表示
        if d["media"]["title"] and not title_flag:
            await msg.edit(embed=discord.Embed(colour=0xFFF100, title=f"[{task_id}] {d['media']['title']}のダウンロードを開始しました"))
            title_flag = True
        #request_timeが現在時刻からtimeout秒以上経過していたらタイムアウト
        current_time = datetime.datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
        diff = (datetime.datetime.fromisoformat(current_time) - datetime.datetime.fromisoformat(d["request_time"])).seconds
        if diff > timeout:
            await msg.edit(embed=discord.Embed(colour=0xFF0000, title=f"タイムアウトしました"))
            return False
        #statusがsuccessならURLを表示
        if d["status"] == "success":
            await msg.edit(embed=discord.Embed(colour=0x0FF000, title=f"[{task_id}] {d['media']['title']}のダウンロードが完了しました\n{d['download_url']['short']}"))
            return True
        #statusがerrorならmessageを表示
        elif d["status"] == "error":
            await msg.edit(embed=discord.Embed(colour=0xFF0000, title=f"[{task_id}] ダウンロードエラー {d['message']}"))
            return False
        
        time.sleep(1)

class Ydl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ydl(self, ctx, url):
        await download(ctx,url,"mp4")        

    @commands.command()
    async def ydl3(self, ctx, url):
        await download(ctx,url,"mp3")
        
    @commands.command()
    async def ydla(self, ctx, url):
        await download(ctx,url,"mp3_album")
