import api from './client';
export const getLiveQueue = () => api.get('/queue');
export const completeEncounter = (encounterId) => api.post(`/queue/${encounterId}/complete`);
