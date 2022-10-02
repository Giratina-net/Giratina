# Giratina
[![Check Syntax](https://github.com/SehataKuro/Giratina/actions/workflows/check_syntax.yml/badge.svg?branch=master)](https://github.com/SehataKuro/Giratina/actions/workflows/check_syntax.yml)  
身内のサーバーで使うことを目的としたDiscord向けのBotです。  
開発段階のためバグや唐突な仕様変更があります。

## メインコマンド
### !anime, !ani
[Annict](https://annict.com)のデータベースからランダムで作品を表示します。
### !bokuseku
ボイスチャンネルに参加している状態でこのコマンドを使うと、課長と恋の実験室を流します。
### !chiibakun
なのはな体操の動画のリンクを貼ります。
### !falco, !syai, !faruko
`ファル子☆面白画像集`チャンネルに貼られた画像やテキストをランダムで返します。
### !fami2
[@fami2repo_bot](https://twitter.com/fami2repo_bot)から最新のツイート10件からランダムでテキストを送信します。
### !genshin
Twitterから#GenshinImpactのついた1000いいね以上のツイートの画像を貼ります。
### !giratina
テスト用コマンドです。ギラティナの画像が返ってきます。
### !help
コマンド一覧を表示します。
### !hentai
`no context hentai img`チャンネルに貼られた画像やテキストをランダムで返します。
### !hiroyuki
おしゃべりひろゆきを生成します。
### !hutao
Twitterから`#胡桃`のついた1000いいね以上のツイートの画像を貼ります。
### !inm
聖バリさんが未だに淫夢ごっこをします。
### !kaosu
[@kaosu_pic](https://twitter.com/kaosu_pic)から最新の画像を貼ります。
### !komachan
[@komachan_pic](https://twitter.com/komachan_pic)から最新の画像を貼ります。
### !lucky
[@LuckyStarPicBot](https://twitter.com/LuckyStarPicBot)から最新の画像を貼ります。
### !ma
ま
### !machitan
`まちカドたんほいざ`チャンネルに貼られた画像やテキストをランダムで返します。
### !manomu, !mano
家で飼ってるピーちゃんを使ったお料理も好きです。
### !mraika
マルコフ連鎖でRaikaさんのツイートを生成します。
### !odai
絵のお題を出してくれます。  
[Annict](https://annict.com)のデータベースからお気に入りが5人以上いるキャラクターをランダムで表示します。
### !ping
BotサーバーとDiscordサーバー間のPingを表示します。
### !raika
9586件のRaikaツイートからランダムでテキストを送信。
### !removebg
remove.bg APIを用いて画像の背景を透過します。
### !satanya
[@satanya_gazobot](https://twitter.com/satanya_gazobot)から最新の画像を貼ります。
### !sushi
[@kasakioiba](https://twitter.com/kasakioiba)から最新の画像を貼ります。
### !toukaiteiou, !teiou, !teio-, !teio
`ﾎﾞｸはﾃｲｵｰ！ちゃんねる`に貼られた画像やテキストをランダムで返します。
### !twitter, !tw
Twitterの検索を使って画像を返します。  
たとえば`!twitter 猫`と打つと、Twitterで猫と検索した時に表示されるツイートの画像を送信します。  
`!twitter from:@hikakin 猫`みたいなこともできます。

TwitterのJSONの仕様がよくわかってなくて、画像が返ってこないときがあります。  
そもそも検索したツイートがないか、検索ワードがでか過ぎると返されないっぽいです。  
`!twitter ウマ娘`だと何も返ってこないけど`!twitter アグネスタキオン`だとひっかかる場合がありました。
### !twitterdl, !twdl
ツイートのURLから最も高画質な動画URLを送信します。
### !uma
ウマ娘のガチャシミュレーターです。    
確率は以下の通り。  

1~9回目:  
| ☆1 | ☆2 | ☆3 |
| :---: | :---: | :---: |
| 79% | 18% | 3% |

10回目:  
| ☆1 | ☆2 | ☆3 |
| :---: | :---: | :---: |
| 0% | 97% | 3% |
※1~9回目も10回目も、ピックアップキャラの出現率は1体当たり0.75%です。
### !yuruyuri
[@YuruYuriBot1](https://twitter.com/YuruYuriBot1)から最新の画像を貼ります。  
今は画像のみですが動画にも対応できるようにしたいです。

## 音楽系コマンド
### !join
ボイスチャンネルにBotを追加するためのコマンドです。  
コマンドを使う人がボイスチャンネルに参加している必要があります。
### !leave
ボイスチャンネルからBotを退出させるコマンドです。
### !nowplaying, !np
再生している曲の情報とリンクを表示するコマンドです。
### !play, !p
曲を流すコマンドです。大抵のサイトに対応しています。  
リンクでの再生のほか、検索ワードでの再生も対応しています。  
再生中に曲を追加するとキューに追加されます。
### !queue, !q
キューを表示するコマンドです。  
再生中の曲と以降再生される10個の曲を表示します。
### !skip, !s
再生中の曲をスキップするコマンドです。  
キューが残っている場合には次の曲を再生します。
### !shuffle
キューをシャッフルします。
### !stop
曲を止めるコマンドです。キューもリセットされます。

## 言葉狩り機能
言葉狩りをして画像や音声、テキストを返します。   
以下の言葉に反応します。
- big brother
- DJ
- somunia
- アーメン
- いい曲
- おはよう
- カニ
- クワガタ
- ドナルド
- バキ
- メタ
- やんぱ
- ゆるゆり
- ライカ
- ランキング
- 一週間
- 君しかいないんだよ
- 死んだ
- 昼
- 風呂

## その他の機能
- 音声ファイルを動画に変換する機能があります。  
`mp3_to_mp4`チャンネルに音声を投げると自動で変換されます。  
スマートフォン版Discordで音声を聴くのに使えます。
