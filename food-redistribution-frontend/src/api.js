// This file will be used to configure Axios for API calls to the Flask backend
import store from './store';
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api', // Flask backend API
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include JWT token if present
api.interceptors.request.use((config) => {
  let token = store.state.token;
  if (!token) {
    const user = JSON.parse(localStorage.getItem('user'));
    token = user?.token;
  }
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
