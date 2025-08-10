# 元気チャットアプリ デプロイ状況

## 作成済みリソース

### 1. IAM
- **Role**: `GenkiChatLambdaRole`
  - ARN: `arn:aws:iam::863646532781:role/GenkiChatLambdaRole`
  - 権限: DynamoDB、Bedrock、CloudWatch Logs

### 2. DynamoDB
- **UserTable**: `GenkiChatUserTable`
  - Key: userId (String)
- **ChatHistoryTable**: `GenkiChatHistoryTable`
  - Partition Key: userId (String)  
  - Sort Key: timestamp (String)

### 3. Cognito
- **User Pool**: `GenkiChatUserPool`
  - Pool ID: `ap-northeast-1_7CLrXZQiB`
- **App Client**: `GenkiChatClient`
  - Client ID: `7af0tuk3i9r0lir5uhqduiep04`
  - Client Secret: `1t87e432carkn9lg6i4tjhmj8brkf7mp1vj8phqhkuljpqtqtnia`

### 4. S3 + CloudFront
- **S3 Bucket**: `genki-chat-frontend-1754637038`
  - Website URL: `http://genki-chat-frontend-1754637038.s3-website-ap-northeast-1.amazonaws.com`
- **CloudFront**: `d13mazydxzmnab.cloudfront.net`
  - Distribution ID: `E381PU3P4AFTM6`

### 5. API Gateway + Lambda
- **API Gateway**: `GenkiChatAPI`
  - API ID: `i6zlozpitk`
  - Base URL: `https://i6zlozpitk.execute-api.ap-northeast-1.amazonaws.com/prod`
  - Endpoints:
    - POST `/chat` → `GenkiChatFunction`
    - GET `/history` → `GenkiHistoryFunction`
- **Lambda Functions**:
  - `GenkiChatFunction`: チャット処理 (Bedrock Agent連携済み)
  - `GenkiHistoryFunction`: 履歴管理

### 6. Bedrock Agent ✅
- **Agent ID**: `PLMASWNAG`
- **Agent名**: `GenkiChatAgent`
- **モデル**: Claude 3 Haiku (us-east-1)
- **権限**: Lambda関数に`bedrock:InvokeAgent`権限を付与済み

## テスト用URL

### フロントエンド
- S3: http://genki-chat-frontend-1754637038.s3-website-ap-northeast-1.amazonaws.com
- CloudFront: https://d13mazydxzmnab.cloudfront.net (配布待ち)

### API エンドポイント
- Chat: `https://i6zlozpitk.execute-api.ap-northeast-1.amazonaws.com/prod/chat`
- History: `https://i6zlozpitk.execute-api.ap-northeast-1.amazonaws.com/prod/history`

## ✅ 構築完了！

### 動作確認済み機能
- ✅ フロントエンド (S3 + CloudFront)
- ✅ API Gateway + Lambda
- ✅ DynamoDB保存
- ✅ Bedrock Agent連携 (Agent ID: PLMASWNAG)

### 今後の拡張
- Cognitoオーソライザー設定 (認証機能)
- 履歴表示機能の実装
- エラーハンドリング強化

## セキュリティ・本番化対応 (今後)

- Cognitoオーソライザー設定
- CORS設定の厳密化
- CloudWatch監視・アラート
- SSL証明書(ACM)
- カスタムドメイン