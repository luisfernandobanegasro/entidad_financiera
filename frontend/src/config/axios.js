// src/config/axios.js
import axios from 'axios';

// ⚠️ NO pongas "/api" aquí. Sólo el host/puerto.
const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000';

const api = axios.create({ baseURL: API_BASE });

export function setTokenPair({ access, refresh }) {
  if (access) localStorage.setItem('access_token', access);
  if (refresh) localStorage.setItem('refresh_token', refresh);
}
export function clearTokenPair() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

api.interceptors.request.use((config) => {
  const url = config.url || '';

  // ✅ Si la URL ya es absoluta (http/https), no toques nada.
  if (/^https?:\/\//i.test(url)) {
    return config;
  }

  // ✅ Si ya empieza con /api/ tampoco toques nada
  if (!url.startsWith('/api/')) {
    // normaliza un solo slash
    const path = url.startsWith('/') ? url : `/${url}`;
    config.url = `/api${path}`;
  }

  const token =
    localStorage.getItem('access_token') ||
    localStorage.getItem('access');

  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// refresh 401 tal como ya lo tienes...
let refreshingPromise = null;
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config || {};
    const status = error.response?.status;
    const isRefreshCall = original?.url?.includes('/auth/refresh/');
    if (status !== 401 || original._retry || isRefreshCall) throw error;

    const refresh = localStorage.getItem('refresh_token') || localStorage.getItem('refresh');
    if (!refresh) throw error;

    if (!refreshingPromise) {
      refreshingPromise = api.post('/auth/refresh/', { refresh })
        .then(({ data }) => {
          const newAccess = data?.access;
          if (!newAccess) throw new Error('No access in refresh');
          localStorage.setItem('access_token', newAccess);
          return newAccess;
        })
        .finally(() => { refreshingPromise = null; });
    }

    const newAccess = await refreshingPromise;
    original._retry = true;
    original.headers = original.headers || {};
    original.headers.Authorization = `Bearer ${newAccess}`;
    return api(original);
  }
);

export default api;