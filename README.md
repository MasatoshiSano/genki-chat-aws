# 元気をくれるチャットアプリ

AWS Bedrock Agentを使用したモチベーション強化型チャットアプリケーション

## プロジェクト構成

```
.
├── backend/           # Lambda関数とAPI実装
├── frontend/          # React SPA
├── infrastructure/    # AWS CDK/CloudFormationテンプレート
├── tests/            # テストファイル
├── docs/             # ドキュメント
├── requirements.md    # 要件定義
├── design.md         # 設計書
└── tasks.md          # タスク分解
```

## 使用AWSサービス

- Amazon Bedrock (Agent)
- Amazon Cognito
- Amazon API Gateway
- AWS Lambda
- Amazon DynamoDB
- Amazon S3
- Amazon CloudFront

## 開発手順

タスク分解（tasks.md）に従って段階的に実装を進めます。

1. IAM基盤設定
2. Bedrock Agent作成
3. データベース・API構築
4. フロントエンド実装
5. テスト・運用設定

## セットアップ

詳細は各ディレクトリのREADMEを参照してください。