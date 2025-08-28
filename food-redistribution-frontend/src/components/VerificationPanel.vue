<template>
  <div class="verification-panel card shadow-sm mb-4">
    <div class="card-header bg-primary text-white">
      <h5 class="mb-0"><i class="fas fa-user-check me-2"></i>Pending Verifications</h5>
    </div>
    <div v-if="loading" class="card-body text-center">
      <div class="spinner-border spinner-border-sm" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <div v-else-if="verifications.length === 0" class="card-body">
      <p class="text-muted mb-0">You have no pending verifications.</p>
    </div>
    <ul v-else class="list-group list-group-flush">
      <li v-for="verification in verifications" :key="verification.id" class="list-group-item d-flex justify-content-between align-items-center">
        <div>
          <div><strong>{{ verification.food_name }}</strong></div>
          <small class="text-muted">
            Confirm {{ verification.type }} with volunteer <strong>{{ verification.volunteer_name }}</strong>.
          </small>
        </div>
        <button class="btn btn-sm btn-success" @click="confirmVerification(verification.token)" :disabled="isSubmitting">
          <span v-if="isSubmitting === verification.token" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
          <span v-else>Confirm</span>
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
const isSubmitting = ref(false);

const fetchPendingVerifications = async () => {
  loading.value = true;
  try {
    const response = await api.get('/verifications/pending');
    verifications.value = response.data.verifications;
  } catch (error) {
    console.error('Failed to fetch pending verifications:', error);
  } finally {
    loading.value = false;
  }
};

const confirmVerification = async (token) => {
  isSubmitting.value = token;
  try {
    await api.post('/verify', { token });
    alert('Confirmation successful!');
    // Refresh the list
    await fetchPendingVerifications();
  } catch (error) {
    console.error('Failed to confirm verification:', error);
    alert(error.response?.data?.error || 'Confirmation failed.');
  } finally {
    isSubmitting.value = false;
  }
};

onMounted(() => {
  fetchPendingVerifications();
});
</script>

<style scoped>
.verification-panel .card-header {
  font-weight: 500;
}
.list-group-item {
  padding: 1rem 1.25rem;
}
</style>
