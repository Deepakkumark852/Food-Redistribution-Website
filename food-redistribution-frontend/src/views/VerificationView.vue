<template>
  <div class="container py-5 text-center">
    <div v-if="loading" class="py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Verifying...</span>
      </div>
      <p class="mt-3 fs-5">Verifying your request, please wait...</p>
    </div>
    
    <div v-else-if="error" class="card shadow-sm border-danger mx-auto" style="max-width: 500px;">
      <div class="card-body p-4">
        <i class="fas fa-times-circle fa-3x text-danger mb-3"></i>
        <h2 class="card-title text-danger">Verification Failed</h2>
        <p class="card-text fs-5">{{ error }}</p>
        <p class="text-muted">This can happen if the link has expired, has already been used, or is invalid. Please contact support if you believe this is an error.</p>
        <router-link to="/" class="btn btn-primary mt-3">Go to Homepage</router-link>
      </div>
    </div>
    
    <div v-else-if="successMessage" class="card shadow-sm border-success mx-auto" style="max-width: 500px;">
      <div class="card-body p-4">
        <i class="fas fa-check-circle fa-3x text-success mb-3"></i>
        <h2 class="card-title text-success">Verification Successful!</h2>
        <p class="card-text fs-5">{{ successMessage }}</p>
        <p class="text-muted">Thank you for your confirmation. The status of the food transfer has been updated.</p>
        <router-link to="/" class="btn btn-success mt-3">Go to Homepage</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import api from '../api';

const route = useRoute();
const loading = ref(true);
const error = ref(null);
const successMessage = ref(null);

onMounted(async () => {
  const token = route.query.token;
  
  if (!token) {
    error.value = 'No verification token found in the URL.';
    loading.value = false;
    return;
  }
  
  try {
    const response = await api.post('/verify', { token });
    successMessage.value = response.data.msg;
  } catch (err) {
    error.value = err.response?.data?.error || 'An unknown error occurred during verification.';
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.container {
  min-height: 70vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.card {
  border-radius: 12px;
}
</style>
