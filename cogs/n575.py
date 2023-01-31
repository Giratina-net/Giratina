
        # 検索欄チャンネルに投稿されたメッセージから、TwitterAPIを通してそのメッセージを検索して、チャンネルに画像を送信する
        # if ctx.content and ctx.channel.id == TWITTER_SEARCH_CHANNEL_ID:
        #     tweets = twapi.search_tweets(q=f"filter:images {arg}", tweet_mode="extended", include_entities=True, count=1)
        #     for tweet in tweets:
        #         media = tweet.extended_entities["media"]
        #         for m in media:
        #             origin = m["media_url"]
        #     await ctx.channel.send(origin)

        # n575
        # https://gist.github.com/4geru/46f300e561374833646ffd8f4b916672
        # if not ctx.author.bot:
        #     m = MeCab.Tagger()
        #     print(str(ctx.content))
        #     print(m.parse(str(ctx.content)))
        # check = [5, 7, 5]  # 5, 7, 5
        # check_index = 0
        # word_cnt = 0
        # node = m.parseToNode(str(ctx.content))
        # # # suggestion文の各要素の品詞を確認
        # while node:
        #     feature = node.feature.split(",")[0]
        #     surface = node.surface.split(",")[0]
        #     print(feature)
        #     print(surface)
        #     # 記号, BOS/EOSはスルー
        #     if feature == "記号" or feature == "BOS/EOS":
        #         node = node.next
        #         continue
        #     # 文字数をカウント
        #     word_cnt += len(surface)
        #     # 字数チェック
        #     if word_cnt == check[check_index]:
        #         check_index += 1
        #         word_cnt = 0
        #         continue
        #     # 字余りチェック
        #     elif word_cnt > check[check_index]:
        #         return False
        #
        #     # [5, 7, 5] の長さになっているか
        #     if check_index == len(check) - 1:
        #         return True
        #     node = node.next
        # print("俳句を見つけました！")
        # return False
