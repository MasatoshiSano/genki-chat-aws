import json
import boto3
import uuid
from datetime import datetime
import logging
from common import (
    setup_logger,
    ResponseBuilder,
    RequestValidator,
    DatabaseHelper,
    ProfileHelper,
    HistoryHelper,
    USER_TABLE,
    HISTORY_TABLE,
    AGENT_ID,
    AGENT_ALIAS_ID,
    BEDROCK_REGION
)

# ログ設定
logger = setup_logger(__name__)

# AWS サービス初期化
dynamodb = boto3.resource('dynamodb')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=BEDROCK_REGION)

# ヘルパー初期化
db_helper = DatabaseHelper(dynamodb)
profile_helper = ProfileHelper(db_helper, USER_TABLE)
history_helper = HistoryHelper(db_helper, HISTORY_TABLE)

def lambda_handler(event, context):
    """
    チャットメッセージを処理するLambda関数（リファクタリング版）
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # OPTIONSリクエストの処理
        if event.get('httpMethod') == 'OPTIONS':
            return ResponseBuilder.options()
        
        # リクエスト検証
        try:
            body = RequestValidator.validate_body(event)
            auth_info = RequestValidator.validate_auth_token(event)
        except ValueError as e:
            logger.error(f"Request validation failed: {str(e)}")
            return ResponseBuilder.error(str(e), 400)
        
        # 必須フィールド検証
        message = body.get('message')
        session_id = body.get('sessionId')
        
        if not message:
            return ResponseBuilder.error('メッセージが必要です')
        
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Generated new session_id: {session_id}")
        
        user_id = auth_info['user_id']
        logger.info(f"Processing chat for user: {user_id}, session: {session_id}")
        
        # ユーザープロフィール取得
        user_profile = profile_helper.get_user_profile(user_id)
        if user_profile:
            logger.info(f"Found user profile for {user_id}")
        
        # メッセージをプロフィールでカスタマイズ
        customized_message = profile_helper.customize_message_with_profile(message, user_profile)
        
        # ユーザーメッセージを履歴に保存
        if not history_helper.save_message(user_id, session_id, 'user', message):
            logger.error("Failed to save user message to history")
        
        # Bedrock Agent に送信
        try:
            agent_response = invoke_bedrock_agent(customized_message, session_id)
            logger.info("Successfully got response from Bedrock Agent")
        except Exception as e:
            logger.error(f"Bedrock Agent error: {str(e)}")
            return ResponseBuilder.error('AI応答の生成に失敗しました', 500, str(e))
        
        # AIメッセージを履歴に保存
        if not history_helper.save_message(user_id, session_id, 'assistant', agent_response):
            logger.error("Failed to save assistant message to history")
        
        # レスポンス返却
        response_data = {
            'response': agent_response,
            'sessionId': session_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info("Chat processing completed successfully")
        return ResponseBuilder.success(response_data)
        
    except Exception as e:
        logger.error(f"Unexpected error in chat lambda: {str(e)}", exc_info=True)
        return ResponseBuilder.error('内部サーバーエラーが発生しました', 500, str(e))

def invoke_bedrock_agent(message, session_id):
    """
    Bedrock Agent を呼び出してレスポンスを取得
    """
    try:
        logger.info(f"Invoking Bedrock Agent with session: {session_id}")
        
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=message
        )
        
        # ストリーミングレスポンスを処理
        response_text = ""
        event_stream = response.get('completion', {})
        
        for event in event_stream:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    response_text += chunk_text
        
        if not response_text.strip():
            logger.warning("Empty response from Bedrock Agent")
            return "申し訳ありませんが、応答を生成できませんでした。もう一度お試しください。"
        
        logger.info("Successfully processed Bedrock Agent response")
        return response_text.strip()
        
    except Exception as e:
        logger.error(f"Failed to invoke Bedrock Agent: {str(e)}")
        raise Exception(f"Bedrock Agent呼び出しエラー: {str(e)}")

if __name__ == "__main__":
    # ローカルテスト用
    test_event = {
        "httpMethod": "POST",
        "headers": {
            "Authorization": "Bearer test-token"
        },
        "body": json.dumps({
            "message": "こんにちは！",
            "sessionId": "test-session-123"
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2, ensure_ascii=False))