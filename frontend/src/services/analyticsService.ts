import { api } from './api';

export const getTeacherOverview = async () => {
  const res = await api.get('/analytics/overview/teacher');
  return res.data;
};

export const getStudentOverview = async () => {
  const res = await api.get('/analytics/overview/student');
  return res.data;
};

export const getResearchMetrics = async () => {
  const res = await api.get('/research/metrics');
  return res.data;
};
