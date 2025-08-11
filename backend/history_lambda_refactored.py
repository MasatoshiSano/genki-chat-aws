import json
import boto3
from datetime import datetime
import logging
from collections import defaultdict
from common import (
    setup_logger,
    ResponseBuilder,
    RequestValidator,
    DatabaseHelper,
    HistoryHelper,
    HISTORY_TABLE
)

# ログ設定
logger = setup_logger(__name__)

# AWS サービス初期化
dynamodb = boto3.resource('dynamodb')

# ヘルパー初期化
db_helper = DatabaseHelper(dynamodb)
history_helper = HistoryHelper(db_helper, HISTORY_TABLE)

def lambda_handler(event, context):
    """
    チャット履歴を管理するLambda関数（リファクタリング版）
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # OPTIONSリクエストの処理
        if event.get('httpMethod') == 'OPTIONS':
            return ResponseBuilder.options()
        
        # 認証情報検証
        try:
            auth_info = RequestValidator.validate_auth_token(event)
            user_id = auth_info['user_id']
        except ValueError as e:
            logger.error(f"Authentication failed: {str(e)}")
            return ResponseBuilder.error(str(e), 401)
        
        http_method = event.get('httpMethod', 'GET')
        query_params = event.get('queryStringParameters') or {}
        
        logger.info(f"Processing {http_method} request for user: {user_id}")
        
        if http_method == 'GET':
            # 履歴取得
            return handle_get_history(user_id)
        
        elif http_method == 'DELETE':
            # 履歴削除
            session_id = query_params.get('sessionId')
            return handle_delete_history(user_id, session_id)
        
        else:
            return ResponseBuilder.error(f'サポートされていないHTTPメソッドです: {http_method}', 405)
    
    except Exception as e:
        logger.error(f"Unexpected error in history lambda: {str(e)}", exc_info=True)
        return ResponseBuilder.error('内部サーバーエラーが発生しました', 500, str(e))

def handle_get_history(user_id: str):
    """履歴取得処理"""
    try:
        logger.info(f"Getting history for user: {user_id}")
        
        # ユーザーの全メッセージを取得
        messages = history_helper.get_user_history(user_id)
        
        if messages is None:
            logger.error("Failed to retrieve user history")
            return ResponseBuilder.error('履歴の取得に失敗しました', 500)
        
        if not messages:
            logger.info("No history found for user")
            return ResponseBuilder.success({'conversations': []})
        
        # セッション別に会話を整理
        conversations = organize_conversations(messages)
        
        logger.info(f"Successfully processed {len(conversations)} conversations")
        
        return ResponseBuilder.success({
            'conversations': conversations,
            'totalCount': len(conversations)
        })
        
    except Exception as e:
        logger.error(f"Error in get history: {str(e)}")
        return ResponseBuilder.error('履歴取得中にエラーが発生しました', 500, str(e))

def handle_delete_history(user_id: str, session_id: str = None):
    """履歴削除処理"""
    try:
        if session_id:
            # 特定セッションの削除
            logger.info(f"Deleting session {session_id} for user {user_id}")
            
            success = history_helper.delete_session(user_id, session_id)
            
            if not success:
                return ResponseBuilder.error('セッションの削除に失敗しました', 500)
            
            logger.info(f"Successfully deleted session: {session_id}")
            return ResponseBuilder.success({'message': 'セッションが削除されました'})
            
        else:
            # 全履歴の削除
            logger.info(f"Deleting all history for user {user_id}")
            
            success = history_helper.delete_user_history(user_id)
            
            if not success:
                return ResponseBuilder.error('履歴の削除に失敗しました', 500)
            
            logger.info(f"Successfully deleted all history for user: {user_id}")
            return ResponseBuilder.success({'message': '全ての履歴が削除されました'})
            
    except Exception as e:
        logger.error(f"Error in delete history: {str(e)}")
        return ResponseBuilder.error('履歴削除中にエラーが発生しました', 500, str(e))

def organize_conversations(messages):
    """
    メッセージをセッション別の会話に整理
    """
    try:
        # セッション別にメッセージをグループ化
        sessions = defaultdict(list)
        
        for message in messages:
            session_id = message.get('sessionId')
            if session_id:
                sessions[session_id].append(message)
        
        conversations = []
        
        for session_id, session_messages in sessions.items():
            # メッセージを時系列でソート
            session_messages.sort(key=lambda x: x.get('timestamp', ''))
            
            # 最初のユーザーメッセージを取得
            first_user_message = None
            for msg in session_messages:
                if msg.get('role') == 'user':
                    first_user_message = msg.get('content', '')
                    break
            
            # 会話の統計情報を計算
            user_messages = [msg for msg in session_messages if msg.get('role') == 'user']
            assistant_messages = [msg for msg in session_messages if msg.get('role') == 'assistant']
            
            # 最新のタイムスタンプを取得
            latest_timestamp = max(
                (msg.get('timestamp', '') for msg in session_messages),
                default=datetime.utcnow().isoformat()
            )
            
            # 最初のタイムスタンプを取得
            earliest_timestamp = min(
                (msg.get('timestamp', '') for msg in session_messages),
                default=latest_timestamp
            )
            
            conversation = {
                'sessionId': session_id,
                'firstMessage': first_user_message or '新しい会話',
                'messageCount': len(session_messages),
                'userMessageCount': len(user_messages),
                'assistantMessageCount': len(assistant_messages),
                'createdAt': earliest_timestamp,
                'updatedAt': latest_timestamp,
                'preview': create_conversation_preview(session_messages)
            }
            
            conversations.append(conversation)
        
        # 最新順でソート
        conversations.sort(key=lambda x: x.get('updatedAt', ''), reverse=True)
        
        logger.info(f"Organized {len(conversations)} conversations from {len(messages)} messages")
        
        return conversations
        
    except Exception as e:
        logger.error(f"Error organizing conversations: {str(e)}")
        return []

def create_conversation_preview(messages):
    """
    会話のプレビューテキストを作成
    """
    try:
        # 最新のユーザーメッセージとAIの応答を取得
        recent_messages = sorted(messages, key=lambda x: x.get('timestamp', ''), reverse=True)[:4]
        
        preview_parts = []
        for msg in reversed(recent_messages):  # 時系列順に戻す
            role = msg.get('role', '')
            content = msg.get('content', '')
            
            if content:
                if role == 'user':
                    preview_parts.append(f"👤: {content[:30]}")
                elif role == 'assistant':
                    preview_parts.append(f"🤖: {content[:30]}")
        
        preview = " | ".join(preview_parts)
        
        # 長さ制限
        if len(preview) > 150:
            preview = preview[:147] + "..."
        
        return preview
        
    except Exception as e:
        logger.error(f"Error creating preview: {str(e)}")
        return "会話プレビューを作成できませんでした"

if __name__ == "__main__":
    # ローカルテスト用
    test_event_get = {
        "httpMethod": "GET",
        "headers": {
            "Authorization": "Bearer test-token"
        }
    }
    
    test_event_delete = {
        "httpMethod": "DELETE",
        "headers": {
            "Authorization": "Bearer test-token"
        },
        "queryStringParameters": {
            "sessionId": "test-session-123"
        }
    }
    
    print("Testing GET:")
    result = lambda_handler(test_event_get, None)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\nTesting DELETE:")
    result = lambda_handler(test_event_delete, None)
    print(json.dumps(result, indent=2, ensure_ascii=False))