import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
});

export const setAuthRole = (role: 'teacher' | 'student', id: string) => {
  if (role === 'teacher') {
    api.defaults.headers.common['X-Teacher-ID'] = id;
    delete api.defaults.headers.common['X-Student-ID'];
  } else {
    api.defaults.headers.common['X-Student-ID'] = id;
    delete api.defaults.headers.common['X-Teacher-ID'];
  }
};
