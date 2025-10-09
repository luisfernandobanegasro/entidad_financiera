// src/config/axios.js
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000';

const api = axios.create({ baseURL: API_BASE });

/** Helpers para gestionar tokens desde cualquier parte */
export function setTokenPair({ access, refresh }) {
  if (access) localStorage.setItem('access_token', access);
  if (refresh) localStorage.setItem('refresh_token', refresh);
}
export function clearTokenPair() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

/** Request: añade /api si falta y Authorization si hay token */
api.interceptors.request.use((config) => {
  // Prefijo /api (por si alguna llamada viene sin él)
  const url = config.url || '';
  if (!url.startsWith('/api/')) {
    // evita doble slash si ya empieza en /
    config.url = '/api' + (url.startsWith('/') ? '' : '/') + url;
  }

  const token =
    localStorage.getItem('access_token') ||
    localStorage.getItem('access'); // tolerante con la otra clave

  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

/** Response: intenta refresh 1 sola vez si recibe 401 */
let refreshingPromise = null;

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config || {};
    const status = error.response?.status;

    // si el endpoint de refresh falla o ya reintentamos, salimos
    const isRefreshCall = original?.url?.includes('/auth/refresh/');
    if (status !== 401 || original._retry || isRefreshCall) {
      throw error;
    }

    // Si no hay refresh token, no podemos hacer nada
    const refresh = localStorage.getItem('refresh_token') || localStorage.getItem('refresh');
    if (!refresh) throw error;

    // Evita múltiples refresh concurrentes
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
