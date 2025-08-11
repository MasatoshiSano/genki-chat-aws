# 共通ライブラリ - Lambda関数間で使用する共通機能
import json
import logging
from datetime import datetime
import jwt
from typing import Dict, Any, Optional

# ログ設定
def setup_logger(name: str, level=logging.INFO):
    """統一されたロガー設定"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # フォーマッター設定
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(levelname)s] %(name)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

class ResponseBuilder:
    """HTTP レスポンス構築用クラス"""
    
    @staticmethod
    def cors_headers() -> Dict[str, str]:
        """CORS ヘッダーを返す"""
        return {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Content-Type': 'application/json'
        }
    
    @staticmethod
    def success(data: Any = None, status_code: int = 200) -> Dict[str, Any]:
        """成功レスポンスを構築"""
        body = data if data is not None else {'message': 'Success'}
        return {
            'statusCode': status_code,
            'headers': ResponseBuilder.cors_headers(),
            'body': json.dumps(body, ensure_ascii=False, default=str)
        }
    
    @staticmethod
    def error(message: str, status_code: int = 400, details: str = None) -> Dict[str, Any]:
        """エラーレスポンスを構築"""
        error_body = {'error': message}
        if details:
            error_body['details'] = details
            
        return {
            'statusCode': status_code,
            'headers': ResponseBuilder.cors_headers(),
            'body': json.dumps(error_body, ensure_ascii=False)
        }
    
    @staticmethod
    def options() -> Dict[str, Any]:
        """OPTIONSリクエスト用レスポンス"""
        return {
            'statusCode': 200,
            'headers': ResponseBuilder.cors_headers(),
            'body': json.dumps({'message': 'OK'})
        }

class RequestValidator:
    """リクエスト検証用クラス"""
    
    @staticmethod
    def validate_body(event: Dict[str, Any]) -> Dict[str, Any]:
        """リクエストボディを検証・パース"""
        if 'body' not in event or not event['body']:
            raise ValueError('リクエストボディが必要です')
        
        try:
            body = json.loads(event['body'])
            return body
        except json.JSONDecodeError as e:
            raise ValueError(f'無効なJSON形式です: {str(e)}')
    
    @staticmethod
    def validate_auth_token(event: Dict[str, Any]) -> Dict[str, Any]:
        """認証トークンを検証"""
        headers = event.get('headers', {})
        
        # 大文字小文字の違いに対応
        auth_header = None
        for key, value in headers.items():
            if key.lower() == 'authorization':
                auth_header = value
                break
        
        if not auth_header:
            raise ValueError('認証ヘッダーが必要です')
        
        if not auth_header.startswith('Bearer '):
            raise ValueError('認証形式が正しくありません')
        
        token = auth_header.replace('Bearer ', '')
        
        try:
            # JWT デコード（検証なし - Cognitoで検証済みと仮定）
            decoded_token = jwt.decode(token, options={"verify_signature": False})
            return {
                'token': token,
                'user_id': decoded_token.get('sub'),
                'email': decoded_token.get('email'),
                'username': decoded_token.get('cognito:username')
            }
        except Exception as e:
            raise ValueError(f'認証トークンが無効です: {str(e)}')

class DatabaseHelper:
    """DynamoDB操作用ヘルパークラス"""
    
    def __init__(self, dynamodb_resource):
        self.dynamodb = dynamodb_resource
        self.logger = setup_logger('DatabaseHelper')
    
    def get_table(self, table_name: str):
        """テーブル取得"""
        return self.dynamodb.Table(table_name)
    
    def safe_get_item(self, table_name: str, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """安全なアイテム取得（エラーハンドリング付き）"""
        try:
            table = self.get_table(table_name)
            response = table.get_item(Key=key)
            return response.get('Item')
        except Exception as e:
            self.logger.error(f"Failed to get item from {table_name}: {str(e)}")
            return None
    
    def safe_put_item(self, table_name: str, item: Dict[str, Any]) -> bool:
        """安全なアイテム保存"""
        try:
            table = self.get_table(table_name)
            table.put_item(Item=item)
            return True
        except Exception as e:
            self.logger.error(f"Failed to put item to {table_name}: {str(e)}")
            return False
    
    def safe_delete_item(self, table_name: str, key: Dict[str, Any]) -> bool:
        """安全なアイテム削除"""
        try:
            table = self.get_table(table_name)
            table.delete_item(Key=key)
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete item from {table_name}: {str(e)}")
            return False
    
    def safe_query(self, table_name: str, **kwargs) -> Optional[list]:
        """安全なクエリ実行"""
        try:
            table = self.get_table(table_name)
            response = table.query(**kwargs)
            return response.get('Items', [])
        except Exception as e:
            self.logger.error(f"Failed to query {table_name}: {str(e)}")
            return None
    
    def safe_scan(self, table_name: str, **kwargs) -> Optional[list]:
        """安全なスキャン実行"""
        try:
            table = self.get_table(table_name)
            response = table.scan(**kwargs)
            return response.get('Items', [])
        except Exception as e:
            self.logger.error(f"Failed to scan {table_name}: {str(e)}")
            return None

class ProfileHelper:
    """プロフィール関連ヘルパー"""
    
    def __init__(self, db_helper: DatabaseHelper, user_table: str):
        self.db_helper = db_helper
        self.user_table = user_table
        self.logger = setup_logger('ProfileHelper')
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """ユーザープロフィールを取得"""
        return self.db_helper.safe_get_item(
            self.user_table, 
            {'userId': user_id}
        )
    
    def save_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """ユーザープロフィールを保存"""
        profile = {
            'userId': user_id,
            'userName': profile_data.get('userName', ''),
            'age': profile_data.get('age', ''),
            'occupation': profile_data.get('occupation', ''),
            'gender': profile_data.get('gender', ''),
            'responseLength': profile_data.get('responseLength', 'medium'),
            'updatedAt': datetime.utcnow().isoformat(),
            'createdAt': profile_data.get('createdAt', datetime.utcnow().isoformat())
        }
        
        return self.db_helper.safe_put_item(self.user_table, profile)
    
    def customize_message_with_profile(self, message: str, user_profile: Dict[str, Any]) -> str:
        """プロフィールに基づいてメッセージをカスタマイズ"""
        if not user_profile:
            return message
        
        # プロフィール情報を抽出
        user_name = user_profile.get('userName', 'あなた')
        age = user_profile.get('age', '')
        occupation = user_profile.get('occupation', '')
        gender = user_profile.get('gender', '')
        response_length = user_profile.get('responseLength', 'medium')
        
        # 応答の長さ設定
        length_instructions = {
            'short': '短め（1-2行）',
            'medium': '適度な長さ（2-4行）',
            'long': '詳しく（4-8行）'
        }
        length_text = length_instructions.get(response_length, '適度な長さ（2-4行）')
        
        # カスタマイズされたメッセージを構築
        customized_message = f"""【ユーザー情報】
