import api from './client';
export const login = (email, password) => api.post('/auth/login', { email, password });
