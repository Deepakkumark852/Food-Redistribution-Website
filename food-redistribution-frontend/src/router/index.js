import { createRouter, createWebHistory } from 'vue-router';
import LoginView from '../views/LoginView.vue';
import RegisterView from '../views/RegisterView.vue';
import DonateView from '../views/DonateView.vue';
import RequestView from '../views/RequestView.vue';
import VolunteerView from '../views/VolunteerView.vue';
import VolunteerAssignmentView from '../views/VolunteerAssignmentView.vue';
import HistoryView from '../views/HistoryView.vue';
import HomeView from '../views/HomeView.vue';
import FoodDetailView from '../views/FoodDetailView.vue';
import VerificationView from '../views/VerificationView.vue';
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
  { path: '/volunteer/assignment/:id', component: VolunteerAssignmentView, meta: { roles: ['volunteer', 'admin'] } },
  { path: '/history', name: 'History', component: HistoryView, meta: { roles: ['donor', 'requester', 'volunteer', 'admin'] } },
  { path: '/food/:id', component: FoodDetailView, meta: { roles: ['donor', 'requester', 'volunteer', 'admin'] } },
  { path: '/home', name: 'Home', component: HomeView, meta: { requiresAuth: true } },
  { path: '/verify', name: 'Verify', component: VerificationView }, // Publicly accessible for email links
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Navigation guard for RBAC and session expiry
router.beforeEach((to, from, next) => {
  const { roles, requiresAuth } = to.meta;
  let isAuthenticated = store.getters.isAuthenticated;

  // Try to restore user from localStorage if the store is not yet populated
  if (!isAuthenticated && localStorage.getItem('user')) {
    try {
      const user = JSON.parse(localStorage.getItem('user'));
      if (user && user.token) {
        store.commit('setUser', user);
        isAuthenticated = true; // Update status after commit
      }
    } catch (e) {
      console.error("Failed to parse user from localStorage", e);
      localStorage.removeItem('user'); // Clear corrupted data
    }
  }

  const userRoles = store.getters.roles;

  // 1. If user is logged in and tries to access login/register, redirect to home
  if (isAuthenticated && (to.path === '/login' || to.path === '/register')) {
    return next('/home');
  }

  // 2. If route requires authentication and user is not logged in, redirect to login
  if (requiresAuth && !isAuthenticated) {
    return next('/login');
  }

  // 3. If route requires specific roles
  if (roles) {
    if (!isAuthenticated) {
      return next('/login'); // Should be caught by #2, but good for safety
    }
    
    const hasRequiredRole = userRoles.some(userRole => roles.includes(userRole));
    
    if (!hasRequiredRole) {
      // User does not have the required role, redirect to home
      return next('/home');
    }
  }

  // 4. Otherwise, allow navigation
  next();
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
