# タスク分解（丁寧・テストあり）  
以下は「Bedrock Agent を使った元気をくれるチャットアプリ」について、**ミスを減らすために各タスクで必ずテストを実施する**ことを前提に細かく分解したワークブレイクダウンです。  
初心者の方でも実行できるように、**事前条件・具体的テスト手順・受け入れ基準**を必ず明記しています。担当者欄は空欄にしていますので、担当者を割り当ててから運用してください。

> ※ 工数は目安です。チームの熟練度により増減します。  
> ※ 全ての API テストは `curl` 例、ユニットテストは `pytest` 例、AWS 操作はコンソール操作 or AWS CLI のどちらでも実行できる想定です。

---

| ID | タスク | サブタスク（詳細） | 事前条件 | 成果物 / 受け入れ基準 | テスト手順（具体） | テストデータ（例） | 依存 | 推定工数 |
|---:|---|---|---|---:|---|---|---|---:|
| T1 | プロジェクト準備 | - リポジトリ作成（Git）<br>- ブランチ戦略決定（main/dev/feature）<br>- Issue テンプレート作成 | AWS アカウント、チームの Git アカウント | リポジトリが作られ、テンプレートが用意されている | Git clone → ブランチ作成 → PR 作成までの流れを検証 | repo: `genki-chat` | なし | 2h |
| T2 | IAM 基盤（最小権限設計） | - Lambda 用ロール作成（DynamoDB, Bedrock 呼出し権限のみ）<br>- CI 用デプロイロール作成 | AWS 管理者アクセス | IAM ロールに最小限のポリシーが付与されている | ロールで一時認証し、想定外のリソースにアクセスできないことを確認（例：s3:ListBucket がない） | なし | なし | 4h |
| T3 | Bedrock Agent 作成（PoC） | - Agent 定義作成（「元気をくれる」プロンプト）<br>- Alias 作成 | Bedrock を利用可能なリージョン権限 | Agent が作成され、Alias から呼び出せる | PoC Lambda から InvokeAgent を呼び、応答が返ることを確認（ログ確認） | テスト入力: `今日は疲れた` | T2 | 6h |
| T4 | S3 + CloudFront（静的ホスティング） | - S3 バケット作成（静的ホスト）<br>- CloudFront 配信作成（HTTPS, OAI） | ドメイン/ACM は任意 | CloudFront の URL で index.html が表示される | ブラウザで配信ドメインにアクセスし、SPA が表示される | index.html の簡易ページ | なし | 4h |
| T5 | Cognito ユーザープール作成 | - User Pool 作成（メール認証）<br>- App Client 作成（Cognito Hosted UI も選択可） | IAM 権限 | サインアップ／サインインが出来、ID トークンが取得できる | Hosted UI またはカスタム UI で登録→確認メール→ログイン→トークン取得を確認 | testuser@example.com / `Passw0rd!` | T2 | 6h |
| T6 | DynamoDB テーブル作成 | - `UserTable` と `ChatHistoryTable` 作成（PK/SK 設計）<br>- テーブルのスループット設定 | T2 の IAM 権限 | テーブル作成済みで PutItem/GetItem が可能 | AWS CLI: `aws dynamodb put-item` → `get-item` で保存データ確認 | userId: `test-user-1` | T2 | 3h |
| T7 | API Gateway + Lambda 基盤 | - HTTP API 作成<br>- Lambda（雛形）作成（/chat, /history）<br>- Cognito Authorizer 設定 | T5, T6, T2 | /chat と /history が認証付きで呼べる | `curl` で Authorization: Bearer <id_token> を付けて POST /chat（空でないメッセージ）、200 を確認 | Authorization header に取得した id_token | T5,T6 | 8h |
| T8 | Lambda: /chat 実装（ユニット） | - 入力バリデーション実装<br>- DynamoDB に user message 保存<br>- Bedrock Invoke 呼び出し（同期）<br>- Agent 応答を保存 | T3, T6, T7 | 期待どおり Dynamo に user/agent の行が保存され、HTTP 200 を返す | ユニットテスト：pytest で DynamoDB をモック（moto）し、`/chat` のハンドラを呼んで期待出力確認 | body: `{"message":"今日はつらい"}` | T7,T3,T6 | 12h |
| T9 | Lambda: /history 実装（取得・削除） | - GET /history?limit=20 実装<br>- DELETE /history/{sessionId} 実装 | T6,T7 | 指定ユーザーの過去会話が取得／削除できる | GET → 返却 JSON の schema 確認、DELETE → DynamoDB 上の対象 sessionId レコードが消えることを確認 | userId: `test-user-1` | T6,T7 | 8h |
| T10 | Agent のプロンプト設計（モチベーション強化） | - System prompt 作成（トーン・禁止事項明記）<br>- 応答テンプレート定義（褒め＋具体アクション3つ） | T3 | プロンプトを変更して Agent の応答が期待トーンになること | PoC で複数入力を与え、応答トーン（例: "応援", "提案"）が守られているかを確認 | 入力例: `面接がうまくいくか不安です` | T3 | 6h |
| T11 | 履歴参照による応答最適化実装 | - Lambda で直近 N 件履歴を Agent プロンプトに含める<br>- 履歴フィルタ（直近6件等） | T6,T8,T10 | Agent が過去の会話参照をして一貫性ある応答を返す | 会話を数ターン行った後、前発言を参照した応答が返っているかを確認（例：前回の目標を覚えている） | シーケンス: 1) `今日はランニング` 2) 次回入力で参照されるか確認 | T8,T10 | 8h |
| T12 | フロントエンド実装（認証連携） | - React でログイン/登録 UI 実装<br>- Cognito と連携して JWT を取得 | T4,T5 | ブラウザでサインアップ→ログイン→JWT が取得され UI に反映される | 実際に UI からログインし、Console（DevTools）で token があることを確認 | testuser@example.com | T4,T5 | 12h |
| T13 | フロントエンド実装（チャット画面） | - チャット履歴表示、入力フォーム、送信機能実装<br>- 履歴選択で過去会話を復元 | T12,T9,T8 | 送信→API呼び出し→応答表示の一連が動くこと | UI からメッセージ送信し、画面に Assistant 応答が表示されるまでを確認（3秒以内目標） | `今日は疲れた` | T12,T8,T9 | 16h |
| T14 | E2E テスト作成（結合） | - 認証→チャット→履歴取得→削除 の流れを自動化（Cypress / Playwright 等） | T12,T13,T7,T9 | E2E テストがグリーンで、主要機能の流れが検証できること | E2E 実行：サインアップ→ログイン→送信→応答表示→履歴取得→削除 を自動で確認 | same as above | T12,T13,T9 | 8h |
| T15 | セキュリティテスト（脆弱性） | - JWT の無効化テスト、権限分離テスト<br>- Forbidden 条件を確認 | T2,T5,T7 | 不正トークンで API にアクセスできない、Lambda が過剰な権限を持たない | Authorization を削った curl 実行で 401 を受けることを確認 | invalid token | T2,T5,T7 | 6h |
| T16 | モニタリング & ロギング設定 | - CloudWatch Logs 集約、アラーム設定（エラー閾値）<br>- Lambda のメトリクス、API Gateway の 5xx 監視 | T7,T8 | エラー時にアラートが上がること | 意図的に error を発生させ、CloudWatch アラームがトリガされるか確認 | シミュレーション例：Lambda で例外を投げる | T7,T8 | 4h |
| T17 | コストガードレール設定 | - API Gateway スロットリング設定<br>- Bedrock 呼出しのレート制御（Lambda 側） | T7,T8 | 高負荷時にスロットリングが働く | ロードツールで同時接続を模擬しスロットリングが働くか確認 | 負荷テスト時 | T13 | 6h |
| T18 | CI/CD（デプロイ自動化） | - GitHub Actions / CodePipeline で CDK デプロイ・Lambda パッケージ自動化 | T1,T10,T11 | PR マージで自動デプロイが走る | PR を作成→マージ→ステージングにデプロイされることを確認 | sample PR | T1 | 8h |
| T19 | 負荷テスト（最小実運用確認） | - 同時 1000 ユーザー想定でのスモークテスト | T13,T14,T17 | 目標同時接続で処理が大きく破綻しないこと（エラー率低） | 負荷ツールで同時接続を模擬し、エラー率 < 5% を目標に確認 | 1000 concurrent simulated | T17,T13 | 12h |
| T20 | リリース準備 & 手順書 | - ドメイン設定、ACM 証明書適用<br>- 運用手順書・ロールバック手順作成 | すべて（ステージング完了） | 本番移行手順がドキュメント化されている | 手順書に従ってステージング→本番切替のドライランを実施 | - | 全タスク完了 | 6h |

