import json
import boto3
from datetime import datetime
import logging

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS サービス初期化
dynamodb = boto3.resource('dynamodb')

# テーブル名
HISTORY_TABLE = 'GenkiChatHistoryTable'

def lambda_handler(event, context):
    """
    チャット履歴を管理するLambda関数
    """
    try:
        # CORS対応
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, DELETE, OPTIONS',
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
        
        # ユーザーID取得
        user_id = get_user_id_from_token(event)
        if not user_id:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({'error': '認証が必要です'})
            }
        
        http_method = event.get('httpMethod')
        
        if http_method == 'GET':
            # 履歴一覧取得
            return get_history_list(user_id, headers, event)
        
        elif http_method == 'DELETE':
            # 特定セッションの履歴削除
            return delete_session_history(user_id, headers, event)
        
        else:
            return {
                'statusCode': 405,
                'headers': headers,
                'body': json.dumps({'error': 'サポートされていないHTTPメソッドです'})
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

def get_history_list(user_id, headers, event):
    """
    ユーザーのチャット履歴一覧を取得
    """
    try:
        # クエリパラメータから制限数を取得
        query_params = event.get('queryStringParameters') or {}
        limit = int(query_params.get('limit', 20))
        
        table = dynamodb.Table(HISTORY_TABLE)
        
        # パスパラメータにsessionIdがある場合は特定セッションの詳細を取得
        path_params = event.get('pathParameters') or {}
        session_id = path_params.get('sessionId')
        
        if session_id:
            # 特定セッションの詳細履歴
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_id),
                FilterExpression=boto3.dynamodb.conditions.Attr('sessionId').eq(session_id),
                ScanIndexForward=True  # 昇順（時系列順）
            )
            
            items = response.get('Items', [])
            messages = []
            
            for item in items:
                messages.append({
                    'timestamp': item['timestamp'],
                    'role': item['role'],
                    'message': item['message']
                })
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'sessionId': session_id,
                    'messages': messages
                })
            }
        
        else:
            # 履歴一覧（セッション別にグループ化）
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_id),
                ScanIndexForward=False,  # 降順（新しい順）
                Limit=limit * 3  # セッション数の見積もり
            )
            
            items = response.get('Items', [])
            
            # セッション別にグループ化
            sessions = {}
            for item in items:
                session_id = item['sessionId']
                if session_id not in sessions:
                    sessions[session_id] = {
                        'sessionId': session_id,
                        'date': item['timestamp'],
                        'preview': '',
                        'messages': []
                    }
                
                sessions[session_id]['messages'].append({
                    'timestamp': item['timestamp'],
                    'role': item['role'],
                    'message': item['message']
                })
            
            # プレビュー作成（最初のユーザーメッセージ）
            session_list = []
            for session_id, session_data in sessions.items():
                # 最初のユーザーメッセージを探す
                for msg in session_data['messages']:
                    if msg['role'] == 'user':
                        preview = msg['message'][:50]
                        if len(msg['message']) > 50:
                            preview += '...'
                        session_data['preview'] = preview
                        break
                
                # messagesフィールドを除いてレスポンスに追加
                session_list.append({
                    'sessionId': session_data['sessionId'],
                    'date': session_data['date'],
                    'preview': session_data['preview']
                })
            
            # 日時順でソート
            session_list.sort(key=lambda x: x['date'], reverse=True)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(session_list[:limit])
            }
        
    except Exception as e:
        logger.error(f"履歴取得エラー: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': '履歴取得に失敗しました'})
        }

def delete_session_history(user_id, headers, event):
    """
    特定セッションの履歴を削除
    """
    try:
        path_params = event.get('pathParameters') or {}
        session_id = path_params.get('sessionId')
        
        if not session_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'セッションIDが必要です'})
            }
        
        table = dynamodb.Table(HISTORY_TABLE)
        
        # 該当セッションのすべてのメッセージを取得
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_id),
            FilterExpression=boto3.dynamodb.conditions.Attr('sessionId').eq(session_id)
        )
        
        items = response.get('Items', [])
        
        if not items:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'セッションが見つかりません'})
            }
        
        # バッチで削除
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(
                    Key={
                        'userId': item['userId'],
                        'timestamp': item['timestamp']
                    }
                )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'status': 'success',
                'message': f'セッション {session_id} の履歴を削除しました',
                'deletedCount': len(items)
            })
        }
        
    except Exception as e:
        logger.error(f"履歴削除エラー: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': '履歴削除に失敗しました'})
        }