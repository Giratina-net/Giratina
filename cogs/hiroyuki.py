import asyncio
import os

import discord
import ffmpeg
import requests
from discord.ext import commands
import requests
from os import getenv
#envから取得
KUTT_HOST = str(getenv("KUTT_HOST"))+"/api/v2/links"
KUTT_API_KEY = getenv("KUTT_API_KEY")


class Hiroyuki(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # おしゃべりひろゆきメーカーの実装。リリース半日クオリティーなので許してください
    @commands.command()
    async def hiroyuki(self, ctx, *arg):
        if arg:
            text = arg[0]
            embed = discord.Embed(colour=0xFF00FF, title=f"{text}を生成中です...")
            hiroyuki_msg: discord.Message = await ctx.channel.send(embed=embed)
            headers = {
                "authority": "tgeedx93af.execute-api.ap-northeast-1.amazonaws.com",
                "accept": "application/json, text/plain, */*",
            }
            json_data = {
                "coefont": "19d55439-312d-4a1d-a27b-28f0f31bedc5",
                "text": f"{text}",
            }
            response = requests.post(
                "https://tgeedx93af.execute-api.ap-northeast-1.amazonaws.com/production/hiroyuki/text2speech",
                headers=headers,
                json=json_data,
            )
            status = response.json()["statusCode"]
            if status == 200:
                key = response.json()["body"]["wav_key"]
                headers2 = {
                    "authority": "johwruw0ic.execute-api.ap-northeast-1.amazonaws.com",
                    "accept": "application/json, text/plain, */*",
                }
                json_data2 = {
                    "voice_key": f"{key}",
                }
                response2 = requests.post(
                    "https://johwruw0ic.execute-api.ap-northeast-1.amazonaws.com/production/hiroyuki_video",
                    headers=headers2,
                    json=json_data2,
                )
                url = response2.json()["body"]["url"]
                embed = discord.Embed(colour=0x4DB56A, title=f"音声の生成に成功しました")
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
                try:
                    r = requests.post(KUTT_HOST, data={"target": url}, headers={'X-API-KEY': KUTT_API_KEY}).json()
                    url=r['link']
                except:
                    pass
                embed0 = discord.Embed(
                    colour=0x4DB56A,
                    title=f"動画 {url}",
                )
                hiroyuki0_msg: discord.Message = await ctx.channel.send(embed=embed0)
                os.remove("temp.mp4")
                os.remove("hiroyuki.mp3")
                return
            else:
                embed = discord.Embed(colour=0xFF0000, title="生成に失敗しました")
                await hiroyuki_msg.edit(embed=embed)
                return
        if not arg:
            embed = discord.Embed(colour=0xFF0000, title=f"文字を入力してください")
            hiroyuki_msg: discord.Message = await ctx.channel.send(embed=embed)

    # hiroyuki talk
    @commands.command()
    async def htalk(self, ctx, *arg):
        if arg:
            text = arg[0]
            embed = discord.Embed(colour=0xFF00FF, title=f"{text}を生成中です...")
            hiroyuki_msg: discord.Message = await ctx.channel.send(embed=embed)
            headers = {
                "authority": "tgeedx93af.execute-api.ap-northeast-1.amazonaws.com",
                "accept": "application/json, text/plain, */*",
            }
            json_data = {
                "coefont": "19d55439-312d-4a1d-a27b-28f0f31bedc5",
                "text": f"{text}",
            }
            response = requests.post(
                "https://tgeedx93af.execute-api.ap-northeast-1.amazonaws.com/production/hiroyuki/text2speech",
                headers=headers,
                json=json_data,
            )
            status = response.json()["statusCode"]
            if status == 200:
                embed = discord.Embed(colour=0x4DB56A, title=f"音声の生成に成功しました")
                await hiroyuki_msg.edit(embed=embed)
                key = response.json()["body"]["wav_key"]
                headers2 = {
                    "authority": "johwruw0ic.execute-api.ap-northeast-1.amazonaws.com",
                    "accept": "application/json, text/plain, */*",
                }
                json_data2 = {
                    "voice_key": f"{key}",
                }
                response2 = requests.post(
                    "https://johwruw0ic.execute-api.ap-northeast-1.amazonaws.com/production/hiroyuki_video",
                    headers=headers2,
                    json=json_data2,
                )
                url = response2.json()["body"]["url"]
                embed = discord.Embed(colour=0x4DB56A, title=f"動画の生成に成功しました")
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
                embed = discord.Embed(colour=0xFF0000, title="生成に失敗しました")
                await hiroyuki_msg.edit(embed=embed)
                return
        if not arg:
            embed = discord.Embed(colour=0xFF0000, title=f"文字を入力してください")
            hiroyuki_msg: discord.Message = await ctx.channel.send(embed=embed)
