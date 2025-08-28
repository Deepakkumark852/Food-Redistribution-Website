<template>
  <div class="container py-5 text-center">
    <div v-if="loading" class="py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-3">Verifying your action, please wait...</p>
    </div>
    
    <div v-else-if="error" class="card shadow-sm bg-danger text-white">
      <div class="card-body p-4">
        <h2 class="card-title"><i class="fas fa-times-circle me-2"></i>Verification Failed</h2>
        <p class="lead">{{ error }}</p>
        <p>The verification link may be invalid, expired, or has already been used. If you believe this is an error, please contact support.</p>
        <router-link to="/" class="btn btn-light mt-3">Go to Homepage</router-link>
      </div>
    </div>
    
    <div v-else-if="successMessage" class="card shadow-sm bg-success text-white">
      <div class="card-body p-4">
        <h2 class="card-title"><i class="fas fa-check-circle me-2"></i>Success!</h2>
        <p class="lead">{{ successMessage }}</p>
        <p>Thank you for your confirmation. The status has been updated.</p>
        <router-link to="/" class="btn btn-light mt-3">Go to Homepage</router-link>
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

const verifyToken = async () => {
  const token = route.query.token;
  
  if (!token) {
    error.value = 'No verification token was provided.';
    loading.value = false;
    return;
  }
  
  try {
    const response = await api.post('/verify', { token });
    successMessage.value = response.data.message || 'Action verified successfully!';
  } catch (err) {
    console.error('Verification error:', err);
    error.value = err.response?.data?.error || 'An unknown error occurred during verification.';
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  verifyToken();
});
</script>

<style scoped>
.card {
  border: none;
  border-radius: 12px;
  max-width: 600px;
  margin: 0 auto;
}
.card-title {
  font-weight: 600;
}
.lead {
  font-size: 1.25rem;
}
</style>
