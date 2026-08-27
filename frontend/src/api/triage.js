import api from './client';
export const acceptTriage = (encounterId) => api.post('/triage/accept', { encounter_id: encounterId });
export const overrideTriage = (data) => api.post('/triage/override', data);
export const reassessPatient = (data) => api.post('/triage/reassess', data);
export const predictTriage = (data) => api.post('/triage/predict', data);
