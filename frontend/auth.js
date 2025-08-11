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

// 統合認証・API通信ライブラリ
class AuthManager {
    constructor() {
        this.apiBaseUrl = 'https://i6zlozpitk.execute-api.ap-northeast-1.amazonaws.com/prod';
        this.cognitoConfig = {
            userPoolId: 'ap-northeast-1_7CLrXZQiB',
            clientId: '5b6kk9mghcr6k80cjn4fktb1jt',
            region: 'ap-northeast-1'
        };
        this.cognitoAuth = new CognitoAuth(this.cognitoConfig);
    }

    // 認証状態チェック
    isAuthenticated() {
        const token = localStorage.getItem('idToken');
        if (!token) return false;
        
        try {
            // JWT の有効期限をチェック
            const payload = JSON.parse(atob(token.split('.')[1]));
            const now = Math.floor(Date.now() / 1000);
            return payload.exp > now;
        } catch (error) {
            console.error('Token validation error:', error);
            return false;
        }
    }

    // 認証ヘッダー取得
    getAuthHeaders() {
        const token = localStorage.getItem('idToken');
        return token ? {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        } : {
            'Content-Type': 'application/json'
        };
    }

    // APIリクエスト送信
    async request(endpoint, options = {}) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        const headers = this.getAuthHeaders();
        
        try {
            const response = await fetch(url, {
                ...options,
                headers: { ...headers, ...options.headers }
            });
            
            if (!response.ok) {
                if (response.status === 401) {
                    this.handleAuthError();
                    throw new Error('認証エラー: ログインし直してください');
                }
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    // GET リクエスト
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    // POST リクエスト
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // DELETE リクエスト
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // 認証エラー処理
    handleAuthError() {
        console.log('Authentication error - clearing tokens');
        localStorage.clear();
        sessionStorage.clear();
        // 現在がログインページでなければリダイレクト
        if (!window.location.pathname.includes('index.html')) {
            window.location.href = 'index.html';
        }
    }

    // ログアウト
    logout() {
        if (confirm('ログアウトしますか？')) {
            this.cognitoAuth.signOut();
            localStorage.clear();
            sessionStorage.clear();
            window.location.href = 'index.html';
        }
    }
}

// チャット機能
class ChatManager {
    constructor(authManager) {
        this.auth = authManager;
        this.currentSessionId = null;
        this.isProcessing = false;
    }

    // セッション初期化
    initializeSession() {
        this.currentSessionId = localStorage.getItem('currentSessionId');
        if (!this.currentSessionId) {
            this.currentSessionId = this.generateSessionId();
            localStorage.setItem('currentSessionId', this.currentSessionId);
        }
        return this.currentSessionId;
    }

    // セッションID生成
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // 新規セッション作成
    createNewSession() {
        this.currentSessionId = this.generateSessionId();
        localStorage.setItem('currentSessionId', this.currentSessionId);
        return this.currentSessionId;
    }

    // メッセージ送信
    async sendMessage(message) {
        if (this.isProcessing || !message.trim()) {
            return null;
        }

        this.isProcessing = true;
        try {
            const requestData = {
                message: message.trim(),
                sessionId: this.currentSessionId || this.initializeSession()
            };

            console.log('Sending message:', requestData);
            const response = await this.auth.post('/chat', requestData);
            console.log('Chat response:', response);
            
            return response;
        } catch (error) {
            console.error('Failed to send message:', error);
            throw error;
        } finally {
            this.isProcessing = false;
        }
    }
}

// 履歴管理
class HistoryManager {
    constructor(authManager) {
        this.auth = authManager;
    }

    // 履歴一覧取得
    async getHistory() {
        try {
            const response = await this.auth.get('/history');
            console.log('History response:', response);
            return response.conversations || [];
        } catch (error) {
            console.error('Failed to load history:', error);
            throw error;
        }
    }

    // 履歴削除
    async deleteHistory(sessionId) {
        try {
            await this.auth.delete(`/history?sessionId=${sessionId}`);
            console.log('History deleted:', sessionId);
        } catch (error) {
            console.error('Failed to delete history:', error);
            throw error;
        }
    }

    // 全履歴削除
    async deleteAllHistory() {
        try {
            await this.auth.delete('/history');
            console.log('All history deleted');
        } catch (error) {
            console.error('Failed to delete all history:', error);
            throw error;
        }
    }
}

// プロフィール管理
class ProfileManager {
    constructor(authManager) {
        this.auth = authManager;
    }

    // プロフィール取得
    async getProfile() {
        try {
            const response = await this.auth.get('/chat/profile');
            console.log('Profile loaded from server:', response);
            return response;
        } catch (error) {
            console.error('Failed to load profile from server:', error);
            throw error;
        }
    }

    // プロフィール保存
    async saveProfile(profileData) {
        try {
            const response = await this.auth.post('/chat/profile', profileData);
            console.log('Profile saved to server:', response);
            return response;
        } catch (error) {
            console.error('Failed to save profile to server:', error);
            throw error;
        }
    }

    // ローカルプロフィール取得
    getLocalProfile() {
        try {
            const profile = JSON.parse(localStorage.getItem('userProfile') || '{}');
            return profile;
        } catch (error) {
            console.error('Failed to load local profile:', error);
            return {};
        }
    }

    // ローカルプロフィール保存
    saveLocalProfile(profileData) {
        try {
            localStorage.setItem('userProfile', JSON.stringify(profileData));
        } catch (error) {
            console.error('Failed to save local profile:', error);
        }
    }
}

// テーマ管理
class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'dark';
        this.initialize();
    }

