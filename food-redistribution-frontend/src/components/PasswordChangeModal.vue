<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="password-modal card shadow-lg p-4 animate__animated animate__fadeInUp">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h4 class="mb-0 fw-bold"><i class="fas fa-key me-2 text-primary"></i>Change Password</h4>
        <button class="btn-close" @click="$emit('close')"></button>
      </div>
      
      <form @submit.prevent="changePassword">
        <div class="form-floating mb-3">
          <input class="form-control" id="currentPassword" v-model="currentPassword" type="password" placeholder="Current Password" required />
          <label for="currentPassword">Current Password</label>
        </div>
        <div class="form-floating mb-3">
          <input class="form-control" id="newPassword" v-model="newPassword" type="password" placeholder="New Password" required />
          <label for="newPassword">New Password</label>
        </div>
        <div class="form-floating mb-3">
          <input class="form-control" id="confirmPassword" v-model="confirmPassword" type="password" placeholder="Confirm New Password" required />
          <label for="confirmPassword">Confirm New Password</label>
        </div>

        <div v-if="error" class="alert alert-danger mt-3 py-2">{{ error }}</div>
        <div v-if="success" class="alert alert-success mt-3 py-2">{{ success }}</div>

        <div class="d-grid gap-2 mt-4">
          <button class="btn btn-primary" type="submit" :disabled="isSubmitting">
            <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            {{ isSubmitting ? 'Changing...' : 'Change Password' }}
          </button>
          <button class="btn btn-light" type="button" @click="$emit('close')">Cancel</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, defineEmits } from 'vue';
import api from '../api';

const emit = defineEmits(['close']);

const currentPassword = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const error = ref('');
const success = ref('');
const isSubmitting = ref(false);

const changePassword = async () => {
  error.value = '';
  success.value = '';
  isSubmitting.value = true;

  if (!currentPassword.value || !newPassword.value || !confirmPassword.value) {
    error.value = 'All fields are required.';
    isSubmitting.value = false;
    return;
  }
  if (newPassword.value.length < 8) {
    error.value = 'New password must be at least 8 characters long.';
    isSubmitting.value = false;
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    error.value = 'New passwords do not match.';
    isSubmitting.value = false;
    return;
  }

  try {
    await api.post('/profile/change_password', {
      current_password: currentPassword.value,
      new_password: newPassword.value,
    });
    success.value = 'Password changed successfully!';
    setTimeout(() => {
      emit('close');
    }, 1500);
  } catch (e) {
    error.value = e.response?.data?.error || 'Password change failed. Please check your current password.';
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
@import url('https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css');

.modal-backdrop {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(5px);
  z-index: 1060; /* Higher than profile modal */
  display: flex;
  align-items: center;
  justify-content: center;
}

.password-modal {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 16px;
  border: none;
}
</style>
