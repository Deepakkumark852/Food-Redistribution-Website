<template>
  <div class="verification-panel">
    <div class="card shadow-sm">
      <div class="card-header bg-warning text-dark">
        <h6 class="mb-0">
          <i class="fas fa-exclamation-triangle me-2"></i>
          Verification Required
        </h6>
      </div>
      <div class="card-body p-3">
        <div v-if="verifications.length === 0" class="text-muted text-center py-2">
          <small>No pending verifications</small>
        </div>
        
        <div v-for="verification in verifications" :key="verification.id" class="verification-item mb-3">
          <div class="d-flex justify-content-between align-items-start">
            <div class="flex-grow-1">
              <h6 class="mb-1">{{ verification.food_name }}</h6>
              <div class="small text-muted mb-2">
                <div v-if="verification.verification_type === 'pickup'">
                  <strong>Volunteer:</strong> {{ verification.volunteer_name }}<br>
                  <strong>Action:</strong> Confirm pickup completion
                </div>
                <div v-else>
                  <strong>Volunteer:</strong> {{ verification.volunteer_name }}<br>
                  <strong>Action:</strong> Confirm delivery received
                </div>
              </div>
              <div class="d-grid">
                <button 
                  class="btn btn-sm"
                  :class="verification.verification_type === 'pickup' ? 'btn-success' : 'btn-primary'"
                  @click="verifyAction(verification)"
                  :disabled="verifying === verification.id"
                >
                  <i v-if="verifying === verification.id" class="fas fa-spinner fa-spin me-1"></i>
                  <i v-else-if="verification.verification_type === 'pickup'" class="fas fa-check me-1"></i>
                  <i v-else class="fas fa-box me-1"></i>
                  {{ getVerificationButtonText(verification) }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import api from '../api';

const verifications = ref([]);
const verifying = ref(null);
let pollInterval = null;

const getVerificationButtonText = (verification) => {
  if (verifying.value === verification.id) {
    return 'Verifying...';
  }
  return verification.verification_type === 'pickup' ? 'Confirm Pickup' : 'Confirm Delivery';
};

const fetchVerifications = async () => {
  try {
    const response = await api.get('/pending-verifications');
    verifications.value = response.data.verifications || [];
  } catch (error) {
    console.error('Error fetching verifications:', error);
  }
};

const verifyAction = async (verification) => {
  verifying.value = verification.id;
  
  try {
    const endpoint = verification.verification_type === 'pickup' 
      ? '/donor/verify-pickup' 
      : '/requester/verify-delivery';
    
    await api.post(endpoint, { request_id: verification.id });
    
    // Remove from local list
    verifications.value = verifications.value.filter(v => v.id !== verification.id);
    
    // Show success message
    const action = verification.verification_type === 'pickup' ? 'Pickup' : 'Delivery';
    alert(`${action} verified successfully!`);
    
  } catch (error) {
    console.error('Error verifying action:', error);
    alert(error.response?.data?.error || 'Failed to verify action');
  } finally {
    verifying.value = null;
  }
};

onMounted(() => {
  fetchVerifications();
  
  // Poll for new verifications every 10 seconds
  pollInterval = setInterval(fetchVerifications, 10000);
});

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval);
  }
});
</script>

<style scoped>
.verification-panel {
  position: fixed;
  top: 80px;
  right: 20px;
  width: 300px;
  z-index: 999;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
  pointer-events: auto;
}

.verification-item {
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 0.75rem;
}

.verification-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.card {
  border: 2px solid #ffc107;
  animation: pulse-border 2s infinite;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  background: white;
}

@keyframes pulse-border {
  0% { border-color: #ffc107; }
  50% { border-color: #ffed4e; }
  100% { border-color: #ffc107; }
}

.btn-sm {
  font-size: 0.8rem;
  padding: 0.4rem 0.8rem;
}

/* Desktop - ensure panel doesn't overlap main content */
@media (min-width: 1400px) {
  .verification-panel {
    right: calc((100vw - 1320px) / 2 - 320px);
  }
}

@media (min-width: 1200px) and (max-width: 1399px) {
  .verification-panel {
    right: calc((100vw - 1140px) / 2 - 320px);
  }
}

@media (min-width: 992px) and (max-width: 1199px) {
  .verification-panel {
    width: 280px;
    right: 15px;
  }
}

@media (min-width: 768px) and (max-width: 991px) {
  .verification-panel {
    width: 260px;
    right: 10px;
    top: 70px;
  }
}

/* Mobile - non-overlapping positioning */
@media (max-width: 767px) {
  .verification-panel {
    position: relative;
    top: 0;
    right: 0;
    width: 100%;
    margin: 0 0 1rem 0;
    max-height: none;
    z-index: auto;
  }
}
</style>
