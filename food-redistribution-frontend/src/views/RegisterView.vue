<template>
  <div class="auth-card card mt-5">
    <div class="card-body p-4">
      <div class="text-center mb-4">
        <i class="fas fa-utensils fa-3x" style="color: #4F46E5;"></i>
        <h2 class="mt-3">Create Account</h2>
      </div>
      <form @submit.prevent="register">
        <div class="mb-3">
          <label for="username" class="form-label">Username</label>
          <input v-model="username" type="text" class="form-control" id="username" required />
        </div>
        <div class="mb-3">
          <label for="password" class="form-label">Password</label>
          <input v-model="password" type="password" class="form-control" id="password" required />
        </div>
        <div class="mb-3">
          <label for="email" class="form-label">Email</label>
          <input v-model="email" type="email" class="form-control" id="email" required />
        </div>
        <div class="mb-3">
          <label for="mobile" class="form-label">Mobile Number</label>
          <input v-model="mobile" type="tel" class="form-control" id="mobile" required />
        </div>
        <div class="mb-3">
          <label for="role" class="form-label">Role</label>
          <select v-model="role" class="form-select" id="role">
            <option value="donor">Donor</option>
            <option value="requester">Requester</option>
            <option value="volunteer">Volunteer</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <div v-if="role === 'admin'" class="mb-3">
          <label for="specialKey" class="form-label">Admin Special Key</label>
          <input v-model="specialKey" type="password" class="form-control" id="specialKey" placeholder="Enter special key for admin" required />
        </div>
        <div class="d-grid gap-2">
          <button type="submit" class="btn btn-primary">Register</button>
        </div>
        <div v-if="error" class="alert alert-danger mt-3">{{ error }}</div>
        <div v-if="success" class="alert alert-success mt-3">{{ success }}</div>
      </form>
      <div class="text-center mt-3">
        Already have an account? <router-link to="/login">Login here</router-link>
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
const email = ref('');
const mobile = ref('');
const role = ref('donor');
const specialKey = ref('');
const error = ref('');
const success = ref('');
const router = useRouter();
const register = async () => {
  error.value = '';
  success.value = '';
  try {
    const payload = { username: username.value, password: password.value, email: email.value, mobile: mobile.value, role: role.value };
    if (role.value === 'admin') {
      payload.special_key = specialKey.value;
    }
    await api.post('/register', payload);
    success.value = 'Registration successful! Please login.';
    setTimeout(() => router.push('/login'), 1500);
  } catch (e) {
    error.value = e.response?.data?.error || 'Registration failed';
  }
};
</script>
<style scoped>
.auth-card { max-width: 400px; margin: 0 auto; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 8px; }
.btn-primary { background-color: #4F46E5; border-color: #4F46E5; }
</style>
