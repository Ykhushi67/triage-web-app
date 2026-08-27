import api from './client';
export const getSurgeStatus = () => api.get('/surge/status');
export const activateSurge = (data) => api.post('/surge/activate', data);
export const deactivateSurge = (data) => api.post('/surge/deactivate', data);
