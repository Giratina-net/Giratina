import csv
import os
import random
import re

import aiohttp
import discord
import requests
from PIL import Image

import modules.img
import modules.img_utils as img_utils


# 添付ファイル処理用の関数
async def attachments_proc(ctx, filepath, media_type):
    # URL先のファイルが指定したmimetypeであるかどうかを判定する関数
    async def ismimetype(url, mimetypes_list):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        mime = resp.headers.get("Content-type", "").lower()
                        if any([mime == x for x in mimetypes_list]):
                            return True
                        else:
                            return False
        except:
            return False

    mimetypes = {
        "image": ["image/png", "image/pjpeg", "image/jpeg", "image/x-icon"],
        "gif": ["image/gif"],
        "audio": ["audio/wav", "audio/mpeg", "audio/aac", "audio/ogg"],
        "video": [
            "video/mpeg",
            "video/mp4",
            "video/webm",
            "video/quicktime",
            "video/x-msvideo",
        ],
    }

    url = ""
    # 返信をしていた場合
    if ctx.message.reference is not None:
        message_reference = await ctx.channel.fetch_message(
            ctx.message.reference.message_id
        )
        # 返信元のメッセージにファイルが添付されていた場合
        if len(message_reference.attachments) > 0:
            url = message_reference.attachments[0].url
        # 返信元のメッセージにファイルが添付されていなかった場合
        else:
            await ctx.reply("返信元のメッセージにファイルが添付されていません", mention_author=False)
            return False
    # 返信をしていなかった場合
    else:
        # 直近10件のメッセージの添付ファイル・URLの取得を試みる
        async for message in ctx.history(limit=10):
            mo = re.search(r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+", message.content)
            # メッセージに添付ファイルが存在する場合
            if len(message.attachments) > 0:
                url = message.attachments[0].url
            # メッセージにURLが存在し、URL先が画像である場合
            elif mo:
                url = mo.group()
                # URL判定
            if await ismimetype(url, mimetypes[media_type]):
                break
        # どちらも存在しない場合
        else:
            await ctx.reply(
                "ファイルやurlが添付されたメッセージの近くに書くか、返信をしてください", mention_author=False
            )
            return False

    # ダウンロード
    response = requests.get(url)
    image = response.content
    with open(filepath, "wb") as f:
        f.write(image)
        return True


async def send_uma(channel, author, custom_weights):
    class Chara:
        # アイコン画像の数字に一致
        id = 0
        rarity = 0
        is_pickup = 0

        def __init__(self, id, rarity, is_pickup):
            self.id = id
            self.rarity = rarity
            self.is_pickup = is_pickup

    class Gacha_Usage:
        user = ""
        chara_id_list = []
        exchange_point = 0

        def __init__(self, user, ids, exchange_point):
            self.user = user
            self.chara_id_list = ids
            self.exchange_point = exchange_point

    chara_list = []
    usage_list = []
    path_uma_gacha = "resources/uma_gacha"
    path_output = f"resources/temporary/uma_gacha_{channel.id}.png"
    fontsize = 32
    region_particle = img_utils.Region(
        [
            img_utils.Rect(0, 30, 32, 236),
            img_utils.Rect(32, 30, 207, 56),
            img_utils.Rect(207, 30, 240, 236),
        ]
    )

    async with channel.typing():
        # CSVファイルからキャラ情報を読み込み
        with open("resources/csv/uma_chara_info.csv") as f:
            reader = csv.reader(f)
            for row in reader:
                chara = Chara(int(row[0]), int(row[1]), int(row[2]))
                chara_list.append(chara)

        # CSVファイルからガチャ使用情報を読み込み
        with open("resources/csv/uma_gacha_usage.csv") as f:
            reader = csv.reader(f)
            for row in reader:
                u = Gacha_Usage(
                    int(row[0]), [int(s) for s in row[1].split("/")], int(row[2])
                )
                usage_list.append(u)

        # コマンド使用者がガチャ使用情報に載っているか確認
        chara_id_list = []
        exchange_point = 0
        for i, u in enumerate(usage_list):
            if author.id == u.user:
                chara_id_list = u.chara_id_list
                exchange_point = u.exchange_point
                usage_list.pop(i)

        # 確率比[★1, ★2, ★3]
        weights = [79, 18, 3]
        # 確率比(10回目)
        weights_10 = [0, 97, 3]

        # 確率比(カスタム)
        if custom_weights:
            weights = custom_weights
            weights_10 = [0, sum(custom_weights) - custom_weights[2], custom_weights[2]]

        # 画像の初期化
        m_img = modules.img.Giratina_Image()
        m_img.load(f"{path_uma_gacha}/bg.png")

        for i in range(10):
            w = weights if i < 9 else weights_10

            chara_results_by_rarity = []

            # レア度1はピックアップが存在しないため等確率で選出
            chara_results_by_rarity.append(
                random.choice([ch for ch in chara_list if ch.rarity == 1])
            )

            # レア度2以降はピックアップの有無ごとに選出
            for r in range(2, 4):
                chara_result_by_rarity = 0
                list_pickup = [
                    ch for ch in chara_list if ch.rarity == r and ch.is_pickup
                ]
                list_not_pickup = [
                    ch for ch in chara_list if ch.rarity == r and not ch.is_pickup
                ]
                # ピックアップ1体ごとの確率
                prob_pickup = 0.75 if r == 3 else 2.25

                # ピックアップが存在し、出現率が0より大きい場合
                if len(list_pickup) and w[r - 1] > 0:
                    chara_results_by_pickup = random.choices(
                        [list_pickup, list_not_pickup],
                        weights=[
                            len(list_pickup) * prob_pickup,
                            w[r - 1] - len(list_pickup) * prob_pickup,
                        ],
                    )[0]
                    chara_result_by_rarity = random.choice(chara_results_by_pickup)
                # ピックアップが存在しない、あるいは出現率が0の場合
                else:
                    chara_result_by_rarity = random.choice(
                        [ch for ch in chara_list if ch.rarity == r]
                    )
                chara_results_by_rarity.append(chara_result_by_rarity)

            # 最終的な排出ウマ娘を決定
            chara_result = random.choices(chara_results_by_rarity, weights=w)[0]

            # アイコン画像をchara_iconフォルダから読み込み&貼り付け
            chara_icon = Image.open(
                f"{path_uma_gacha}/chara_icon/{chara_result.id}.png"
            )

            x = 0
            y = 0
            # 3つ並びの行
            if i % 5 < 3:
                x = 96 + 324 * (i % 5)
                y = 157 + 724 * (i // 5)
            # 2つ並びの行
            else:
                x = 258 + 324 * (i % 5 - 3)
                y = 519 + 724 * (i // 5)

            m_img.composit(chara_icon, (x, y))

            piece_x = 0
            bonus_x = 0
            num_piece = 0
            num_megami = 0
            text_piece_x = 0

            if chara_result.rarity == 3:
                num_megami = 20
                if chara_result.is_pickup:
                    num_piece = 90
                else:
                    num_piece = 60
            elif chara_result.rarity == 2:
                num_megami = 3
                num_piece = 10
            else:
                num_megami = 1
                num_piece = 5

            # 排出ウマ娘が獲得済みの場合
            if chara_result.id in chara_id_list:
                adjust_x = -11 if chara_result.rarity == 2 else 0
                # 女神像
                megami = Image.open(f"{path_uma_gacha}/icon_megami.png")
                megami_x = 4 if chara_result.rarity == 3 else 26
                m_img.composit(megami, (x + megami_x + adjust_x, y + 300))

                # ピース・おまけの位置
                piece_x = 130 + adjust_x
                bonus_x = 134 + adjust_x
                text_piece_x = 182 + adjust_x

                # テキスト(女神像)
                text_megami_x = 54 if chara_result.rarity == 3 else 76
                m_img.drawtext(
                    f"x{num_megami}",
                    (x + text_megami_x + adjust_x, y + 311),
                    fill=(124, 63, 18),
                    anchor="lt",
                    fontpath=".fonts/rodin_wanpaku_eb.otf",
                    fontsize=fontsize,
                    stroke_width=2,
                    stroke_fill="white",
                )

            # 未獲得の場合
            else:
                chara_id_list.append(chara_result.id)
                # NEW!
                label_new = Image.open(f"{path_uma_gacha}/label_new.png")
                m_img.composit(label_new, (x - 22, y))

                adjust_x = 11 if chara_result.rarity == 1 else 0

                # ピース・おまけの位置
                piece_x = 65 + adjust_x
                text_piece_x = 117 + adjust_x
                bonus_x = 68 + adjust_x

            # テキスト(ピース)
            m_img.drawtext(
                f"x{num_piece}",
                (x + text_piece_x, y + 311),
                fill=(124, 63, 18),
                anchor="lt",
                fontpath=".fonts/rodin_wanpaku_eb.otf",
                fontsize=fontsize,
                stroke_width=2,
                stroke_fill="white",
            )

            # ピース
            piece = Image.open(f"{path_uma_gacha}/piece_icon/{chara_result.id}.png")
            m_img.composit(piece, (x + piece_x, y + 300))

            # おまけ
            label_bonus = Image.open(f"{path_uma_gacha}/label_bonus.png")
            m_img.composit(label_bonus, (x + bonus_x, y + 286))

            # レア度が3の場合枠を描画
            if chara_result.rarity == 3:
                frame = Image.open(f"{path_uma_gacha}/frame.png")
                m_img.composit(frame, (x - 8, y))

            # パーティクルを描画
            if chara_result.rarity > 1:
                num_stars = 7 if chara_result.rarity == 3 else 5
                particle = Image.open(
                    f"{path_uma_gacha}/particle_{chara_result.rarity}.png"
                )
                particle_pos = None
                for _ in range(num_stars):
                    scale = random.uniform(1, 3)
                    particle_resize = particle.resize(
                        (int(particle.width // scale), int(particle.height // scale))
                    )
                    particle_pos = region_particle.randompos()
                    m_img.composit(
                        particle_resize,
                        (
                            x - (particle_resize.width // 2) + particle_pos[0],
                            y - (particle_resize.height // 2) + particle_pos[1],
                        ),
                    )

            # 星マークを貼り付け
            stars = Image.open(f"{path_uma_gacha}/stars_{chara_result.rarity}.png")
            m_img.composit(stars, (x + 46, y + 243))

        # 育成ウマ娘交換ポイント書き込み
        m_img.drawtext(
            str(exchange_point),
            (732, 1611),
            fill=(124, 63, 18),
            anchor="rt",
            fontpath=".fonts/rodin_wanpaku_eb.otf",
            fontsize=fontsize,
        )
        exchange_point += 10
        m_img.drawtext(
            str(exchange_point),
            (860, 1611),
            fill=(255, 145, 21),
            anchor="rt",
            fontpath=".fonts/rodin_wanpaku_eb.otf",
            fontsize=fontsize,
        )

        # リザルト画面の保存&読み込み
        m_img.write(path_output)
        gacha_result_image = discord.File(path_output)

        # ボタンのサブクラス
        class Button_Uma(discord.ui.Button):
            async def callback(self, interaction):
                response = interaction.response
                await response.edit_message(view=None)
                await send_uma(interaction.channel, interaction.user, custom_weights)

        button = Button_Uma(style=discord.ButtonStyle.success, label="もう一回引く")

        view = discord.ui.View()
        view.timeout = None
        view.add_item(button)

        # メッセージを送信
        await channel.send(
            content=f"<@{author.id}>", file=gacha_result_image, view=view
        )

    # 生成した画像を削除
    if os.path.isfile(path_output):
        os.remove(path_output)

    # ガチャ使用情報を更新
    usage = Gacha_Usage(author.id, chara_id_list, exchange_point)
    usage_list.append(usage)

    with open("resources/csv/uma_gacha_usage.csv", "w") as f:
        writer = csv.writer(f)
        for u in usage_list:
            writer.writerow(
                [u.user, "/".join([str(n) for n in u.chara_id_list]), u.exchange_point]
            )
