<template>
  <div class="login-container">
    <div class="auth-card card">
      <div class="card-body p-4 p-md-5">
        <div class="text-center mb-4">
          <i class="fas fa-hands-helping fa-3x text-white"></i>
          <h2 class="mt-3 text-white">Welcome Back</h2>
          <p class="text-white-50">Sign in to continue</p>
        </div>
        <form @submit.prevent="login">
          <div class="form-floating mb-3">
            <input v-model="username" type="text" class="form-control" id="username" placeholder="Username" required />
            <label for="username">Username</label>
          </div>
          <div class="form-floating mb-3">
            <input v-model="password" type="password" class="form-control" id="password" placeholder="Password" required />
            <label for="password">Password</label>
          </div>
          <div class="d-flex justify-content-between align-items-center mb-4">
            <div class="form-check">
              <input class="form-check-input" type="checkbox" id="remember" v-model="remember" />
              <label class="form-check-label text-white-50" for="remember">Remember me</label>
            </div>
            <a href="#" class="forgot-password-link">Forgot password?</a>
          </div>
          <div class="d-grid gap-2">
            <button type="submit" class="btn btn-primary btn-lg">
              <i class="fas fa-sign-in-alt me-2"></i>Login
            </button>
          </div>
          <div v-if="error" class="alert alert-danger mt-3 p-2 text-center">{{ error }}</div>
        </form>
        <div class="text-center mt-4">
          <span class="text-white-50">Don't have an account? </span><router-link to="/register" class="register-link">Register here</router-link>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue';
import api from '../api';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';

const username = ref('');
const password = ref('');
const remember = ref(false);
const error = ref('');
const router = useRouter();
const store = useStore();

const login = async () => {
  error.value = '';
  try {
    const res = await api.post('/login', { username: username.value, password: password.value });
    
    // Store user data in both Vuex store and localStorage for consistency
    const userData = {
      token: res.data.access_token,
      roles: res.data.roles,
      username: username.value,
    };
    
    store.commit('setUser', userData);
    
    // Also store in localStorage with 'user' key for API interceptor
    localStorage.setItem('user', JSON.stringify(userData));
    
    console.log('Login successful, token stored:', userData.token ? 'Yes' : 'No');
    router.push('/home');
  } catch (e) {
    error.value = e.response?.data?.error || 'Login failed';
  }
};
</script>
<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  width: 100%;
  background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
  background-size: 400% 400%;
  animation: gradient 15s ease infinite;
  padding: 1rem;
}

@keyframes gradient {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.auth-card {
  max-width: 450px;
  width: 100%;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  color: white;
}

.form-control {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  border-radius: 8px;
}

.form-control::placeholder {
  color: rgba(255, 255, 255, 0.7);
}

.form-control:focus {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: none;
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

.forgot-password-link, .register-link {
  color: #a7c5ff;
  text-decoration: none;
  transition: color 0.2s;
}

.forgot-password-link:hover, .register-link:hover {
  color: #ffffff;
  text-decoration: underline;
}

.form-check-input {
  background-color: rgba(255,255,255,0.2);
  border-color: rgba(255,255,255,0.3);
}
.form-check-input:checked {
  background-color: var(--secondary-color);
  border-color: var(--secondary-color);
}
</style>
