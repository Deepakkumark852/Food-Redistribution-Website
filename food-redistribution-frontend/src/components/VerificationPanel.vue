<template>
  <div class="card shadow-sm mb-4">
    <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
      <h3 class="mb-0"><i class="fas fa-tasks me-2"></i>Pending Verifications</h3>
      <button class="btn btn-light btn-sm" @click="fetchPendingVerifications" :disabled="loading">
        <i class="fas fa-sync-alt" :class="{'fa-spin': loading}"></i>
      </button>
    </div>
    <div v-if="loading" class="card-body text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <div v-else-if="error" class="card-body">
      <div class="alert alert-danger">{{ error }}</div>
    </div>
    <div v-else-if="verifications.length === 0" class="card-body text-center text-muted py-4">
      <p class="mb-0">You have no pending verifications at this time.</p>
    </div>
    <ul v-else class="list-group list-group-flush">
      <li v-for="verification in verifications" :key="verification.id" class="list-group-item d-flex justify-content-between align-items-center p-3">
        <div>
          <p class="mb-1">
            Awaiting your confirmation for the <strong>{{ verification.type }}</strong> of <strong>{{ verification.food_name }}</strong>.
          </p>
          <small class="text-muted">Requested on: {{ formatDate(verification.created_at) }}</small>
        </div>
        <button class="btn btn-sm btn-success" @click="confirmVerification(verification.token)" :disabled="isSubmitting === verification.token">
          <span v-if="isSubmitting === verification.token" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
          <i v-else class="fas fa-check me-1"></i>
          Confirm
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../api';

const verifications = ref([]);
const loading = ref(true);
const error = ref(null);
const isSubmitting = ref(null);

const fetchPendingVerifications = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await api.get('/verifications/pending');
    // The backend needs to return the token for each verification
    verifications.value = response.data.verifications;
  } catch (err) {
    error.value = 'Failed to load pending verifications.';
    console.error(err);
  } finally {
    loading.value = false;
  }
};

const confirmVerification = async (token) => {
  if (!token) {
    alert('Error: This verification is missing a token.');
    return;
  }
  isSubmitting.value = token;
  try {
    await api.post('/verify', { token });
    alert('Verification successful!');
    await fetchPendingVerifications(); // Refresh the list
  } catch (err) {
    alert(err.response?.data?.error || 'Verification failed.');
    console.error(err);
  } finally {
    isSubmitting.value = null;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

onMounted(() => {
  fetchPendingVerifications();
});
</script>

<style scoped>
.card-header {
  border-bottom: none;
}
.list-group-item {
  transition: background-color 0.2s;
}
.list-group-item:hover {
  background-color: #f8f9fa;
}
.fa-sync-alt.fa-spin {
  animation: fa-spin 1.5s infinite linear;
}
</style>
