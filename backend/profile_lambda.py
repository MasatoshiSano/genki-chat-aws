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
USER_TABLE = 'GenkiChatUserTable'

def lambda_handler(event, context):
    """
    ユーザープロフィールを管理するLambda関数
    """
    try:
        # CORS対応
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
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
            # プロフィール取得
            return get_user_profile(user_id, headers)
        
        elif http_method == 'POST':
            # プロフィール保存
            return save_user_profile(user_id, headers, event)
        
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

def get_user_profile(user_id, headers):
    """
    ユーザープロフィールを取得
    """
    try:
        table = dynamodb.Table(USER_TABLE)
        
        # ユーザープロフィールを取得
        response = table.get_item(
            Key={'userId': user_id}
        )
        
        if 'Item' in response:
            profile = response['Item']
            # DynamoDBの内部フィールドを除去
            profile_data = {
                'userName': profile.get('userName', ''),
                'age': profile.get('age', ''),
                'occupation': profile.get('occupation', ''),
                'gender': profile.get('gender', ''),
                'responseLength': profile.get('responseLength', 'medium'),
                'updatedAt': profile.get('updatedAt', '')
            }
        else:
            # プロフィールが存在しない場合はデフォルト値
            profile_data = {
                'userName': '',
                'age': '',
                'occupation': '',
                'gender': '',
                'responseLength': 'medium',
                'updatedAt': ''
            }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(profile_data)
        }
        
    except Exception as e:
        logger.error(f"プロフィール取得エラー: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'プロフィール取得に失敗しました'})
        }

def save_user_profile(user_id, headers, event):
    """
    ユーザープロフィールを保存
    """
    try:
        if 'body' not in event or not event['body']:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'リクエストボディが必要です'})
            }
        
        body = json.loads(event['body'])
        logger.info(f"Profile save request: {json.dumps(body)}")
        
        # プロフィールデータを検証・サニタイズ
        profile_data = {
            'userId': user_id,
            'userName': str(body.get('userName', ''))[:50],  # 最大50文字
            'age': str(body.get('age', ''))[:10],  # 年代文字列
            'occupation': str(body.get('occupation', ''))[:50],  # 最大50文字
            'gender': str(body.get('gender', ''))[:10],  # 性別
            'responseLength': body.get('responseLength', 'medium'),  # 応答の長さ
            'updatedAt': datetime.utcnow().isoformat()
        }
        
        # 応答の長さの値を検証
        if profile_data['responseLength'] not in ['short', 'medium', 'long']:
            profile_data['responseLength'] = 'medium'
        
        table = dynamodb.Table(USER_TABLE)
        
        # プロフィールを保存
        table.put_item(Item=profile_data)
        
        logger.info(f"Profile saved for user {user_id}: {profile_data}")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'status': 'success',
                'message': 'プロフィールが保存されました',
                'profile': {
                    'userName': profile_data['userName'],
                    'age': profile_data['age'],
                    'occupation': profile_data['occupation'],
                    'gender': profile_data['gender'],
                    'responseLength': profile_data['responseLength'],
                    'updatedAt': profile_data['updatedAt']
                }
            })
        }
        
    except Exception as e:
        logger.error(f"プロフィール保存エラー: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'プロフィール保存に失敗しました'})
        }