ユーザーの名前: {user_name}さん"""
        
        if age:
            customized_message += f"\n年齢層: {age}"
        if occupation:
            customized_message += f"\n職業: {occupation}"
        if gender:
            customized_message += f"\n性別: {gender}"
        
        customized_message += f"""

【応答指示】
{length_text}で応答してください。
ユーザーの属性に適した話し方や内容で応答してください。

【ユーザーメッセージ】
{message}"""
        
        return customized_message

class HistoryHelper:
    """履歴管理ヘルパー"""
    
    def __init__(self, db_helper: DatabaseHelper, history_table: str):
        self.db_helper = db_helper
        self.history_table = history_table
        self.logger = setup_logger('HistoryHelper')
    
    def save_message(self, user_id: str, session_id: str, role: str, content: str) -> bool:
        """メッセージを履歴に保存"""
        timestamp = datetime.utcnow().isoformat()
        
        message_item = {
            'userId': user_id,
            'timestamp': timestamp,
            'sessionId': session_id,
            'role': role,
            'content': content,
            'messageId': f"{session_id}_{timestamp}_{role}"
        }
        
        return self.db_helper.safe_put_item(self.history_table, message_item)
    
    def get_user_history(self, user_id: str) -> Optional[list]:
        """ユーザーの全履歴を取得"""
        try:
            return self.db_helper.safe_query(
                self.history_table,
                KeyConditionExpression='userId = :userId',
                ExpressionAttributeValues={':userId': user_id},
                ScanIndexForward=False  # 最新順
            )
        except Exception as e:
            self.logger.error(f"Failed to get user history: {str(e)}")
            return None
    
    def get_session_history(self, user_id: str, session_id: str) -> Optional[list]:
        """特定セッションの履歴を取得"""
        try:
            return self.db_helper.safe_query(
                self.history_table,
                KeyConditionExpression='userId = :userId',
                FilterExpression='sessionId = :sessionId',
                ExpressionAttributeValues={
                    ':userId': user_id,
                    ':sessionId': session_id
                },
                ScanIndexForward=True  # 時系列順
            )
        except Exception as e:
            self.logger.error(f"Failed to get session history: {str(e)}")
            return None
    
    def delete_session(self, user_id: str, session_id: str) -> bool:
        """セッション全体を削除"""
        try:
            # セッションの全メッセージを取得
            messages = self.get_session_history(user_id, session_id)
            if not messages:
                return True
            
            # 各メッセージを削除
            success = True
            for message in messages:
                if not self.db_helper.safe_delete_item(
                    self.history_table,
                    {'userId': user_id, 'timestamp': message['timestamp']}
                ):
                    success = False
            
            return success
        except Exception as e:
            self.logger.error(f"Failed to delete session: {str(e)}")
            return False
    
    def delete_user_history(self, user_id: str) -> bool:
        """ユーザーの全履歴を削除"""
        try:
            messages = self.get_user_history(user_id)
            if not messages:
                return True
            
            success = True
            for message in messages:
                if not self.db_helper.safe_delete_item(
                    self.history_table,
                    {'userId': user_id, 'timestamp': message['timestamp']}
                ):
                    success = False
            
            return success
        except Exception as e:
            self.logger.error(f"Failed to delete user history: {str(e)}")
            return False

# 共通設定
AWS_REGION = 'ap-northeast-1'
BEDROCK_REGION = 'us-east-1'  # Bedrock Agentのリージョン

# テーブル名
USER_TABLE = 'GenkiChatUserTable'
HISTORY_TABLE = 'GenkiChatHistoryTable'

# Bedrock Agent設定
AGENT_ID = 'PLMASWUNAG'
AGENT_ALIAS_ID = 'XWFWAS7SOV'