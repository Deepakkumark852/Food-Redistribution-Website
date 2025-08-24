import { createRouter, createWebHistory } from 'vue-router';
import LoginView from '../views/LoginView.vue';
import RegisterView from '../views/RegisterView.vue';
import DonateView from '../views/DonateView.vue';
import RequestView from '../views/RequestView.vue';
import VolunteerView from '../views/VolunteerView.vue';
import AssignmentDetailsView from '../views/AssignmentDetailsView.vue';
import HistoryView from '../views/HistoryView.vue';
import HomeView from '../views/HomeView.vue';
import FoodDetailView from '../views/FoodDetailView.vue';
import api from '../api';
import store from '../store';

// Role-based route meta
const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginView },
  { path: '/register', component: RegisterView },
  { path: '/donate', component: DonateView, meta: { roles: ['donor', 'admin'] } },
  { path: '/request', component: RequestView, meta: { roles: ['requester', 'admin'] } },
  { path: '/volunteer', component: VolunteerView, meta: { roles: ['volunteer', 'admin'] } },
  { path: '/volunteer/assignment/:id', component: AssignmentDetailsView, meta: { roles: ['volunteer', 'admin'] } },
  { path: '/history', name: 'History', component: HistoryView, meta: { roles: ['donor', 'requester', 'volunteer', 'admin'] } },
  { path: '/food/:id', component: FoodDetailView, meta: { roles: ['donor', 'requester', 'volunteer', 'admin'] } },
  { path: '/home', name: 'Home', component: HomeView },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Navigation guard for RBAC and session expiry
router.beforeEach((to, from, next) => {
  const allowedRoles = to.meta.roles;
  if (!allowedRoles) return next(); // Public route

  // Restore user from localStorage if store is empty (e.g., on reload)
  if (!store.getters.isAuthenticated && localStorage.getItem('user')) {
    try {
      const user = JSON.parse(localStorage.getItem('user'));
      if (user && user.token && user.roles && user.username) {
        store.commit('setUser', user);
      }
    } catch (e) { /* ignore */ }
  }

  const userRoles = store.getters.roles;
  const token = store.getters.token;
  if (!token) {
    // No token, force login
    return next('/login');
  }
  if (allowedRoles.some(r => userRoles.includes(r))) {
    return next();
  } else {
    return next('/login');
  }
});

// Axios response interceptor for session expiry
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401 && error.response.data?.error?.includes('Session expired')) {
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      localStorage.removeItem('username');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default router;
