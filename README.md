# AI LINE Assistant — 第1段階

## 機能
- iPhone Safari / Tesla車載ブラウザ向けレスポンシブUI
- ChatGPT (OpenAI API) / Grok (xAI API) 切替
- 対応ブラウザで音声認識、音声読み上げ（Web Speech API。iOS/車載ブラウザでは動作が異なります）
- AI返信文の作成とLINE共有画面の起動
- LINE個人トークの受信・連絡先自動指定・自動送信には**非対応**

## 1. Render（バックエンド）
1. `backend/` のファイルをGitHubの**非公開リポジトリ**にアップロード。
2. Renderで新しいWeb Serviceを作り、リポジトリを指定。Root Directoryは `backend`（リポジトリ直下に配置した場合は空欄）。
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. 環境変数 `OPENAI_API_KEY`、`XAI_API_KEY` を設定。必要に応じて `OPENAI_MODEL`、`XAI_MODEL` を変更。モデル名は各プロバイダーで利用可能なものを指定してください。
6. 環境変数 `ALLOWED_ORIGINS` に公開するGitHub Pagesのオリジンを設定。例: `https://YOURNAME.github.io`。末尾のパスは含めません。複数の場合はカンマ区切り。
7. `https://<RenderのURL>/health` を開き、`status: ok` を確認。

## 2. GitHub Pages（フロントエンド）
1. `frontend/index.html` と `frontend/manifest.webmanifest` を公開用リポジトリにアップロード。
2. Settings → Pages → Deploy from a branch → main / root を選択。
3. 公開されたURLをiPhone Safariで開く。
4. `Render API URL` にRenderのURLを入力して保存・接続テスト。
5. iPhone Safariの「共有」→「ホーム画面に追加」でアプリ風に利用できます。

## 3. 使い方
1. AIモデルを選択。
2. マイク（対応ブラウザのみ）またはテキストで依頼し「AIに送信」。
3. AIの回答を確認し「AIの回答を反映」または返信文を手で修正。
4. 「LINEで送信先を選ぶ」を押し、LINE側で送信先を選択・確認して送信。
5. 運転中は画面操作しないでください。停車してからLINEで送信を確定してください。

## セキュリティ・制限
- APIキーは必ずRenderの環境変数に保存。GitHub Pagesには記載しない。
- この試作APIにはユーザー認証・レート制限がありません。**一般公開して運用しないでください。** 第2段階前に認証、レート制限、利用量上限を追加してください。
- 会話履歴はブラウザのメモリのみで、更新時に消去されます。接続先URLとAI選択のみlocalStorageに保存します。
- テキストはRenderを経由して選択したAI事業者に送信されます。
- LINEへの共有URLは、LINEがインストールされたiPhoneでの利用を想定。TeslaブラウザではLINEアプリを起動できません。
- iPhoneの音声認識・音声合成やBluetooth音声出力はOS/ブラウザ/車両状態に依存します。バックグラウンドでの常時待ち受けは非対応。
- Teslaブラウザのマイク対応は保証しません。Teslaではテキスト操作を基本とします。
- LINE通知本文の自動取得、個人アカウントからの無人送信は非対応です。
