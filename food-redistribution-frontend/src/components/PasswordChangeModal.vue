<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="profile-modal card shadow-lg p-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0"><i class="fas fa-key me-2"></i>Change Password</h5>
        <button class="btn-close" @click="$emit('close')"></button>
      </div>
      <div class="mb-3">
        <label class="form-label">Current Password</label>
        <input class="form-control" v-model="currentPassword" type="password" />
      </div>
      <div class="mb-3">
        <label class="form-label">New Password</label>
        <input class="form-control" v-model="newPassword" type="password" />
      </div>
      <div class="mb-3">
        <label class="form-label">Confirm New Password</label>
        <input class="form-control" v-model="confirmPassword" type="password" />
      </div>
      <div class="d-flex justify-content-end gap-2">
        <button class="btn btn-secondary" @click="$emit('close')">Cancel</button>
        <button class="btn btn-primary" @click="changePassword">Change</button>
      </div>
      <div v-if="error" class="alert alert-danger mt-3">{{ error }}</div>
      <div v-if="success" class="alert alert-success mt-3">{{ success }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import api from '../api';

const currentPassword = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const error = ref('');
const success = ref('');

const changePassword = async () => {
  error.value = '';
  success.value = '';
  if (!currentPassword.value || !newPassword.value || !confirmPassword.value) {
    error.value = 'All fields are required.';
    return;
  }
  if (newPassword.value.length < 8) {
    error.value = 'New password must be at least 8 characters.';
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    error.value = 'New passwords do not match.';
    return;
  }
  try {
    await api.post('/profile/change_password', {
      current_password: currentPassword.value,
      new_password: newPassword.value,
    });
    success.value = 'Password changed successfully!';
    setTimeout(() => {
      $emit('close');
    }, 1200);
  } catch (e) {
    error.value = e.response?.data?.error || 'Password change failed.';
  }
};
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.25);
  z-index: 1050;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.profile-modal {
  min-width: 340px;
  max-width: 400px;
  background: #fff;
  border-radius: 14px;
  border: none;
  animation: popin 0.2s;
}
@keyframes popin {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style>
