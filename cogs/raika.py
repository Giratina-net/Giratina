from discord.ext import commands
import random
import re
import requests
import MeCab
from nltk import ngrams
from collections import Counter, defaultdict


class Raika(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Raika
    @commands.command()
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
    @commands.command()
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
