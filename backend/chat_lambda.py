import json
import boto3
import uuid
from datetime import datetime
import logging

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS サービス初期化
dynamodb = boto3.resource('dynamodb')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

# テーブル名
USER_TABLE = 'GenkiChatUserTable'
HISTORY_TABLE = 'GenkiChatHistoryTable'

# Bedrock Agent設定
AGENT_ID = 'PLMASWUNAG'
AGENT_ALIAS_ID = 'XWFWAS7SOV'

def lambda_handler(event, context):
    """
    チャットメッセージを処理するLambda関数
    """
    try:
        # CORS対応
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Content-Type': 'application/json'
        }
        
        # OPTIONSリクエストの処理
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'OK'})
            }
        
        # リクエストボディのパース
        if 'body' not in event or not event['body']:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'リクエストボディが必要です'})
            }
        
        body = json.loads(event['body'])
        user_message = body.get('message', '').strip()
        existing_session_id = body.get('sessionId')  # 既存セッションID（継続用）
        
        if not user_message:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'メッセージが空です'})
            }
        
        # ユーザーID取得（JWT Claimから）
        user_id = get_user_id_from_token(event)
        if not user_id:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({'error': '認証が必要です'})
            }
        
        # セッションID処理（継続または新規生成）
        if existing_session_id:
            # 既存セッションの継続
            session_id = existing_session_id
            logger.info(f"継続セッション: {session_id}")
        else:
            # 新規セッション生成
            session_id = str(uuid.uuid4())
            logger.info(f"新規セッション: {session_id}")
            
        timestamp = datetime.utcnow().isoformat()
        
        # ユーザーメッセージをDynamoDBに保存
        save_message(user_id, session_id, timestamp, 'user', user_message)
        
        # Bedrock Agentを呼び出し（セッション継続あり）
        agent_response = invoke_bedrock_agent(user_message, session_id)
        
        # Agentの応答をDynamoDBに保存
        agent_timestamp = datetime.utcnow().isoformat()
        save_message(user_id, session_id, agent_timestamp, 'assistant', agent_response)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'reply': agent_response,
                'sessionId': session_id
            })
        }
        
    except Exception as e:
        logger.error(f"エラー: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': '内部サーバーエラーが発生しました'})
        }

def get_user_id_from_token(event):
    """
    JWTトークンからユーザーIDを取得
    """
    try:
        # Authorizationヘッダーからトークンを取得
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization') or headers.get('authorization')
        
        if not auth_header:
            return None
            
        # "Bearer "プレフィックスを削除
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        else:
            token = auth_header
            
        # JWTトークンをデコード（ペイロード部分のみ）
        import base64
        parts = token.split('.')
        if len(parts) != 3:
            return None
            
        # ペイロードをデコード
        payload = parts[1]
        # Base64デコードのためのパディング調整
        missing_padding = len(payload) % 4
        if missing_padding:
            payload += '=' * (4 - missing_padding)
            
        decoded = base64.b64decode(payload)
        claims = json.loads(decoded)
        
        # CognitoのsubフィールドからユーザーIDを取得
        return claims.get('sub')
        
    except Exception as e:
        logger.error(f"トークン解析エラー: {str(e)}")
        return "demo-user-123"  # フォールバック

def save_message(user_id, session_id, timestamp, role, message):
    """
    メッセージをDynamoDBに保存
    """
    table = dynamodb.Table(HISTORY_TABLE)
    
    table.put_item(
        Item={
            'userId': user_id,
            'timestamp': timestamp,
            'sessionId': session_id,
            'role': role,
            'message': message
        }
    )

def invoke_bedrock_agent(message, session_id):
    """
    Bedrock Agentを呼び出して応答を取得
    セッションIDにより会話の継続性を保持
    """
    try:
        logger.info(f"Invoking Bedrock Agent - AgentID: {AGENT_ID}, AliasID: {AGENT_ALIAS_ID}, SessionID: {session_id}")
        logger.info(f"User message: {message}")
        
        # Bedrock Agentを呼び出し（同一セッションIDで継続）
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=message,
            enableTrace=True  # デバッグのためにtrueに変更
        )
        
        logger.info(f"Bedrock Agent response received: {type(response)}")
        
        # ストリーミングレスポンスを処理
        completion = ""
        event_count = 0
        
        try:
            for event in response.get("completion", []):
                event_count += 1
                logger.info(f"Processing event {event_count}: {list(event.keys())}")
                
                if 'chunk' in event:
                    chunk = event["chunk"]
                    logger.info(f"Chunk keys: {list(chunk.keys())}")
                    if 'bytes' in chunk:
                        chunk_text = chunk["bytes"].decode('utf-8')
                        completion += chunk_text
                        logger.info(f"Added chunk: {chunk_text}")
                elif 'trace' in event:
                    logger.info(f"Trace event: {event['trace']}")
                    
        except Exception as e:
            logger.error(f"ストリーミングレスポンス処理エラー: {str(e)}")
            logger.error(f"Response structure: {response}")
        
        logger.info(f"Total events processed: {event_count}")
        logger.info(f"Final completion length: {len(completion)}")
        logger.info(f"Final completion content: {completion}")
        
        if completion.strip():
            return completion.strip()
        
        # 空の応答の場合のフォールバック
        logger.warning("Empty completion received from agent")
        return "申し訳ありません。エージェントから応答を受信できませんでした。もう一度お試しください。"
        
    except Exception as e:
        logger.error(f"Bedrock Agent呼び出しエラー: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {e}")
        
        # エラーの詳細をユーザーに返す
        return f"エージェントエラー: {str(e)}。エージェントIDやエイリアスIDを確認してください。"

