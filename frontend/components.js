// 共通コンポーネント管理
class ComponentManager {
    constructor() {
        this.components = new Map();
    }

    // ヘッダーコンポーネントを作成
    createHeader(config = {}) {
        console.log('Creating header with config:', config);
        const { 
            title = '🌟 元気チャット',
            showBackButton = false,
            backUrl = 'chat.html',
            backText = 'チャット',
            menuItems = this.getDefaultMenuItems()
        } = config;

        return `
            <div class="header">
                <div class="header-left">
                    ${showBackButton ? `
                        <a href="${backUrl}" class="back-button">
                            <span>←</span>
                            ${backText}
                        </a>
                    ` : ''}
                    <h1>${title}</h1>
                </div>
                
                <div class="hamburger-menu" id="hamburgerMenu">
                    <button class="hamburger-button" onclick="toggleMenu()">
                        <div class="hamburger-icon">
                            <div class="hamburger-line"></div>
                            <div class="hamburger-line"></div>
                            <div class="hamburger-line"></div>
                        </div>
                    </button>
                    
                    <div class="menu-dropdown">
                        ${menuItems.map(item => `
                            <${item.href ? 'a href="' + item.href + '"' : 'div'} 
                                class="menu-item ${item.className || ''}" 
                                ${item.onclick ? 'onclick="' + item.onclick + '"' : ''}>
                                <span class="menu-icon">${item.icon}</span>
                                ${item.text}
                            </${item.href ? 'a' : 'div'}>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    // デフォルトのメニューアイテム
    getDefaultMenuItems() {
        return [
            { icon: '✨', text: '新規チャット', onclick: 'newSession()' },
            { icon: '📚', text: '履歴', href: 'history.html' },
            { icon: '👤', text: 'プロフィール', href: 'profile.html' },
            { icon: '🌙', text: 'ダークモード', onclick: 'toggleTheme()', id: 'themeToggle' },
            { icon: '🚪', text: 'ログアウト', onclick: 'logout()', className: 'logout' }
        ];
    }

    // すべてのコンポーネントを初期化
    initializeAll() {
        this.initializeCommon();
        this.initializeTheme();
    }

    // 共通のJavaScript関数を初期化
    initializeCommon() {
        // ハンバーガーメニューの切り替え
        window.toggleMenu = function() {
            const menu = document.getElementById('hamburgerMenu');
            menu.classList.toggle('active');
        };

        // メニュー外クリックで閉じる
        document.addEventListener('click', function(event) {
            const menu = document.getElementById('hamburgerMenu');
            if (menu && !menu.contains(event.target)) {
                menu.classList.remove('active');
            }
        });

        // 新規セッション
        window.newSession = function() {
            localStorage.removeItem('currentSessionId');
            if (window.location.pathname.includes('chat.html')) {
                location.reload();
            } else {
                window.location.href = 'chat.html';
            }
        };

        // ログアウト
        window.logout = function() {
            if (confirm('ログアウトしますか？')) {
                localStorage.clear();
                sessionStorage.clear();
                if (window.cognitoAuth) {
                    window.cognitoAuth.signOut();
                }
                window.location.href = 'index.html';
            }
        };

        // テーマ切り替え
        window.toggleTheme = function() {
            const currentTheme = document.body.getAttribute('data-theme') || 'dark';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // メニューのテーマトグルテキストを更新
            const themeToggle = document.getElementById('themeToggle');
            if (themeToggle) {
                const icon = newTheme === 'light' ? '🌙' : '☀️';
                const text = newTheme === 'light' ? 'ダークモード' : 'ライトモード';
                themeToggle.innerHTML = `<span class="menu-icon">${icon}</span> ${text}`;
            }
        };

        // テーマを初期化
        window.initializeTheme = function() {
            const savedTheme = localStorage.getItem('theme') || 'dark';
            document.body.setAttribute('data-theme', savedTheme);
            
            // メニューのテーマトグルテキストを更新
            const themeToggle = document.getElementById('themeToggle');
            if (themeToggle) {
                const icon = savedTheme === 'dark' ? '🌙' : '☀️';
                const text = savedTheme === 'dark' ? 'ダークモード' : 'ライトモード';
                themeToggle.innerHTML = `<span class="menu-icon">${icon}</span> ${text}`;
            }
        };
    }

    // テーマを初期化（インスタンスメソッド）
    initializeTheme() {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.body.setAttribute('data-theme', savedTheme);
        
        // 少し遅延してテーマトグルのテキストを更新
        setTimeout(() => {
            const themeToggle = document.getElementById('themeToggle');
            if (themeToggle) {
                const icon = savedTheme === 'dark' ? '🌙' : '☀️';
                const text = savedTheme === 'dark' ? 'ダークモード' : 'ライトモード';
                themeToggle.innerHTML = `<span class="menu-icon">${icon}</span> ${text}`;
            }
        }, 100);
    }

    // エラーメッセージコンポーネント
    createErrorMessage(id = 'errorMessage') {
        return `
            <div class="error-message" id="${id}">
                <div class="error-title">接続エラー</div>
                <div class="error-details" id="${id}Details">サーバーに接続できませんでした。</div>
                <button class="retry-button" onclick="retryLastMessage()">再試行</button>
            </div>
        `;
    }

    // ネットワーク状態表示コンポーネント
    createNetworkStatus() {
        return `
            <div class="network-status offline" id="networkStatus">
                オフラインです
            </div>
        `;
    }

    // 共通のユーティリティ関数
    static utils = {
        // APIベースURL取得
        getApiBaseUrl() {
            return 'https://i6zlozpitk.execute-api.ap-northeast-1.amazonaws.com/prod';
        },

        // エラー表示
        showError(message, details = '') {
            const errorMsg = document.getElementById('errorMessage');
            if (errorMsg) {
                errorMsg.style.display = 'block';
                const errorDetails = errorMsg.querySelector('.error-details');
                if (errorDetails) {
                    errorDetails.textContent = details || message;
                }
            }
        },

        // エラー非表示  
        hideError() {
            const errorMsg = document.getElementById('errorMessage');
            if (errorMsg) {
                errorMsg.style.display = 'none';
            }
        },

        // 日時フォーマット
        formatDate(timestamp) {
            const date = new Date(timestamp);
            return date.toLocaleString('ja-JP', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        },

        // セッションIDの生成
        generateSessionId() {
            return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }
    };
}

// グローバルにインスタンスを作成
window.componentManager = new ComponentManager();