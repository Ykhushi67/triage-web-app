import api from './client';
export const getAuditLogs = (skip = 0, limit = 50, action = null) => {
  const params = { skip, limit };
  if (action) params.action = action;
  return api.get('/audit', { params });
};
export const getPatientTimeline = (patientId, limit = 50) =>
  api.get(`/audit/patient/${patientId}`, { params: { limit } });
