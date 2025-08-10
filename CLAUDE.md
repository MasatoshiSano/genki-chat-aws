# Genki Chat - AWS Bedrock Agent Chat Application

## プロジェクト概要

Genki Chat は AWS Bedrock Agents を活用した日本語チャットアプリケーションです。ユーザーごとのプロフィール設定、チャット履歴管理、セッション継続機能を備えたフルスタックWebアプリケーションです。

## システム構成

### アーキテクチャ図
```
[Frontend (S3)] → [API Gateway] → [Lambda Functions] → [DynamoDB]
                                      ↓
                               [Bedrock Agent]
                                      ↓
                               [Cognito (認証)]
```

## AWS リソース構成

### 1. Frontend (S3 Static Website)
- **S3 Bucket**: `genki-chat-frontend-1754637038`
- **エンドポイント**: `https://genki-chat-frontend-1754637038.s3.amazonaws.com/`
- **ファイル構成**:
  - `index.html` - ログイン画面
  - `chat.html` - メインチャット画面
  - `history.html` - チャット履歴一覧
  - `profile.html` - ユーザープロフィール設定
  - `styles.css` - 共通CSS（ダーク/ライトモード対応）
  - `components.js` - 再利用可能UIコンポーネント
  - `auth.js` - Cognito認証ライブラリ

### 2. API Gateway
- **API ID**: `i6zlozpitk`
- **ステージ**: `prod`
- **エンドポイント**: `https://i6zlozpitk.execute-api.ap-northeast-1.amazonaws.com/prod`

#### API エンドポイント:
- `POST /chat` - チャットメッセージ送信
- `GET /history` - チャット履歴一覧取得
- `GET /history/{sessionId}` - 特定セッション詳細取得
- `DELETE /history/{sessionId}` - セッション削除
- `GET /chat/profile` - ユーザープロフィール取得
- `POST /chat/profile` - ユーザープロフィール保存

### 3. Lambda Functions

#### a) GenkiChatFunction
- **ファイル**: `backend/chat_lambda_clean.py`
- **機能**: チャットメッセージ処理・Bedrock Agent呼び出し
- **主要機能**:
  - セッション管理（継続的な会話）
  - ユーザープロフィール取得
  - Bedrock Agentへのカスタマイズされたメッセージ送信
  - 応答の長さ制御（短め/普通/詳しく）

#### b) GenkiHistoryFunction  
- **ファイル**: `backend/history_lambda.py`
- **機能**: チャット履歴管理
- **主要機能**:
  - 履歴一覧表示（セッション別グループ化）
  - 特定セッションの詳細表示
  - セッション削除（個別・一括）

#### c) GenkiProfileFunction
- **ファイル**: `backend/profile_lambda.py`
- **機能**: ユーザープロフィール管理
- **主要機能**:
  - プロフィール情報の保存・取得
  - ユーザー名、年齢、職業、性別設定
  - 応答長さ設定

### 4. DynamoDB Tables

#### a) GenkiChatUserTable
- **パーティションキー**: `userId` (String)
- **用途**: ユーザープロフィール情報
- **格納データ**:
  - `userName`: 表示名
  - `age`: 年齢層（10代〜60代以上）
  - `occupation`: 職業
  - `gender`: 性別
  - `responseLength`: 応答の長さ（short/medium/long）

#### b) GenkiChatHistoryTable
- **パーティションキー**: `userId` (String)
- **ソートキー**: `timestamp` (String)
- **用途**: チャット履歴保存
- **格納データ**:
  - `sessionId`: セッションID（会話グループ）
  - `role`: 発言者（user/assistant）
  - `message`: メッセージ内容

### 5. Amazon Bedrock Agent
- **Agent ID**: `PLMASWUNAG`
- **Alias ID**: `XWFWAS7SOV`
- **機能**: 日本語での自然な対話
- **カスタマイズ**: ユーザープロフィールに基づく応答調整

### 6. Amazon Cognito
- **User Pool ID**: `ap-northeast-1_7CLrXZQiB`
- **Client ID**: `7af0tuk3i9r0lir5uhqduiep04`
- **機能**: ユーザー認証・JWT トークン発行

### 7. IAM Role
- **Role Name**: `GenkiChatLambdaRole`
- **権限**:
  - `dynamodb:GetItem`, `PutItem`, `Query`, `BatchWriteItem`
  - `bedrock:InvokeAgent`
  - `logs:CreateLogGroup`, `CreateLogStream`, `PutLogEvents`

## 主要機能

### 1. ユーザー認証
- Amazon Cognitoによるサインアップ・ログイン
- JWT トークンベースの認証
- セッション自動復元

### 2. プロフィール設定
- 個人情報設定（名前、年齢、職業、性別）
- 応答スタイル設定（短め/普通/詳しく）
- リアルタイム保存・読み込み

