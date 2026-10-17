# ひとまず道具店・AI業務本部（無料の試作版）

このフォルダはCloudflare OS本体から独立した静的Webアプリです。Cloudflare OSのAI推論・Sign in with ChatGPT・Notion同期・複数端末同期・自律実行ができると誤認しないでください。

## 動く機能

- タスク追加・編集・状態遷移・削除・担当フィルター
- タスク別の「AI依頼文をコピー」（ChatGPT等に貼り付けるための文章を生成。AIに自動送信はしません）
- 売上・注文件数の「未確認」と0の区別
- JSONバックアップと読み込み
- GitHub Actionsによる公開サイト2件の簡易HTTP/販売リンク点検結果の表示

初期表示の3件は候補であり、既存Notionや実際の担当体制と照合したタスクではありません。

データはブラウザのlocalStorageにのみ保存されます。端末変更・シークレットモード・Safariデータ削除で消える可能性があります。GitHub Pagesで公開しても、保存したタスク自体はGitHubに公開されません。ブラウザ間同期はありません。機密データは入力しないでください。

## GitHub Pagesで公開する

1. この開発ブランチをmainへ反映する。
2. リポジトリの Settings → Pages → Build and deployment → Source → GitHub Actions に設定する（GitHub Pagesはpublic repoで無料枠を利用可能）。
3. Actions画面でworkflowが使えることを確認する。ForkはGitHub Actionsがデフォルト無効の場合がある。Hitomazu Free Site Audit and Dashboard を有効化して Run workflow するか、mainへのpushで自動実行させる。
4. https://ge2kanata-droid.github.io/cloudflare-os/ を開く。URLはGitHub Pagesの発行後のみ有効です。GitHub Pages Settingsで提示されるURLを正とする。

定期ジョブはUTC毎日01:23（日本時間10:23）に実行する設定です。ただしGitHub Actionsのスケジュールは遅延や自動無効化があり、常時稼働とは違います。

## セキュリティと料金

- 課金サービス/APIキー不要。公開ページにGETリクエストを送るだけ。
- 売上の実測は管理画面から手動入力。HTTPアクセス結果で売上が発生したと判断しない。
- 非公開API・認証Cookie・ChatGPT資格情報をコードやGitHub公開リポジトリへ保存しない。
- URLの応答403/429はアクセス制御の可能性もあるため「要確認」とし、停止扱いしない。
- 無料枠は無限ではない。GitHub Actions/Pagesの利用枠・利用規約に従う。

## 本体Cloudflare OSとの違いと今後の計画

Cloudflare OS本体のGadgetsはDynamic Workersに依存し、2026年10月時点でPaidプラン限定。したがって「Cloudflare OSをCloudflare無料枠で24時間動かす」は未達。

OpenAI公式の [Sign in with ChatGPT（OSS向け）](https://developers.openai.com/siwc/token-sharing-open-source) はChatGPTプランを使うAI推論の道を提供するが、サブスク利用枠は有限で、Cloudflare OSへの接続と自動稼働の実装・ホスティング・秘密情報の安全な管理が別途必要。商用のリモートホスト型アプリは別の参加手続きが必要になる場合がある。

優先順位：非破壊タスク管理 → 既存Notionと照合 → 公式認証とバックエンドの可否検証 → 小規模な自動化 → 本番公開。購入・広告・契約・既存公開物の上書きは承認制。
