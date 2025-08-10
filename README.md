# 🌟 Genki Chat - AWS Bedrock Agent Chat Application

日本語対応のインテリジェントチャットアプリケーション。AWS Bedrock Agentsを活用し、ユーザープロフィールに基づくパーソナライズされた会話を提供します。

## ✨ 主要機能

- 🤖 **AI チャット**: AWS Bedrock Agent による高品質な日本語対話
- 👤 **プロフィール設定**: 年齢・職業・性別に基づく会話カスタマイズ
- 📱 **レスポンシブUI**: ダーク/ライトモード、モバイル対応
- 💾 **履歴管理**: セッション別チャット履歴、継続会話
- 🔐 **セキュア**: Amazon Cognito認証、データ暗号化

## 🚀 クイックスタート

### アクセス
**本番URL**: https://genki-chat-frontend-1754637038.s3.amazonaws.com/

1. アカウント作成・ログイン
2. プロフィール設定（オプション）
3. チャット開始

## 📁 プロジェクト構造

```
aws-agents/
├── 📄 README.md              # このファイル
├── 📄 CLAUDE.md              # 詳細技術文書
├── 📂 frontend/              # フロントエンドアプリケーション
│   ├── 🏠 index.html         # ログイン画面
│   ├── 💬 chat.html          # メインチャット
│   ├── 📚 history.html       # 履歴管理
│   ├── 👤 profile.html       # プロフィール設定
│   ├── 🎨 styles.css         # スタイル（テーマ対応）
│   ├── 🧩 components.js      # 再利用コンポーネント
│   └── 🔐 auth.js           # 認証ライブラリ
├── 📂 backend/               # Lambda Functions
│   ├── 🤖 chat_lambda_clean.py    # チャット処理
│   ├── 📖 history_lambda.py       # 履歴管理
│   └── 👤 profile_lambda.py       # プロフィール管理
├── 📂 docs/                  # ドキュメント
├── 📂 infrastructure/        # AWS設定ファイル
└── 📂 tests/                 # テスト（今後）
```

## 🏗 AWS構成

### 主要サービス
- 🤖 **Amazon Bedrock Agent** - AI対話エンジン
- 🔐 **Amazon Cognito** - ユーザー認証
- 🌐 **API Gateway** - RESTful API
- ⚡ **AWS Lambda** - サーバーレス実行環境
- 🗄️ **Amazon DynamoDB** - NoSQLデータベース
- 📦 **Amazon S3** - 静的ウェブサイトホスティング

### リソース詳細
- **S3 Bucket**: `genki-chat-frontend-1754637038`
- **API Gateway**: `i6zlozpitk.execute-api.ap-northeast-1.amazonaws.com`
- **Cognito Pool**: `ap-northeast-1_7CLrXZQiB`
- **Bedrock Agent**: `PLMASWUNAG` (Alias: `XWFWAS7SOV`)

## 🛠 セットアップ手順

### 1. 前提条件
```bash
# AWS CLI設定
aws configure
# Node.js 18+ (ローカル開発の場合)
node --version
```

### 2. 環境構築
詳細な手順は **CLAUDE.md** を参照してください。

#### 基本リソース作成
```bash
# DynamoDB テーブル
aws dynamodb create-table --table-name GenkiChatUserTable ...
aws dynamodb create-table --table-name GenkiChatHistoryTable ...

# Lambda Functions
cd backend
aws lambda create-function --function-name GenkiChatFunction ...
```

### 3. デプロイ
```bash
# フロントエンド
cd frontend
aws s3 sync . s3://your-bucket-name

# バックエンド
cd backend
zip function.zip *.py
aws lambda update-function-code --function-name GenkiChatFunction --zip-file fileb://function.zip
```

## 📊 システム特徴

### パーソナライズ機能
ユーザープロフィール（年齢・職業・性別）に基づいて、AIが適切な話し方・内容で応答:

```
【ユーザー情報】
ユーザーの名前: 田中さん
年齢層: 30代
職業: エンジニア
性別: 男性

【応答指示】
適度な長さ（2-4行）で応答してください。
ユーザーの属性に適した話し方や内容で応答してください。
```

### セッション管理
- 継続的な会話記憶
- 履歴からの会話再開
- ユーザー別データ分離

## 💰 コスト見積もり

### 月額（100アクティブユーザー想定）
- **Lambda**: $3-8
- **DynamoDB**: $2-5  
- **API Gateway**: $1-3
- **Bedrock**: $15-60
- **その他**: $2-5

**合計: $23-81/月**

## 🔒 セキュリティ

### 実装済み対策
- ✅ Cognito JWT認証
- ✅ HTTPS強制
- ✅ CORS設定
- ✅ IAM最小権限
- ✅ ユーザーデータ分離

## 📞 サポート・ドキュメント

- 📋 **詳細仕様**: `CLAUDE.md`
- 🚨 **トラブルシューティング**: ブラウザF12でコンソール確認
- 🐛 **バグレポート**: GitHub Issues

---

**🚀 Happy Chatting with Genki Chat!**