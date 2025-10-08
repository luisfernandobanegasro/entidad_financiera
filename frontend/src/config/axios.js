// src/config/axios.js
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
});

// Agrega el access al header en cada request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token'); // usamos tu misma clave
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Si el access expira, intenta refrescar con refresh_token
let refreshing = null;
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config || {};
    // si 401 y no hemos intentado refrescar para este request
    if (error.response?.status === 401 && !original._retry) {
      if (!refreshing) {
        const refresh = localStorage.getItem('refresh_token');
        if (!refresh) throw error;
        refreshing = api.post('/api/auth/refresh/', { refresh })
          .then(({data}) => {
            localStorage.setItem('access_token', data.access);
            return data.access;
          })
          .finally(() => { refreshing = null; });
      }
      const newAccess = await refreshing;
      original._retry = true;
      original.headers = original.headers || {};
      original.headers.Authorization = `Bearer ${newAccess}`;
      return api(original);
    }
    throw error;
  }
);

export default api;