    // テーマ初期化
    initialize() {
        document.body.setAttribute('data-theme', this.currentTheme);
        this.updateThemeToggleText();
    }

    // テーマ切り替え
    toggle() {
        this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        document.body.setAttribute('data-theme', this.currentTheme);
        localStorage.setItem('theme', this.currentTheme);
        this.updateThemeToggleText();
    }

    // テーマトグルテキスト更新
    updateThemeToggleText() {
        setTimeout(() => {
            const themeToggle = document.getElementById('themeToggle');
            if (themeToggle) {
                const icon = this.currentTheme === 'dark' ? '🌙' : '☀️';
                const text = this.currentTheme === 'dark' ? 'ダークモード' : 'ライトモード';
                themeToggle.innerHTML = `<span class="menu-icon">${icon}</span> ${text}`;
            }
        }, 100);
    }
}

// UI ユーティリティ
class UIUtils {
    // ステータス表示
    static showStatus(message, type = 'info', duration = 3000) {
        const statusDiv = document.getElementById('statusMessage') || this.createStatusDiv();
        statusDiv.textContent = message;
        statusDiv.className = `status-message ${type}`;
        statusDiv.style.display = 'block';
        
        if (duration > 0) {
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, duration);
        }
    }

    // ステータス用DIV作成
    static createStatusDiv() {
        let statusDiv = document.getElementById('statusMessage');
        if (!statusDiv) {
            statusDiv = document.createElement('div');
            statusDiv.id = 'statusMessage';
            statusDiv.className = 'status-message';
            statusDiv.style.display = 'none';
            document.body.appendChild(statusDiv);
        }
        return statusDiv;
    }

    // ローディング表示
    static showLoading(elementId, message = '読み込み中...') {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `<div class="loading">${message}</div>`;
        }
    }

    // エラー表示
    static showError(message, details = '') {
        const errorMsg = document.getElementById('errorMessage');
        if (errorMsg) {
            errorMsg.style.display = 'block';
            const errorDetails = errorMsg.querySelector('.error-details');
            if (errorDetails) {
                errorDetails.textContent = details || message;
            }
        }
    }

    // エラー非表示
    static hideError() {
        const errorMsg = document.getElementById('errorMessage');
        if (errorMsg) {
            errorMsg.style.display = 'none';
        }
    }

    // 日時フォーマット
    static formatDate(timestamp) {
        try {
            const date = new Date(timestamp);
            if (isNaN(date.getTime())) {
                return '無効な日付';
            }
            return date.toLocaleString('ja-JP', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            console.error('Date formatting error:', error);
            return '日付不明';
        }
    }

    // 相対時間フォーマット
    static formatRelativeTime(timestamp) {
        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diffMs = now.getTime() - date.getTime();
            const diffMins = Math.floor(diffMs / (1000 * 60));
            const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
            const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

            if (diffMins < 1) return 'たった今';
            if (diffMins < 60) return `${diffMins}分前`;
            if (diffHours < 24) return `${diffHours}時間前`;
            if (diffDays < 7) return `${diffDays}日前`;
            return this.formatDate(timestamp);
        } catch (error) {
            console.error('Relative time formatting error:', error);
            return this.formatDate(timestamp);
        }
    }
}

// グローバル初期化
window.authManager = new AuthManager();
window.chatManager = new ChatManager(window.authManager);
window.historyManager = new HistoryManager(window.authManager);
window.profileManager = new ProfileManager(window.authManager);
window.themeManager = new ThemeManager();
window.UIUtils = UIUtils;

// 認証チェックを含む共通初期化関数
function initializeApp() {
    // ログインページ以外で認証チェック
    if (!window.location.pathname.includes('index.html') && !window.authManager.isAuthenticated()) {
        console.log('Not authenticated, redirecting to login');
        window.location.href = 'index.html';
        return false;
    }
    return true;
}

// 共通関数をグローバルに公開（後方互換性のため）
window.initializeApp = initializeApp;