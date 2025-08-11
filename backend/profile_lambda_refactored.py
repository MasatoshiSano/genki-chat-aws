import json
import boto3
from datetime import datetime
import logging
from common import (
    setup_logger,
    ResponseBuilder,
    RequestValidator,
    DatabaseHelper,
    ProfileHelper,
    USER_TABLE
)

# ログ設定
logger = setup_logger(__name__)

# AWS サービス初期化
dynamodb = boto3.resource('dynamodb')

# ヘルパー初期化
db_helper = DatabaseHelper(dynamodb)
profile_helper = ProfileHelper(db_helper, USER_TABLE)

def lambda_handler(event, context):
    """
    プロフィール管理を行うLambda関数（リファクタリング版）
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
        
        logger.info(f"Processing {http_method} request for user: {user_id}")
        
        if http_method == 'GET':
            # プロフィール取得
            return handle_get_profile(user_id)
        
        elif http_method == 'POST':
            # プロフィール保存
            return handle_save_profile(event, user_id)
        
        else:
            return ResponseBuilder.error(f'サポートされていないHTTPメソッドです: {http_method}', 405)
    
    except Exception as e:
        logger.error(f"Unexpected error in profile lambda: {str(e)}", exc_info=True)
        return ResponseBuilder.error('内部サーバーエラーが発生しました', 500, str(e))

def handle_get_profile(user_id: str):
    """プロフィール取得処理"""
    try:
        logger.info(f"Getting profile for user: {user_id}")
        
        profile = profile_helper.get_user_profile(user_id)
        
        if profile:
            logger.info("Profile found for user")
            
            # 不要なフィールドを除去（セキュリティ）
            safe_profile = {
                'userName': profile.get('userName', ''),
                'age': profile.get('age', ''),
                'occupation': profile.get('occupation', ''),
                'gender': profile.get('gender', ''),
                'responseLength': profile.get('responseLength', 'medium'),
                'updatedAt': profile.get('updatedAt', ''),
                'createdAt': profile.get('createdAt', '')
            }
            
            return ResponseBuilder.success(safe_profile)
        else:
            logger.info("No profile found for user")
            return ResponseBuilder.success({
                'userName': '',
                'age': '',
                'occupation': '',
                'gender': '',
                'responseLength': 'medium',
                'message': 'プロフィールが見つかりません'
            })
        
    except Exception as e:
        logger.error(f"Error in get profile: {str(e)}")
        return ResponseBuilder.error('プロフィール取得中にエラーが発生しました', 500, str(e))

def handle_save_profile(event, user_id: str):
    """プロフィール保存処理"""
    try:
        logger.info(f"Saving profile for user: {user_id}")
        
        # リクエストボディ検証
        try:
            body = RequestValidator.validate_body(event)
        except ValueError as e:
            logger.error(f"Request validation failed: {str(e)}")
            return ResponseBuilder.error(str(e), 400)
        
        # プロフィールデータ検証
        profile_data = validate_profile_data(body)
        if isinstance(profile_data, dict) and 'error' in profile_data:
            return ResponseBuilder.error(profile_data['error'], 400)
        
        # 既存プロフィール取得（作成日時保持のため）
        existing_profile = profile_helper.get_user_profile(user_id)
        if existing_profile:
            profile_data['createdAt'] = existing_profile.get('createdAt')
        
        # プロフィール保存
        success = profile_helper.save_user_profile(user_id, profile_data)
        
        if not success:
            logger.error("Failed to save profile to database")
            return ResponseBuilder.error('プロフィールの保存に失敗しました', 500)
        
        logger.info("Profile saved successfully")
        
        return ResponseBuilder.success({
            'message': 'プロフィールが保存されました',
            'profile': {
                'userName': profile_data.get('userName', ''),
                'age': profile_data.get('age', ''),
                'occupation': profile_data.get('occupation', ''),
                'gender': profile_data.get('gender', ''),
                'responseLength': profile_data.get('responseLength', 'medium'),
                'updatedAt': profile_data.get('updatedAt')
            }
        })
        
    except Exception as e:
        logger.error(f"Error in save profile: {str(e)}")
        return ResponseBuilder.error('プロフィール保存中にエラーが発生しました', 500, str(e))

def validate_profile_data(data):
    """
    プロフィールデータの検証とサニタイゼーション
    """
    try:
        # 許可されたフィールドのみ抽出
        allowed_fields = ['userName', 'age', 'occupation', 'gender', 'responseLength']
        
        validated_data = {}
        
        for field in allowed_fields:
            value = data.get(field, '')
            
            if field == 'userName':
                # ユーザー名の検証
                if value and len(value.strip()) > 50:
                    return {'error': 'ユーザー名は50文字以内で入力してください'}
                validated_data[field] = value.strip() if value else ''
                
            elif field == 'age':
                # 年齢の検証
                valid_ages = ['', '10代', '20代', '30代', '40代', '50代', '60代以上']
                if value not in valid_ages:
                    return {'error': '無効な年齢が選択されています'}
                validated_data[field] = value
                
            elif field == 'occupation':
                # 職業の検証
                if value and len(value.strip()) > 50:
                    return {'error': '職業は50文字以内で入力してください'}
                validated_data[field] = value.strip() if value else ''
                
            elif field == 'gender':
                # 性別の検証
                valid_genders = ['', '男性', '女性', 'その他', '答えない']
                if value not in valid_genders:
                    return {'error': '無効な性別が選択されています'}
                validated_data[field] = value
                
            elif field == 'responseLength':
                # 応答の長さの検証
                valid_lengths = ['short', 'medium', 'long']
                if value not in valid_lengths:
                    validated_data[field] = 'medium'  # デフォルト値
                else:
                    validated_data[field] = value
        
        # タイムスタンプ追加
        validated_data['updatedAt'] = datetime.utcnow().isoformat()
        
        logger.info(f"Profile data validated: {validated_data}")
        
        return validated_data
        
    except Exception as e:
        logger.error(f"Error validating profile data: {str(e)}")
        return {'error': 'プロフィールデータの検証中にエラーが発生しました'}

if __name__ == "__main__":
    # ローカルテスト用
    test_event_get = {
        "httpMethod": "GET",
        "headers": {
            "Authorization": "Bearer test-token"
        }
    }
    
    test_event_post = {
        "httpMethod": "POST",
        "headers": {
            "Authorization": "Bearer test-token"
        },
        "body": json.dumps({
            "userName": "テストユーザー",
            "age": "30代",
            "occupation": "エンジニア",
            "gender": "男性",
            "responseLength": "medium"
        })
    }
    
    print("Testing GET:")
    result = lambda_handler(test_event_get, None)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\nTesting POST:")
    result = lambda_handler(test_event_post, None)
    print(json.dumps(result, indent=2, ensure_ascii=False))