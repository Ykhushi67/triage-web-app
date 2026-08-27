import api from './client';
export const getPatientHistory = (patientId) => api.get(`/patients/${patientId}/history`);
export const submitIntake = (data) => api.post('/patients/intake', data);
