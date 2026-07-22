import axios from 'axios';
import { API } from '../utils/constants';

const api = axios.create({
  baseURL: API,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor: attach JWT token
// SECURITY NOTE: JWT is stored in localStorage for simplicity.
// This is acceptable for an intranet tool behind network access controls.
// For internet-facing deployments, migrate to httpOnly cookies with CSRF protection.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401 -> redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
