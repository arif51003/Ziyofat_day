import { store, API_BASE } from './store.js';
import { apiCall } from './api.js';

// ---- Router ----
const routes = {
    '/login': () => import('./pages/login.js').then(m => m.default()),
    '/dashboard': () => renderDashboard(),
};

async function navigateTo(path) {
    console.log(`📍 Navigating to: ${path}`);
    
    if (path !== '/login' && !store.isAuthenticated()) {
        console.log('🚫 Not authenticated, redirecting to /login');
        path = '/login';
    } else if (path === '/login' && store.isAuthenticated()) {
        console.log('✅ Already authenticated, redirecting to /dashboard');
        path = '/dashboard';
    }

    const appRoot = document.getElementById('app-root');
    if (!appRoot) {
        console.error('❌ app-root element not found!');
        return;
    }
    
    appRoot.innerHTML = '<div style="display:flex;justify-content:center;align-items:center;height:100vh;"><div style="text-align:center;"><i class="ri-loader-4-line" style="font-size:48px;animation:spin 1s linear infinite;"></i><p>Yuklanmoqda...</p></div></div>';

    const renderer = routes[path] || routes['/login'];
    try {
        const content = await renderer();
        appRoot.innerHTML = '';
        appRoot.appendChild(content);
        history.pushState(null, '', path);
        console.log(`✅ Page loaded: ${path}`);
    } catch (e) {
        console.error('❌ Navigation error:', e);
        appRoot.innerHTML = '<h2 style="color:var(--c-danger);padding:24px;">Xatolik yuz berdi sahifani yuklashda: ' + e.message + '</h2>';
    }
}

// Global Custom Event for navigation inside SPAs
window.addEventListener('navTo', (e) => {
    console.log('🔄 Navigation event:', e.detail);
    navigateTo(e.detail);
});

// App Entry
async function initApp() {
    console.log('🔧 App initializing...');
    console.log('🔐 Auth status:', store.isAuthenticated() ? '✅ Authenticated' : '❌ Not authenticated');
    
    let initialPath = window.location.pathname;
    if (initialPath === '/') initialPath = store.isAuthenticated() ? '/dashboard' : '/login';
    
    console.log(`📍 Initial route: ${initialPath}`);
    try {
        await navigateTo(initialPath);
    } catch (error) {
        console.error('Init error:', error);
        const appRoot = document.getElementById('app-root');
        if (appRoot) {
            appRoot.innerHTML = '<h2 style="color:var(--c-danger);padding:24px;">Xatolik yuz berdi. Iltimos sahifani qayta yuklang.</h2>';
        }
    }
}

// -----------------------------------------
// Role-based Dashboard Renderer
// -----------------------------------------
async function renderDashboard() {
    const userRole = (store.user?.role || 'user').toLowerCase();
    const container = document.createElement('div');
    
    console.log(`📊 Rendering dashboard for role: ${userRole}`);
    
    try {
        switch(userRole) {
            case 'waiter':
                // Waiter: Show full interface (tables + orders + menu)
                console.log('📥 Loading waiter interface...');
                const waiterRenderer = await import('./pages/waiter.js').then(m => m.default);
                const waiterContent = await waiterRenderer();
                container.appendChild(waiterContent);
                console.log('✅ Waiter interface loaded');
                break;
                
            case 'kitchen':
                // Kitchen: ONLY show queue (no tables, no navigation)
                console.log('📥 Loading kitchen interface...');
                const kitchenRenderer = await import('./pages/kitchen.js').then(m => m.default);
                const kitchenContent = await kitchenRenderer();
                container.appendChild(kitchenContent);
                console.log('✅ Kitchen interface loaded');
                break;
                
            case 'cashier':
                // Cashier: ONLY show payment interface (no navigation)
                console.log('📥 Loading cashier interface...');
                const cashierRenderer = await import('./pages/cashier.js').then(m => m.default);
                const cashierContent = await cashierRenderer();
                container.appendChild(cashierContent);
                console.log('✅ Cashier interface loaded');
                break;
                
            case 'admin':
                // Admin: Show dashboard with navigation
                console.log('📥 Loading admin dashboard...');
                container.innerHTML = `
                    <div style="padding: 40px; text-align: center;">
                        <button id="logout-btn-top" style="float: right; padding: 8px 16px; background: var(--c-danger-alpha); color: var(--c-danger); border: none; border-radius: 4px; cursor: pointer;">
                            <i class="ri-logout-box-r-line"></i> Chiqish
                        </button>
                        <h2>Admin Paneli</h2>
                        <p style="color: var(--text-muted); margin-top: 12px;">Admin paneli backend Starlette-Admin orqali ishlaydi.</p>
                        <p style="margin-top: 20px;"><a href="${API_BASE}/admin/" style="color: var(--c-primary);">Admin Page'ga o'ting</a></p>
                    </div>
                `;
                container.querySelector('#logout-btn-top').addEventListener('click', () => {
                    store.logout();
                    window.dispatchEvent(new CustomEvent('navTo', { detail: '/login' }));
                });
                break;
                
            default:
                container.innerHTML = `
                    <div style="padding: 40px; text-align: center;">
                        <h2>Noma'lum rol</h2>
                        <p style="color: var(--text-muted);">Rolingiz tanilmadi: ${userRole}</p>
                        <button onclick="window.location.href='/login'" style="margin-top: 20px; padding: 10px 20px; background: var(--c-primary); color: white; border: none; border-radius: 4px; cursor: pointer;">
                            Qayta Login
                        </button>
                    </div>
                `;
        }
    } catch (error) {
        console.error('❌ Dashboard error:', error);
        container.innerHTML = `
            <div style="padding: 40px; color: var(--c-danger); text-align: center;">
                <h2>Xatolik!</h2>
                <p>${error.message}</p>
                <p style="font-size: 0.9rem; margin-top: 12px; color: var(--text-muted);">F12 dan console'ni ochilib error'ni ko'ring</p>
                <button onclick="location.reload()" style="margin-top: 20px; padding: 10px 20px; background: var(--c-primary); color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Qayta yuklash
                </button>
            </div>
        `;
    }
    
    return container;
}

window.addEventListener('popstate', () => {
    navigateTo(window.location.pathname);
});

// Handle unhandled errors - log but don't show toasts for resource errors
window.addEventListener('error', (event) => {
    console.error('❌ Global Error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('❌ Unhandled Promise Rejection:', event.reason);
});

// Add spin animation if not already present
if (!document.querySelector('style[data-spin-animation]')) {
    const style = document.createElement('style');
    style.setAttribute('data-spin-animation', 'true');
    style.innerHTML = `
        @keyframes spin { 100% { transform: rotate(360deg); } }
        @keyframes fadeOut { to { opacity: 0; } }
    `;
    document.head.appendChild(style);
}

// Boot when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
