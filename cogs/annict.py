import random

import requests
from discord.ext import commands


class Annict(commands.Cog):
    def __init__(self, bot, annict_api_key):
        self.bot = bot
        self.annict_api_key = annict_api_key

    @commands.command(aliases=["ani"])
    async def anime(self, ctx):
        random_id = random.randint(1, 9669)
        # エンドポイント
        annict_url = f"https://api.annict.com/v1/works?access_token={self.annict_api_key}&filter_ids={random_id}"
        # リクエスト
        annict_res = requests.get(annict_url)
        # 取得したjsonから必要な情報を取得
        annict_works = annict_res.json()["works"][0]
        annict_works_title = annict_works["title"]
        annict_works_season_name_text = annict_works["season_name_text"]
        annict_works_episodes_count = annict_works["episodes_count"]
        annict_works_images_recommended_url = annict_works["images"]["recommended_url"]
        await ctx.channel.send(
            f"{annict_works_title}({annict_works_season_name_text}-{annict_works_episodes_count}話)\nhttps://annict.com/works/{random_id}"
        )

    # アニクトから取得したキャラクターをランダムで表示
    @commands.command()
    async def odai(self, ctx):
        while 1:
            # 10個のランダムな数を生成
            random_ids = [str(random.randint(1, 41767)) for _ in range(10)]
            # リストの中の要素を結合する
            filter_ids = ",".join(random_ids)
            # エンドポイント
            annict_url = f"https://api.annict.com/v1/characters?access_token={self.annict_api_key}&filter_ids={filter_ids}"
            # リクエスト
            annict_res = requests.get(annict_url)
            # 変数
            annict_characters = annict_res.json()["characters"]
            # シャッフルする
            random.shuffle(annict_characters)
            # お気に入り数が5以上の要素のみ抽出
            annict_characters_favorite_count = list(
                filter(lambda e: e["favorite_characters_count"] > 4, annict_characters)
            )
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
