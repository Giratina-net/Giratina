# Giratina
[![Check Syntax](https://github.com/SehataKuro/Giratina/actions/workflows/check_syntax.yml/badge.svg?branch=master)](https://github.com/SehataKuro/Giratina/actions/workflows/check_syntax.yml)
[![badge](https://github.com/neko252222/GIF/blob/main/badge.svg)](https://github.com/SehataKuro/Shaymin)
- 身内のサーバーで使うことを目的としたDiscord向けのBotです。
- 開発段階のためバグや唐突な仕様変更があります。

## メインコマンド
### !anime, !ani
[Annict](https://annict.com)のデータベースからランダムで作品を表示します。
### !bokuseku
ボイスチャンネルに参加している状態でこのコマンドを使うと、課長と恋の実験室を流します。
### !chiibakun
なのはな体操の動画のリンクを貼ります。
### !falco, !syai, !faruko
ファル子☆面白画像集チャンネルに貼られた画像やテキストをランダムで返します。
### !giratina
テスト用コマンドです。ギラティナの画像が返ってきます。
### !help
コマンド一覧を表示します。
### !inm
聖バリさんが未だに淫夢ごっこをします。
### !kaosu
[@kaosu_pic](https://twitter.com/kaosu_pic)から最新の画像を貼ります。
### !komachan
[@komachan_pic](https://twitter.com/komachan_pic)から最新の画像を貼ります。
### !lucky
[@LuckyStarPicBot](https://twitter.com/LuckyStarPicBot)から最新の画像を貼ります。
### !odai
絵のお題を出してくれます。  
[Annict](https://annict.com)のデータベースからお気に入りが5人以上いるキャラクターをランダムで表示します。
### !ping
BotサーバーとDiscordサーバー間のPingを表示します。
### !raika
Twitterをやってるときの指の動作またはスマートフォンを凝視するという行動が同じだけなのであって容姿がこのような姿であるという意味ではありません
### !satanya
[@satanya_gazobot](https://twitter.com/satanya_gazobot)から最新の画像を貼ります。
### !twitter, !tw
Twitterの検索を使って画像を返します。  
たとえば`!twitter 猫`と打つと、Twitterで猫と検索した時に表示されるツイートの画像を送信します。  
`!twitter from:@hikakin 猫`みたいなこともできます。

TwitterのJSONの仕様がよくわかってなくて、画像が返ってこないときがあります。  
そもそも検索したツイートがないか、検索ワードがでかすぎると返されないっぽいです。  
`!twitter ウマ娘`だと何も返ってこないけど`!twitter アグネスタキオン`だとひっかかる場合がありました。
### !uma
ウマ娘のガチャシミュレーターです。  
実装ウマ娘やピックアップなどは2022/6/10現在のものです。  
確率は以下の通り。  

1~9回目:  
| ☆1 | ☆2 | ☆3 |
| :---: | :---: | :---: |
| 79% | 18% | 3% (ピックアップ0.75%) |

10回目:  
| ☆1 | ☆2 | ☆3 |
| :---: | :---: | :---: |
| 0% | 97% | 3% (ピックアップ0.75%) |
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
現在再生中の曲と以降再生される10個の曲を表示します。
### !skip, !s
現在再生中の曲をスキップするコマンドです。  
キューが残っている場合には次の曲を再生します。
### !shuffle
キューをシャッフルします。
### !stop
曲を止めるコマンドです。キューもリセットされます。

## 言葉狩り機能
言葉狩りをして画像やテキストを返します。   
以下の言葉に反応します。
- big brother
- DJ
- somunia
- いい曲
- おはよう
- ドナルド
- バキ
- メタ
- やんぱ
- ゆるゆり
- ランキング
- 一週間
- 死んだ
- 風呂
- ライカ

## その他の機能
- 音声ファイルを動画に変換する機能があります。  
mp3_to_mp4チャンネルに音声を投げると自動で変換されます。  
スマホアプリで音声を聴くのに使えます。
- 起動時にギラティナ、オォン！と鳴いてくれます。