### 3. インテリジェントチャット
- AWS Bedrock Agentによる高品質な日本語対話
- ユーザープロフィールに基づくパーソナライズ
- セッション継続（記憶保持）
- コンテキスト理解

### 4. チャット履歴管理
- セッション別履歴保存
- 過去の会話から継続可能
- 履歴検索・削除機能
- プレビュー表示

### 5. モダンUI/UX
- ダーク/ライトモード切り替え
- レスポンシブデザイン
- ハンバーガーメニュー
- リアルタイム応答

## プロフィールベース会話カスタマイズ

### システムメッセージ生成例:
```
【ユーザー情報】
ユーザーの名前: 田中太郎
年齢層: 30代
職業: エンジニア
性別: 男性

【応答指示】
適度な長さ（2-4行）で応答してください。
ユーザーの属性に適した話し方や内容で応答してください。

【ユーザーメッセージ】
プロジェクトで困っています
```

## セキュリティ機能

### 1. 認証・認可
- Cognito JWTトークン検証
- API Gateway統合認証
- セッションタイムアウト管理

### 2. データ保護
- HTTPS通信の強制
- CORS設定
- APIキー・シークレット保護

### 3. アクセス制御
- ユーザー別データ分離
- IAM最小権限の原則
- リソースベースポリシー

## 開発・デプロイメント

### ディレクトリ構成:
```
aws-agents/
├── frontend/           # フロントエンドファイル
│   ├── index.html
│   ├── chat.html
│   ├── history.html
│   ├── profile.html
│   ├── styles.css
│   ├── components.js
│   └── auth.js
├── backend/            # Lambda関数
│   ├── chat_lambda_clean.py
│   ├── history_lambda.py
│   └── profile_lambda.py
├── infrastructure/     # インフラ設定（今後）
├── docs/              # ドキュメント
└── CLAUDE.md          # このファイル
```

### デプロイメントフロー:
1. **Frontend**: S3への同期デプロイ
2. **Backend**: Lambda関数のZIPアップロード  
3. **API**: API Gateway設定・デプロイ
4. **Database**: DynamoDBテーブル作成

## パフォーマンス・スケーラビリティ

### 現在の設定:
- **Lambda**: 30秒タイムアウト、128MB メモリ
- **DynamoDB**: オンデマンド課金
- **API Gateway**: 10,000 RPS制限
- **S3**: 無制限静的配信

### 最適化ポイント:
- DynamoDB パーティション設計
- Lambda コールドスタート削減
- CloudFront CDN活用（今後）
- 画像・アセット最適化

## 監視・ロギング

### CloudWatch Logs:
- `/aws/lambda/GenkiChatFunction`
- `/aws/lambda/GenkiHistoryFunction`  
- `/aws/lambda/GenkiProfileFunction`
- API Gateway実行ログ

### メトリクス監視:
- Lambda実行時間・エラー率
- DynamoDB読み書きキャパシティ
- API Gateway応答時間
- Bedrock Agent呼び出し数

## トラブルシューティング

### よくある問題:

#### 1. 認証エラー (401)
- Cognitoトークンの期限切れ
- API Gateway CORS設定
- 解決: ページリフレッシュまたは再ログイン

#### 2. セッション継続しない
- sessionId未送信
- DynamoDB書き込みエラー
- 解決: ローカルストレージ確認

#### 3. 履歴表示されない
- API Gateway エンドポイント
- Lambda関数権限
- 解決: CloudWatchログ確認

#### 4. プロフィール保存失敗
- API パス間違い（/profile vs /chat/profile）
- DynamoDB テーブル権限
- 解決: ネットワークタブで確認

## コスト最適化

### 月間想定コスト（100ユーザー）:
- **Lambda**: $2-5（実行時間ベース）
- **DynamoDB**: $1-3（読み書き量ベース） 
- **API Gateway**: $1-2（リクエスト数ベース）
- **Bedrock**: $10-50（使用量ベース）
- **Cognito**: 無料枠内
- **S3**: $1未満（静的サイト）

### 合計: **$15-61/月**

## 今後の拡張予定

### 短期:
- [ ] 削除機能デバッグ修正
- [ ] エラーハンドリング強化
- [ ] UI/UX改善

### 中期:
- [ ] チャット履歴検索機能
- [ ] ファイルアップロード対応
- [ ] 多言語対応（英語）
- [ ] チャットルーム機能

### 長期:
- [ ] 音声入出力対応
- [ ] リアルタイムチャット
- [ ] 企業向けプラン
- [ ] AI アシスタント学習機能

## ライセンス・コンプライアンス

- **AWS利用規約**: 準拠
- **データ保護**: GDPR考慮設計
- **個人情報**: 暗号化保存
- **監査ログ**: CloudTrail記録

---

**更新日**: 2025年8月9日  
**作成者**: Claude Code Assistant  
**バージョン**: v1.0