export const API_BASE = ''; // Frontend is served by the same FastAPI app, so requests are same-origin

// Store for global state
export const store = {
    token: localStorage.getItem('access_token') || null,
    user: JSON.parse(localStorage.getItem('user')) || null,

    login(token, user) {
        this.token = token;
        this.user = user;
        localStorage.setItem('access_token', token);
        localStorage.setItem('user', JSON.stringify(user));
    },

    logout() {
        // Admins also get a Starlette-Admin session cookie on login (see
        // /auth/login/) so /admin doesn't ask for a second login. Clear it
        // here too, otherwise it stays valid after the SPA "logs out".
        if (this.user?.is_admin || this.user?.is_platform_owner) {
            fetch(`${API_BASE}/admin/logout`, { credentials: 'include' }).catch(() => {});
        }
        this.token = null;
        this.user = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
    },

    isAuthenticated() {
        return !!this.token;
    }
};

// UI Utils (Toast)
export function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconMap = {
        success: 'ri-checkbox-circle-fill',
        error: 'ri-error-warning-fill',
        warning: 'ri-alert-fill',
        info: 'ri-information-fill'
    };

    toast.innerHTML = `
        <i class="${iconMap[type] || iconMap.info}" style="font-size: 24px;"></i>
        <div style="flex:1;">${message}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
