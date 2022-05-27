# seibaribot
[![Check Syntax](https://github.com/SehataKuro/seibaribot/actions/workflows/flake8.yaml/badge.svg?branch=master)](https://github.com/SehataKuro/seibaribot/actions/workflows/flake8.yaml)
- 身内のサーバーで使うことを目的としたDiscord向けのbotです。
- 開発段階のためバグや唐突な仕様変更があります。

## メインコマンド
### !anime, !ani
[Annict](https://annict.com)のデータベースからランダムで作品を表示させます。
### !bokuseku
ボイスチャンネルに参加している状態でこのコマンドを使うと、課長と恋の実験室を流します。
### !chiibakun
なのはな体操の動画のリンクを貼ります。
### !falco, !syai, !faruko
ファル子☆面白画像集チャンネルに貼られた画像やテキストをランダムで返します。
### !giratina
テスト用コマンドです。ギラティナの画像が返ってきます。
### !help
どんなコマンドがあるか見れます。
### !inm
聖バリさんがいまだに淫夢ごっこをします。
### !kaosu
[@kaosu_pic](https://twitter.com/kaosu_pic)から最新の画像を貼ります。
### !komachan
[@komachan_pic](https://twitter.com/komachan_pic)から最新の画像を貼ります。
### !lucky
[@LuckyStarPicBot](https://twitter.com/LuckyStarPicBot)から最新の画像を貼ります。
### !odai
絵のお題を出してくれます。  
[Annict](https://annict.com)のデータベースからお気に入りが5人以上いるキャラクターをランダムで表示させます。
### !ping
テスト用コマンドです。pongが返ってきます。
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
### !yuruyuri
[@YuruYuriBot1](https://twitter.com/YuruYuriBot1)から最新の画像を貼ります。  
今は画像のみですが動画にも対応できるようにしたいです。

## 音楽系コマンド
### !join
ボイスチャンネルにbotを追加するためのコマンドです。  
コマンドを使う人がボイスチャンネルに参加している必要があります。
### !leave
ボイスチャンネルからbotを退出させるコマンドです。
### !play, !p
曲を流すコマンドです。  
大抵のサイトに対応していますが、ニコニコは再生までにかなり時間がかかります。  
近いうちに改善します。

リンクでの再生のほか、検索ワードでの再生も対応しています。

再生中に曲を追加するとキューに追加されます。
### !queue, !q
**現在開発中です。**  
**キューの表示はできませんが、キュー自体は機能しています。**  

~~キューを表示するコマンドです。~~
### !nowplaying, !np
**現在開発中です。**  
**実行すると最後に追加された曲が表示されます(今後修正予定)。**  

再生している曲の情報とリンクを表示するコマンドです。
### !skip
次の曲を再生するコマンドです。
### !stop
曲を止めるコマンドです。キューもリセットされます。

## 言葉狩り機能
言葉狩りをして画像やテキストを返します。   
以下の言葉に反応します。
- big brother
- DJ
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

## その他の機能
- 音声ファイルを動画に変換する機能があります。  
mp3_to_mp4チャンネルに音声を投げると自動で変換されます。  
スマホアプリで音声を聴くのに使えます。

- 起動時にギラティナ、オォン！と鳴いてくれます。