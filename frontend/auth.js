// AWS Cognito認証ライブラリ
// Amazon Cognito Identity SDK for JavaScript
class CognitoAuth {
    constructor(config) {
        this.config = config;
        this.currentUser = null;
        this.idToken = null;
        this.accessToken = null;
        this.refreshToken = null;
    }

    // ユーザー登録
    async signUp(email, password, attributes = {}) {
        try {
            const response = await fetch(`https://cognito-idp.${this.config.region}.amazonaws.com/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-amz-json-1.1',
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.SignUp'
                },
                body: JSON.stringify({
                    ClientId: this.config.clientId,
                    Username: email,
                    Password: password,
                    UserAttributes: Object.keys(attributes).map(key => ({
                        Name: key,
                        Value: attributes[key]
                    })),
                    SecretHash: this.calculateSecretHash(email)
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'サインアップに失敗しました');
            }

            return {
                success: true,
                userSub: data.UserSub,
                codeDeliveryDetails: data.CodeDeliveryDetails
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    // メール確認
    async confirmSignUp(email, confirmationCode) {
        try {
            const response = await fetch(`https://cognito-idp.${this.config.region}.amazonaws.com/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-amz-json-1.1',
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.ConfirmSignUp'
                },
                body: JSON.stringify({
                    ClientId: this.config.clientId,
                    Username: email,
                    ConfirmationCode: confirmationCode,
                    SecretHash: this.calculateSecretHash(email)
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || '確認に失敗しました');
            }

            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    // ログイン
    async signIn(email, password) {
        try {
            const response = await fetch(`https://cognito-idp.${this.config.region}.amazonaws.com/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-amz-json-1.1',
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth'
                },
                body: JSON.stringify({
                    ClientId: this.config.clientId,
                    AuthFlow: 'USER_PASSWORD_AUTH',
                    AuthParameters: {
                        USERNAME: email,
                        PASSWORD: password,
                        SECRET_HASH: this.calculateSecretHash(email)
                    }
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'ログインに失敗しました');
            }

            // トークンを保存
            this.idToken = data.AuthenticationResult.IdToken;
            this.accessToken = data.AuthenticationResult.AccessToken;
            this.refreshToken = data.AuthenticationResult.RefreshToken;
            
            // ローカルストレージに保存
            localStorage.setItem('idToken', this.idToken);
            localStorage.setItem('accessToken', this.accessToken);
            localStorage.setItem('refreshToken', this.refreshToken);
            
            // ユーザー情報を取得
            this.currentUser = this.parseJWT(this.idToken);

            return {
                success: true,
                user: this.currentUser,
                tokens: {
                    idToken: this.idToken,
                    accessToken: this.accessToken,
                    refreshToken: this.refreshToken
                }
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    // ログアウト
    async signOut() {
        try {
            if (this.accessToken) {
                const response = await fetch(`https://cognito-idp.${this.config.region}.amazonaws.com/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-amz-json-1.1',
                        'X-Amz-Target': 'AWSCognitoIdentityProviderService.GlobalSignOut'
                    },
                    body: JSON.stringify({
                        AccessToken: this.accessToken
                    })
                });
            }
        } catch (error) {
            console.warn('GlobalSignOut failed:', error.message);
        }

        // ローカル状態をクリア
        this.currentUser = null;
        this.idToken = null;
        this.accessToken = null;
        this.refreshToken = null;
        
        // ローカルストレージをクリア
        localStorage.removeItem('idToken');
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        
        return { success: true };
    }

    // セッション復元
    restoreSession() {
        const idToken = localStorage.getItem('idToken');
        const accessToken = localStorage.getItem('accessToken');
        const refreshToken = localStorage.getItem('refreshToken');

        if (idToken && accessToken && refreshToken) {
            // トークンの有効性チェック
            const tokenPayload = this.parseJWT(idToken);
            const now = Math.floor(Date.now() / 1000);
            
            if (tokenPayload.exp > now) {
                this.idToken = idToken;
                this.accessToken = accessToken;
                this.refreshToken = refreshToken;
                this.currentUser = tokenPayload;
                return true;
            }
        }
        return false;
    }

    // トークンリフレッシュ
    async refreshTokens() {
        if (!this.refreshToken) {
            throw new Error('Refresh token not available');
        }

        try {
            const response = await fetch(`https://cognito-idp.${this.config.region}.amazonaws.com/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-amz-json-1.1',
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth'
                },
                body: JSON.stringify({
                    ClientId: this.config.clientId,
                    AuthFlow: 'REFRESH_TOKEN_AUTH',
                    AuthParameters: {
                        REFRESH_TOKEN: this.refreshToken,
                        SECRET_HASH: this.calculateSecretHash(this.currentUser.email)
                    }
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'トークンリフレッシュに失敗しました');
            }

            // 新しいトークンを保存
            this.idToken = data.AuthenticationResult.IdToken;
            this.accessToken = data.AuthenticationResult.AccessToken;
            
            localStorage.setItem('idToken', this.idToken);
            localStorage.setItem('accessToken', this.accessToken);

            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    // 現在のユーザー情報を取得
    getCurrentUser() {
        return this.currentUser;
    }

    // IDトークンを取得
    getIdToken() {
        return this.idToken;
    }

    // ログイン状態チェック
    isAuthenticated() {
        if (!this.idToken) return false;
        
        const tokenPayload = this.parseJWT(this.idToken);
        const now = Math.floor(Date.now() / 1000);
        
        return tokenPayload.exp > now;
    }

    // SECRET_HASHを計算 (CLIENT_SECRETが設定されている場合)
    calculateSecretHash(username) {
        if (!this.config.clientSecret) return undefined;
        
        const message = username + this.config.clientId;
        
        // CryptoJSを使用してHMAC-SHA256を計算
        if (typeof CryptoJS !== 'undefined') {
            const hash = CryptoJS.HmacSHA256(message, this.config.clientSecret);
            return CryptoJS.enc.Base64.stringify(hash);
        }
        
        // CryptoJSが利用できない場合のフォールバック
        console.error('CryptoJS not available. Please ensure the library is loaded.');
        return null;
    }

    // JWTトークンをパース
    parseJWT(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            return JSON.parse(jsonPayload);
        } catch (error) {
            console.error('JWT parse error:', error);
            return null;
        }
    }
}

// グローバルに公開
window.CognitoAuth = CognitoAuth;