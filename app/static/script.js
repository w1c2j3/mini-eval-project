const API_BASE = '/api/v1';

function getToken() {
    return localStorage.getItem('access_token');
}

function setToken(token) {
    localStorage.setItem('access_token', token);
}

function logout() {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
}

async function apiCall(endpoint, method = 'GET', body = null, isFileUpload = false) {
    const headers = {};
    const token = getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const options = { method, headers };

    if (body) {
        if (isFileUpload) {
            options.body = body; // FormData handles content-type
        } else {
            headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }
    }

    const response = await fetch(`${API_BASE}${endpoint}`, options);
    
    if (response.status === 401) {
        logout();
        return null;
    }
    
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'API Error');
    }

    return response.json();
}

function checkAuth() {
    if (!getToken() && window.location.pathname !== '/login') {
        window.location.href = '/login';
    }
}

