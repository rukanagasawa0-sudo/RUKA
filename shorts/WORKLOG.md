# 作業ログ：ワンピースカード ショート動画（トレカラフテル / ちゃみtv）

最終更新：2026/11/14

会話の全文（パソコンのブラウザで開けます。スマホと同じアカウントでログイン）：
https://claude.ai/code/session_01JhQexwLSiHDmULVH4uyFHG

ファイル一式（GitHub）：
https://github.com/rukanagasawa0-sudo/RUKA/tree/claude/adoring-bohr-umuey5/shorts

---

## 1. 現在の完成動画（`shorts/output/`）

| # | ファイル | 内容 | 長さ | 名札 |
|---|---|---|---|---|
| 2 | v2_op18_summary.mp4 | 新弾「神の支配」買う前にこれだけ見て！ | 46秒 | 司会・Aさん |
| 3 | v3_price_quiz.mp4 | 3秒で答えて！一番高いカードは？（トレカラフテル販売価格） | 35秒 | 司会・Aさん・Bさん |
| 5 | v5_release_calendar.mp4 | ワンピカ半年分の発売日まとめ | 38秒 | 司会・Aさん |

- 1（値上がりBOXランキング）と 4（環境シェア）は、ご依頼により削除済み。
- v2 のアップロード一式：`v2_upload_set.zip`（動画・縦型サムネ `v2_thumbnail_1080x1920.png`・タイトル/説明文 `v2_upload.txt`）

## 2. これまでの主な修正

- 画像：公式サイトのカード・パック・BOX画像を使用（天野喜孝パラレル、ニコ・ロビンSP、神の騎士団パラレル含む）
- 店名：トレカラフテル（秋葉原の店舗＆通販 tcg-raftel.com）。「予約」と誤解される表現は使わない
- テーマ：神の支配は「ウォーターセブン・エルバフ・アラバスタ」
- テロップ：言葉の区切りで自然に改行、字幕と中央の文字が重ならないよう全フレーム自動チェック
- 文字：小さい文字・潰れる縁取りを全面見直し（クイズのTOP3・「全部ルフィ！！」など）
- 強調：並べた名前は色をそろえる（フランキー・ロキ・カルーを全部赤に）
- 読み上げ：速さ1.08倍、話者交代の間0.28秒（速すぎて不自然だったのを調整）
- 画面下のクレジットは表示しない（VOICEVOX名と©表記は概要欄に必ず入れる）
- クイズ：価格はトレカラフテル通販の販売価格、回答の流れを自然に（Aさん→B、Bさん→C、正解A）

## 3. アップロードの状況（未完了）

- このセッションはクラウドで動いており、パソコン・携帯・YouTubeには直接つながっていないため、まだアップロードしていません。
- 方法A：トークンを発行して Claude に任せる（下の手順）
- 方法B：携帯のYouTubeアプリで「ちゃみtv」に切り替えて自分でアップロード（おすすめ・約2分）

### 方法A：トークンの発行手順（パソコン推奨）
1. https://developers.google.com/oauthplayground を開く
2. 左の「Step 1」のAPI一覧の一番下の入力欄に `https://www.googleapis.com/auth/youtube.upload` を貼り、「Authorize APIs」
3. 「ちゃみtv」を管理するGoogleアカウントでログイン → チャンネル「ちゃみtv」を選択 →「許可」
4. 「Step 2」で「Exchange authorization code for tokens」→「Access token」（ya29.で始まる）をコピー
5. Claude に「発行できた」と伝える → 出てくるフォームに貼る（チャットには貼らない）。有効期限は約1時間
6. Claude が非公開でアップロード＋サムネ設定 → 確認後に公開/予約公開へ切り替え

### 方法B：携帯からのアップロード手順
1. 動画とサムネを携帯に保存
2. YouTubeアプリ：右下アイコン →「アカウントを切り替える」→「ちゃみtv」
3. 「＋」→ 動画を選択 →「次へ」
4. タイトル：`新弾「神の支配」買う前にこれだけ見て！天野喜孝パラレルも【ワンピースカード】`
5. 説明文：`v2_upload.txt` の中身を貼る（VOICEVOXと©の2行は消さない）
6. サムネの項目があれば縦型サムネを選択 →「子ども向けではありません」→ アップロード
7. 公開は発売前の 11/19〜20 の夕方がおすすめ

## 4. 作り直し方（エンジニア向け）

```bash
python3 shorts/make.py            # 全部作る（v2 v3 v5）
python3 shorts/make.py v2         # 1本だけ
python3 shorts/tools/check_overlap.py   # 字幕との重なりチェック
python3 shorts/thumbs/make_thumb_v2.py  # v2 のサムネ
```
- 店名・告知文：`shorts/config.py`
- 読み上げの速さ：`shorts/engine/render.py` の `TEMPO` / `TURN_GAP` / `MAX_PAUSE`
- 台本：`shorts/scripts/v*.py`、名札は各台本の `names=`

## 5. 出典（2026/11/13〜14 確認）
- 新弾・発売予定・商品画像・カード画像：ONE PIECEカードゲーム公式サイト / ONE PIECE.com
- クイズの価格：トレカラフテル通販（tcg-raftel.com）
- 神の支配の収録内容：公式商品ページ、GameWith 系まとめ
