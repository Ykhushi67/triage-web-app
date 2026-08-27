import api from './client';
export const getAnalyticsOverview = () => api.get('/analytics/overview');