---

## テストに関する共通ルール（必須）
1. **「テストは必ず失敗→修正→再テスト」** のサイクルを守ること。  
2. **ユニットテスト**（pytest + moto 等）で小さなロジックを検証する。Lambda のビジネスロジックは必ずユニットテストを用意する。  
3. **結合テスト / E2E** は UI（Playwright/Cypress）を使って自動化する。手動テストだけに頼らない。  
4. **ログ確認**：CloudWatch のログは常に確認可能にし、エラー発生時に Slack/メールへ通知する。  
5. **セキュリティ検証**：認可/認証が正しく機能していることを明示的にテストする（無効トークンや他ユーザーアクセス試験）。  
6. **テストデータ** は環境ごとに分け（`staging_` prefix 等）本番データと混ざらないようにする。  

---

## 具体的なテストコマンド例（すぐ使える）
- **Cognito でログインして id_token を取得（例）**  
  - ブラウザの Hosted UI を使うのが簡単。カスタム UI の場合は Authorization Code フローを実装してトークン取得。  
- **/chat を curl で叩く（例）**  
  ```bash
  curl -X POST "https://<api-domain>/chat" \
    -H "Authorization: Bearer <ID_TOKEN>" \
    -H "Content-Type: application/json" \
    -d '{"message":"今日はちょっと落ち込んでる"}'

期待: HTTP 200、JSON に assistant フィールドがあり空でない文字列が返る。

DynamoDB に保存されているか確認（AWS CLI）

aws dynamodb query \
  --table-name ChatHistoryTable \
  --key-condition-expression "userId = :u" \
  --expression-attribute-values '{":u":{"S":"test-user-1"}}'

pytest 実行例（Lambda ユニット）

pytest tests/test_chat_lambda.py -q

E2E（Playwright）実行例

npx playwright test tests/e2e/chat.spec.ts



---

推奨の順序（実行順）

1. T1 → T2 → T4 → T5 → T6 → T3（Bedrock PoC）


2. T7 → T8 → T9（API+Lambda）


3. T12 → T13（フロント実装） → T14（E2E）


4. T10 → T11（Agent チューニングと履歴連携）


5. T15 → T16（セキュリティ・モニタリング）


6. T17 → T19（コスト制御・負荷）


7. T18 → T20（CI/CD 本番準備・リリース手順）




---

最後に（注意点）

「テストしながら丁寧に」は時間がかかりますが、本番での致命的ミスを防げます。

各タスク完了時に 必ず担当者がチェックリスト（受け入れ基準）にチェックを入れてから次へ進んでください。

さらに詳細なテストケース（例えばユニットテストの具体的な期待値や Playwright のシナリオ脚本）も必要なら作成します。ご希望あれば続けて作ります。



---






