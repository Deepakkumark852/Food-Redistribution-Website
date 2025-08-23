<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="profile-modal card shadow-lg p-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="mb-0"><i class="fas fa-id-badge me-2"></i>Profile</h4>
        <button class="btn-close" @click="$emit('close')"></button>
      </div>
      <div class="mb-3">
        <label class="form-label">Username</label>
        <input class="form-control" v-model="form.username" disabled />
      </div>
      <div class="mb-3">
        <label class="form-label">Email</label>
        <input class="form-control" v-model="form.email" />
      </div>
      <div class="mb-3">
        <label class="form-label">Mobile</label>
        <input class="form-control" v-model="form.mobile" />
      </div>
      <div class="mb-3">
        <label class="form-label">Roles</label>
        <div class="d-flex flex-wrap gap-2">
          <span v-for="role in form.roles" :key="role" class="badge bg-primary">
            {{ role }}
            <button v-if="form.roles.length > 1" class="btn btn-sm btn-link text-light ms-1 p-0" @click="removeRole(role)" title="Remove role">
              <i class="fas fa-times"></i>
            </button>
          </span>
        </div>
      </div>
      <div class="mb-3">
        <label class="form-label">Add Role</label>
        <div class="input-group">
          <select class="form-select" v-model="newRole">
            <option value="">Select role</option>
            <option v-for="role in availableRoles" :key="role" :value="role" :disabled="form.roles.includes(role)">{{ role.charAt(0).toUpperCase() + role.slice(1) }}</option>
          </select>
          <button class="btn btn-outline-primary" type="button" @click="addRole" :disabled="!newRole || form.roles.includes(newRole)">Add</button>
        </div>
      </div>
      <div v-if="newRole === 'admin'" class="mb-3">
        <label class="form-label">Admin Special Key</label>
        <input class="form-control" v-model="specialKey" type="password" placeholder="Enter special key" />
      </div>
      <div class="d-flex justify-content-between gap-2">
        <button class="btn btn-secondary" @click="$emit('close')">Close</button>
        <button class="btn btn-outline-primary" @click="showPasswordModal = true">Change Password</button>
        <button class="btn btn-primary" @click="saveProfile">Save</button>
      </div>
      <div v-if="error" class="alert alert-danger mt-3">{{ error }}</div>
      <div v-if="success" class="alert alert-success mt-3">{{ success }}</div>
      <PasswordChangeModal v-if="showPasswordModal" @close="showPasswordModal = false" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useStore } from 'vuex';
import api from '../api';
import PasswordChangeModal from './PasswordChangeModal.vue';

const store = useStore();
const form = ref({
  username: store.state.username,
  email: '',
  mobile: '',
  roles: [],
});
const availableRoles = ['donor', 'requester', 'volunteer', 'admin'];
const newRole = ref('');
const specialKey = ref('');
const error = ref('');
const success = ref('');
const showPasswordModal = ref(false);

const roles = computed(() => store.state.roles || []);

const fetchProfile = async () => {
  try {
    const res = await api.get('/profile');
    form.value.email = res.data.email;
    form.value.mobile = res.data.mobile;
    form.value.roles = Array.isArray(res.data.roles) ? res.data.roles : (res.data.role ? [res.data.role] : []);
  } catch (e) {
    error.value = 'Failed to load profile.';
  }
};
onMounted(fetchProfile);

const addRole = () => {
  if (newRole.value && !form.value.roles.includes(newRole.value)) {
    form.value.roles.push(newRole.value);
    newRole.value = '';
  }
};

const removeRole = (role) => {
  if (form.value.roles.length > 1) {
    form.value.roles = form.value.roles.filter(r => r !== role);
  }
};

const saveProfile = async () => {
  error.value = '';
  success.value = '';
  try {
    const payload = {
      email: form.value.email,
      mobile: form.value.mobile,
      roles: form.value.roles,
      special_key: specialKey.value,
    };
    const res = await api.post('/profile/edit', payload);
    success.value = 'Profile updated!';
    if (res.data.roles) {
      store.commit('setUser', {
        token: store.state.token,
        roles: res.data.roles,
        username: store.state.username,
      });
    }
    specialKey.value = '';
  } catch (e) {
    error.value = e.response?.data?.error || 'Update failed.';
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
