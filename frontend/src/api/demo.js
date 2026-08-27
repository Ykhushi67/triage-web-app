import api from './client';
export const resetDemo = () => api.post('/demo/reset');
export const triggerDeterioration = () => api.post('/demo/trigger-deterioration');
export const triggerSurgeInflux = () => api.post('/demo/trigger-surge-influx');
