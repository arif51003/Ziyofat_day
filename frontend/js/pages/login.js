import { store, showToast } from '../store.js';
import { apiCall } from '../api.js';

export default function renderLogin() {
    const container = document.createElement('div');
    container.className = 'login-view';

    container.innerHTML = `
        <div class="login-card glass">
            <div class="brand-icon">
                <i class="ri-restaurant-2-fill"></i>
            </div>
            <h1 class="login-title">Tizimga kirish</h1>
            <p class="login-subtitle">Ziyofat-day boshqaruv paneli</p>

            <form id="login-form">
                <div class="input-group" style="text-align: left;">
                    <label class="input-label">Login (Username)</label>
                    <input type="text" id="username" name="username" class="input-field" placeholder="admin" required>
                </div>
                
                <div class="input-group" style="text-align: left; margin-bottom: 32px;">
                    <label class="input-label">Parol (Password)</label>
                    <input type="password" id="password" name="password" class="input-field" placeholder="••••••••" required>
                </div>

                <button type="submit" class="btn btn-primary btn-block" id="submit-btn">
                    Tizimga kirish <i class="ri-arrow-right-line"></i>
                </button>
            </form>
        </div>
    `;

    const form = container.querySelector('#login-form');
    const submitBtn = container.querySelector('#submit-btn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const usernameInput = document.getElementById('username');
        const passwordInput = document.getElementById('password');
        const username = usernameInput?.value || '';
        const password = passwordInput?.value || '';
        
        console.log('Login attempt:', { username, password_length: password.length });
        
        if (!username || !password) {
            showToast('Username va password ni to\'ldiring!', 'error');
            return;
        }
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="ri-loader-4-line" style="animation: spin 1s linear infinite;"></i> Tekshirilmoqda...';

        try {
            // Fetch token (Assuming OAuth2 Password Bearer flow standard in FastAPI)
            const body = new URLSearchParams();
            body.append('username', username);
            body.append('password', password);
            
            console.log('Sending to /auth/login/:', body.toString());

            const tokenData = await apiCall('/auth/login/', 'POST', body);
            
            console.log('✅ Login response:', tokenData);
            
            if(tokenData.access_token) {
                // Use user data from backend if available
                let userData = tokenData.user ? {
                    id: tokenData.user.id,
                    username: tokenData.user.username,
                    role: tokenData.user.role,
                    first_name: tokenData.user.first_name,
                    last_name: tokenData.user.last_name,
                    is_admin: tokenData.user.is_admin
                } : { 
                    username: username, 
                    role: "unknown" 
                };
                
                store.login(tokenData.access_token, userData);
                console.log('✅ User logged in:', userData);
                showToast('Muvaffaqiyatli kirdingiz!', 'success');
                window.dispatchEvent(new CustomEvent('navTo', { detail: '/dashboard' }));
            } else {
                showToast('❌ Login muvaffaqsiz - token yo\'q', 'error');
                console.error('No access token in response:', tokenData);
            }

        } catch (error) {
            console.error('❌ Login error:', error);
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Tizimga kirish <i class="ri-arrow-right-line"></i>';
        }
    });

    return container;
}

// Add global style for spin if not exist
const style = document.createElement('style');
style.innerHTML = `
@keyframes spin { 100% { transform: rotate(360deg); } }
`;
document.head.appendChild(style);
