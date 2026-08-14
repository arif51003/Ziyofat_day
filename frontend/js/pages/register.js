import { store, showToast } from '../store.js';
import { apiCall } from '../api.js';

export default function renderRegister() {
    const container = document.createElement('div');
    container.className = 'login-view';

    container.innerHTML = `
        <div class="login-card glass">
            <div class="brand-icon">
                <i class="ri-restaurant-2-fill"></i>
            </div>
            <h1 class="login-title">Restoranni ro'yxatdan o'tkazish</h1>
            <p class="login-subtitle">14 kunlik bepul sinov muddati bilan boshlang</p>

            <form id="register-form">
                <div class="input-group" style="text-align: left;">
                    <label class="input-label">Restoran nomi</label>
                    <input type="text" id="restaurant_name" class="input-field" placeholder="Masalan: Coffee Lux" required>
                </div>

                <div class="input-group" style="text-align: left;">
                    <label class="input-label">Restoran kodi (login uchun)</label>
                    <input type="text" id="restaurant_code" class="input-field" placeholder="masalan: coffee-lux" autocapitalize="off" required>
                </div>

                <div class="input-group" style="text-align: left;">
                    <label class="input-label">Telefon (ixtiyoriy)</label>
                    <input type="text" id="phone" class="input-field" placeholder="+998 90 123 45 67">
                </div>

                <hr style="border-color: var(--c-border); margin: 20px 0;">

                <div class="input-group" style="text-align: left;">
                    <label class="input-label">Ismingiz</label>
                    <input type="text" id="first_name" class="input-field" placeholder="Ismingiz">
                </div>

                <div class="input-group" style="text-align: left;">
                    <label class="input-label">Admin login (Username)</label>
                    <input type="text" id="username" class="input-field" placeholder="admin" required>
                </div>

                <div class="input-group" style="text-align: left; margin-bottom: 32px;">
                    <label class="input-label">Parol</label>
                    <input type="password" id="password" class="input-field" placeholder="••••••••" required minlength="6">
                </div>

                <button type="submit" class="btn btn-primary btn-block" id="submit-btn">
                    Ro'yxatdan o'tish <i class="ri-arrow-right-line"></i>
                </button>
            </form>

            <p style="margin-top: 20px; text-align: center;">
                Hisobingiz bormi? <a href="#" id="go-login-link" style="color: var(--c-primary);">Tizimga kirish</a>
            </p>
        </div>
    `;

    const form = container.querySelector('#register-form');
    const submitBtn = container.querySelector('#submit-btn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const restaurant_name = container.querySelector('#restaurant_name').value.trim();
        const restaurant_code = container.querySelector('#restaurant_code').value.trim();
        const phone = container.querySelector('#phone').value.trim();
        const first_name = container.querySelector('#first_name').value.trim();
        const username = container.querySelector('#username').value.trim();
        const password = container.querySelector('#password').value;

        if (!restaurant_name || !restaurant_code || !username || !password) {
            showToast('Barcha majburiy maydonlarni to\'ldiring!', 'error');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="ri-loader-4-line" style="animation: spin 1s linear infinite;"></i> Yaratilmoqda...';

        try {
            const body = new URLSearchParams();
            body.append('restaurant_name', restaurant_name);
            body.append('restaurant_code', restaurant_code);
            if (phone) body.append('phone', phone);
            if (first_name) body.append('first_name', first_name);
            body.append('username', username);
            body.append('password', password);

            const tokenData = await apiCall('/auth/register-restaurant', 'POST', body);

            if (tokenData.access_token) {
                const userData = {
                    id: tokenData.user.id,
                    username: tokenData.user.username,
                    role: tokenData.user.role,
                    first_name: tokenData.user.first_name,
                    last_name: tokenData.user.last_name,
                    is_admin: tokenData.user.is_admin,
                    is_platform_owner: tokenData.user.is_platform_owner,
                    restaurant: tokenData.user.restaurant
                };
                store.login(tokenData.access_token, userData);
                showToast('Restoran muvaffaqiyatli yaratildi!', 'success');
                window.dispatchEvent(new CustomEvent('navTo', { detail: '/dashboard' }));
            }
        } catch (error) {
            console.error('❌ Register error:', error);
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Ro\'yxatdan o\'tish <i class="ri-arrow-right-line"></i>';
        }
    });

    container.querySelector('#go-login-link').addEventListener('click', (e) => {
        e.preventDefault();
        window.dispatchEvent(new CustomEvent('navTo', { detail: '/login' }));
    });

    return container;
}
