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
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      token = user?.token;
    } catch (e) {
      console.warn('Failed to parse user from localStorage:', e);
    }
  }
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    console.log('API request with token:', token.substring(0, 20) + '...');
  } else {
    console.warn('No token found for API request to:', config.url);
  }
  return config;
});

// Add a response interceptor to handle token errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error("Authentication error (401). Token is invalid or expired. Logging out.");
      // Prevent looping API calls by checking if we are already on the login page
      if (window.location.pathname !== '/login') {
        store.commit('logout');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Food Requests
export const submitFoodRequest = async (requestData) => {
  try {
    const response = await api.post('/requests', requestData);
    return response.data;
  } catch (error) {
    console.error('Error submitting food request:', error);
    throw error.response?.data || { error: 'Failed to submit request' };
  }
};

// Profile
export const changePassword = async (data) => {
  try {
    const response = await api.post('/profile/change_password', data);
    return response.data;
  } catch (error) {
    console.error('Error changing password:', error);
    throw error.response?.data || { error: 'Failed to change password' };
  }
};

// Notifications
export const getNotifications = async () => {
  try {
    const response = await api.get('/notifications');
    return response.data;
  } catch (error) {
    console.error('Error fetching notifications:', error);
    throw error.response?.data || { error: 'Failed to fetch notifications' };
  }
};

export const markNotificationAsRead = async (notificationId) => {
  try {
    const response = await api.post(`/notifications/${notificationId}/read`);
    return response.data;
  } catch (error) {
    console.error('Error marking notification as read:', error);
    throw error.response?.data || { error: 'Failed to mark notification as read' };
  }
};

export default api;
