import { createRouter, createWebHistory } from 'vue-router';
import LoginView from '../views/LoginView.vue';
import RegisterView from '../views/RegisterView.vue';
import DonateView from '../views/DonateView.vue';
import RequestView from '../views/RequestView.vue';
import VolunteerView from '../views/VolunteerView.vue';

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginView },
  { path: '/register', component: RegisterView },
  { path: '/donate', component: DonateView },
  { path: '/request', component: RequestView },
  { path: '/volunteer', component: VolunteerView },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
