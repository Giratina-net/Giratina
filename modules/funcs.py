import aiohttp
import re
import requests


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