<template>
  <div class="register-container">
    <div class="auth-card card">
      <div class="card-body p-4 p-md-5">
        <div class="text-center mb-4">
          <i class="fas fa-user-plus fa-3x text-white"></i>
          <h2 class="mt-3 text-white">Create Your Account</h2>
          <p class="text-white-50">Join our community</p>
        </div>
        <form @submit.prevent="register">
          <div class="row">
            <div class="col-md-6">
              <div class="form-floating mb-3">
                <input v-model="username" type="text" class="form-control" id="username" placeholder="Username" required />
                <label for="username">Username</label>
              </div>
            </div>
            <div class="col-md-6">
              <div class="form-floating mb-3">
                <input v-model="password" type="password" class="form-control" id="password" placeholder="Password" required />
                <label for="password">Password</label>
              </div>
            </div>
          </div>
          <div class="form-floating mb-3">
            <input v-model="email" type="email" class="form-control" id="email" placeholder="Email" required />
            <label for="email">Email</label>
          </div>
          <div class="form-floating mb-3">
            <input v-model="mobile" type="tel" class="form-control" id="mobile" placeholder="Mobile Number" required />
            <label for="mobile">Mobile Number</label>
          </div>
          <div class="form-floating mb-3">
            <select v-model="role" class="form-select" id="role">
              <option value="donor">Donor</option>
              <option value="requester">Requester</option>
              <option value="volunteer">Volunteer</option>
              <option value="admin">Admin</option>
            </select>
            <label for="role">I want to be a...</label>
          </div>
          <div v-if="role === 'admin'" class="form-floating mb-3">
            <input v-model="specialKey" type="password" class="form-control" id="specialKey" placeholder="Enter special key for admin" required />
            <label for="specialKey">Admin Special Key</label>
          </div>
          <div class="d-grid gap-2 mt-4">
            <button type="submit" class="btn btn-primary btn-lg">
              <i class="fas fa-check-circle me-2"></i>Register
            </button>
          </div>
          <div v-if="error" class="alert alert-danger mt-3 p-2 text-center">{{ error }}</div>
          <div v-if="success" class="alert alert-success mt-3 p-2 text-center">{{ success }}</div>
        </form>
        <div class="text-center mt-4">
          <span class="text-white-50">Already have an account? </span><router-link to="/login" class="login-link">Login here</router-link>
        </div>
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
.register-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  width: 100%;
  background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
  background-size: 400% 400%;
  animation: gradient 15s ease infinite;
  padding: 2rem 1rem;
}

@keyframes gradient {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.auth-card {
  max-width: 600px;
  width: 100%;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  color: white;
}

.form-control, .form-select {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  border-radius: 8px;
}

.form-control::placeholder, .form-select {
  color: rgba(255, 255, 255, 0.7);
}

.form-control:focus, .form-select:focus {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: none;
  color: white;
}

.form-select option {
  background: #333;
  color: white;
}

.form-floating > label {
  color: rgba(255, 255, 255, 0.7);
}

.btn-primary {
  background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
  border: none;
  transition: all 0.3s ease;
  padding: 12px;
  font-weight: 600;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.login-link {
  color: #a7c5ff;
  text-decoration: none;
  transition: color 0.2s;
}

.login-link:hover {
  color: #ffffff;
  text-decoration: underline;
}
</style>
