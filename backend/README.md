# Lambda関数デプロイ手順

## 概要
Lambda関数をBedrock Agentの呼び出しのみに最適化しました。

## デプロイ前の設定

### 1. Bedrock Agent情報の設定
`chat_lambda.py`の21-22行目を更新：

```python
AGENT_ID = 'your-actual-agent-id'  # AWSコンソールから取得
AGENT_ALIAS_ID = 'your-actual-agent-alias-id'  # AWSコンソールから取得
```

### 2. エージェント情報の取得方法
1. AWSコンソール > Amazon Bedrock > Agents
2. 作成したエージェントを選択
3. Agent ID をコピー
4. Aliases タブでAlias ID をコピー

## デプロイコマンド

```bash
# chat_lambda.py をZIPに圧縮
zip -r chat_lambda_optimized.zip chat_lambda.py

# Lambda関数を更新
aws lambda update-function-code \
  --function-name GenkiChatFunction \
  --zip-file fileb://chat_lambda_optimized.zip

# history_lambda.py をZIPに圧縮（変更なし）
zip -r history_lambda_optimized.zip history_lambda.py

# Lambda関数を更新
aws lambda update-function-code \
  --function-name GenkiHistoryFunction \
  --zip-file fileb://history_lambda_optimized.zip
```

## 最適化内容

### chat_lambda.py の変更点
- ❌ 削除: Claude 3 Haiku直接呼び出し
- ❌ 削除: 複雑な感情分析機能
- ❌ 削除: 会話文脈構築機能
- ❌ 削除: 応答後処理機能
- ✅ 追加: Bedrock Agent呼び出しのみ
- ✅ 追加: 適切なエラーハンドリング
- ✅ 追加: ストリーミングレスポンス処理

### history_lambda.py
- 変更なし（既にシンプル）

## メリット
1. **エージェント設定に依存**: プロンプトやモデル設定はエージェント側で管理
2. **コードサイズ削減**: 482行 → 89行（81%削減）
3. **メンテナンス性向上**: ロジックがエージェント設定に集約
4. **パフォーマンス向上**: 不要な処理を削除