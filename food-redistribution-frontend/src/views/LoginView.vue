<template>
  <div class="auth-card card mt-5">
    <div class="card-body p-4">
      <div class="text-center mb-4">
        <i class="fas fa-utensils fa-3x" style="color: #4F46E5;"></i>
        <h2 class="mt-3">Welcome Back</h2>
      </div>
      <form @submit.prevent="login">
        <div class="mb-3">
          <label for="username" class="form-label">Username</label>
          <input v-model="username" type="text" class="form-control" id="username" required />
        </div>
        <div class="mb-3">
          <label for="password" class="form-label">Password</label>
          <input v-model="password" type="password" class="form-control" id="password" required />
        </div>
        <div class="d-flex justify-content-between mb-3">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" id="remember" v-model="remember" />
            <label class="form-check-label" for="remember">Remember me</label>
          </div>
          <a href="#">Forgot password?</a>
        </div>
        <div class="d-grid gap-2">
          <button type="submit" class="btn btn-primary">Login</button>
        </div>
        <div v-if="error" class="alert alert-danger mt-3">{{ error }}</div>
      </form>
      <div class="text-center mt-3">
        Don't have an account? <router-link to="/register">Register here</router-link>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue';
import api from '../api';
import { useRouter } from 'vue-router';
const username = ref('');
const password = ref('');
const remember = ref(false);
const error = ref('');
const router = useRouter();
const login = async () => {
  error.value = '';
  try {
    const res = await api.post('/login', { username: username.value, password: password.value });
    localStorage.setItem('token', res.data.access_token);
    localStorage.setItem('role', res.data.role);
    localStorage.setItem('username', username.value);
    router.push('/donate');
  } catch (e) {
    error.value = e.response?.data?.error || 'Login failed';
  }
};
</script>
<style scoped>
.auth-card { max-width: 400px; margin: 0 auto; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 8px; }
.btn-primary { background-color: #4F46E5; border-color: #4F46E5; }
</style>
