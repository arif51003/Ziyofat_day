import { store, showToast, API_BASE } from './store.js';

export async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = {
        'Content-Type': 'application/json',
    };

    if (store.token) {
        headers['Authorization'] = `Bearer ${store.token}`;
    }

    const config = {
        method,
        headers,
        credentials: 'include', // let the browser store/send the admin session cookie set by /auth/login/
    };

    if (body) {
        // Special case for URL encoded form (OAuth2 Password Bearer)
        if (body instanceof URLSearchParams) {
            delete headers['Content-Type']; // Let browser set form-urlencoded
            headers['Content-Type'] = 'application/x-www-form-urlencoded';
            config.body = body.toString();
        } else {
            config.body = JSON.stringify(body);
        }
    }

    try {
        console.log(`API Call: ${method} ${endpoint}`);
        
        const response = await fetch(`${API_BASE}${endpoint}`, config);
        console.log(`API Response: ${response.status} ${endpoint}`);
        
        let data;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            data = { detail: text };
        }

        if (!response.ok) {
            // Handle token expiration / 401
            if (response.status === 401) {
                store.logout();
                window.dispatchEvent(new CustomEvent('navTo', { detail: '/login' }));
                throw new Error("Sessiya muddati tugadi. Iltimos qayta kiring.");
            }
            
            // Handle 404
            if (response.status === 404) {
                console.error(`API 404: ${method} ${endpoint}`, data);
                throw new Error(data.detail || `Endpoint topilmadi: ${endpoint}`);
            }
            
            throw new Error(data.detail || `API xatosi: ${response.status}`);
        }

        return data;
    } catch (error) {
        console.error(`API Error (${method} ${endpoint}):`, error.message);
        // Only show toast if it's not an already-handled error
        if (!error.message.includes('Sessiya muddati')) {
            showToast(error.message, 'error');
        }
        throw error;
    }
}

export { showToast };
