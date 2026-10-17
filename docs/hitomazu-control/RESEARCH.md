# 2026-10-17 実装可否の調査結果

## 先に結論

1. Cloudflare OS公式本体のGadget実行基盤はDynamic Workersであり、Cloudflare公式の料金表ではWorkers Paidプランのみ提供。追加課金禁止のままクラウド版Cloudflare OS本体を本番デプロイするのは現時点で不適切。
2. OpenAI公式「Sign in with ChatGPT」にはオープンソース向けの自己登録型OAuthとプラン利用の仕組みが存在する。独立したサブスク利用枠ではなく、ユーザーの利用枠と共有する。無制限ではない。
3. ChatGPTプラン用の公式Codex app-serverは動作設計例があり、access tokenを安全に渡してResponsesを使う。プロセス起動・トークン更新・認証・永続化を伴うため、静的GitHub Pagesだけでは動かせない。
4. Cloudflare OSの公式Discussion #312にはCodex app-server統合実験版が存在するが、確認できるのは主にローカル単一ユーザー版。ホスト型の認証済み常時稼働は検証対象外。
5. Github Pagesを利用したタスク管理と、GitHub Actionsの定期的な読み取り専用公開サイト監査なら、API課金なしで実施可能。AI推論ではなく通常の自動処理である。

## 根拠

- Cloudflare Dynamic Workers Pricing: https://developers.cloudflare.com/dynamic-workers/pricing/
- OpenAI Sign in with ChatGPT OSS Overview: https://developers.openai.com/siwc/token-sharing-open-source
- OpenAI Codex app-server: https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server
- Cloudflare OS実験的Codex統合: https://github.com/cloudflare/cloudflare-os/discussions/312
- GitHub Pages: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- ForkのGitHub Actions有効化: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows

## 未解決・ブロッカー

- デプロイ先のGitHub Pages有効化（アカウント側の設定が必要）
- GitHub ActionsのFork側許可と実行結果（現時点でコードの静的解析のみ）
- ChatGPT OAuthの手元での認証成功・トークン保管と更新（まだ実装・認証していない）
- Cloudflare OS本体を課金なしでクラウドホスティングできる方式（未確立）
- Notion実データの安全な同期方法と既存担当への確認（未着手）

## 今回完成したもの

- ./index.html + ./app.js + ./style.css : スマホで管理できる端末内保存式タスクボード
- ../../tools/hitomazu-audit/check_sites.py : 公開サイトの読み取り専用チェック
- ../../.github/workflows/hitomazu-dashboard.yml : GitHub Actionsを使った日次チェックと静的サイト配信の設定

商用サイトへのログイン、商品の自動更新、売上取得、AI推論、24時間無休稼働、GitHub Pages公開完了は今回の完了項目に含めない。
