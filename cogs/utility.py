import asyncio
import os

import discord
import requests
from discord.ext import commands

import modules.funcs

#権限がない場合？
EMBED_FORBIDDEN = discord.Embed(
    title = "エラーが発生しました",
    color = 0xFF000,
    description = "権限がありません"
)
#◆◇ニックネーム長すぎ注意◇◆
EMBED_CHARACTER_LIMIT = discord.Embed(
    title = "エラーが発生しました",
    color = 0xFF000,
    description = "ニックネームに使える文字数は最大32文字です"
)



class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ピンポン
    @commands.command()
    async def ping(self, ctx):
        latency = self.bot.latency
        latency_milli = round(latency * 1000)
        await ctx.channel.send(f"Pong!: {latency_milli}ms")

    # mp4
    @commands.command()
    async def mp4(self, ctx):
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
        proc = await asyncio.create_subprocess_exec(
            *command.split(" "),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        await mes_pros.delete()
        await ctx.channel.send(file=discord.File("resources/temporary/wip_output.mp4"))
        os.remove("resources/temporary/wip_input.mp3")
        os.remove("resources/temporary/wip_output.mp4")

    # 背景を除去(RemoveBG)
    @commands.command()
    async def removebg(self, ctx):
        removebg_apikey = os.getenv("REMOVEBG_APIKEY")

        filename_input = f"resources/temporary/temp_input_{ctx.channel.id}.png"
        filename_output = f"resources/temporary/temp_output_{ctx.channel.id}.png"

        if not await modules.funcs.attachments_proc(ctx, filename_input, "image"):
            return

        async with ctx.typing():
            # RemoveBgAPI
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


    #メンバーのニックネームを一括編集
    #argを指定しなかった場合の例外誰かかいてください
    @commands.command(aliase = "nick")
    async def bulk_edit_nick(self,ctx,arg):
        try:
            #discordで使えるニックネームの最大文字数は32
            if len(arg) > 32:
                embed = EMBED_CHARACTER_LIMIT
            else:
                #変更するメンバー数を数える
                count = 0
                for member in ctx.guild.members:
                    if arg == member.nick:
                        continue
                    #全権限を与えられている場合を除いて、サーバー管理人のニックネームは変更不可（？）
                    #論理式を使うのが下手なので誰か読みやすいように書き換えてください
                    if (not ctx.bot_permissions.administrator) and member == ctx.guild.owner: 
                        continue
                    else:
                        count += 1
                        await member.edit(nick = arg)
                embed = discord.Embed(
                    title = "ニックネーム一括変更",
                    description = f"{count}人のメンバーのニックネームを{arg}に変更しました"
                )
                if ctx.guild.icon:
                    embed.set_thumbnail(url = ctx.guild.icon)
                
        #一応権限がない場合（エラー文間違ってるかも）
        except discord.Forbidden:
            embed = EMBED_FORBIDDEN

        await ctx.channel.send(embed = embed)

