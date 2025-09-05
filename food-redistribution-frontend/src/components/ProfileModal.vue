<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="profile-modal card shadow-lg animate__animated animate__fadeInUp">
      <div class="card-header bg-transparent border-0 text-center pt-4">
        <div class="profile-picture-wrapper mb-3">
          <i class="fas fa-user-circle fa-5x text-primary"></i>
          <!-- <img src="path/to/user-image.jpg" alt="Profile Picture" /> -->
        </div>
        <h3 class="fw-bold mb-0">{{ form.username }}</h3>
        <p class="text-muted">{{ form.email }}</p>
      </div>
      <div class="card-body px-4 pb-4">
        <form @submit.prevent="saveProfile">
          <div class="form-floating mb-3">
            <input type="email" class="form-control" id="profileEmail" placeholder="Email" v-model="form.email" />
            <label for="profileEmail">Email Address</label>
          </div>
          <div class="form-floating mb-3">
            <input type="text" class="form-control" id="profileMobile" placeholder="Mobile" v-model="form.mobile" />
            <label for="profileMobile">Mobile Number</label>
          </div>

          <div class="mb-3">
            <label class="form-label">Your Roles</label>
            <div class="d-flex flex-wrap gap-2">
              <span v-for="role in form.roles" :key="role" class="badge rounded-pill fs-6 text-capitalize" :class="`bg-${role.toLowerCase()}`">
                <i :class="getRoleIcon(role)" class="me-1"></i>
                {{ role }}
                <button v-if="form.roles.length > 1" class="btn-close btn-close-white ms-1" @click="removeRole(role)" title="Remove role"></button>
              </span>
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label">Add New Role</label>
            <div class="input-group">
              <select class="form-select" v-model="newRole">
                <option value="" disabled>Select a role to add...</option>
                <option v-for="role in availableRoles" :key="role" :value="role" :disabled="form.roles.includes(role)">
                  {{ role.charAt(0).toUpperCase() + role.slice(1) }}
                </option>
              </select>
              <button class="btn btn-outline-secondary" type="button" @click="addRole" :disabled="!newRole || form.roles.includes(newRole)">
                <i class="fas fa-plus"></i> Add
              </button>
            </div>
          </div>

          <div v-if="newRole === 'admin'" class="form-floating mb-3 animate__animated animate__fadeIn">
            <input class="form-control" id="specialKey" v-model="specialKey" type="password" placeholder="Enter special key" />
            <label for="specialKey">Admin Special Key</label>
          </div>

          <div v-if="error" class="alert alert-danger mt-3">{{ error }}</div>
          <div v-if="success" class="alert alert-success mt-3">{{ success }}</div>

          <div class="d-grid gap-2 mt-4">
            <button class="btn btn-primary" type="submit">
              <i class="fas fa-save me-2"></i>Save Changes
            </button>
            <button class="btn btn-outline-secondary" type="button" @click="showPasswordModal = true">
              <i class="fas fa-key me-2"></i>Change Password
            </button>
            <button class="btn btn-light mt-2" type="button" @click="$emit('close')">Close</button>
          </div>
        </form>
      </div>
    </div>
    <PasswordChangeModal v-if="showPasswordModal" @close="showPasswordModal = false" />
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
    // Do not reset newRole here to allow for admin key input
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
    };
    if (specialKey.value) {
      payload.special_key = specialKey.value;
    }
    const res = await api.post('/profile/edit', payload);
    success.value = 'Profile updated successfully!';
    if (res.data.roles) {
      store.commit('setUser', {
        token: store.state.token,
        roles: res.data.roles,
        username: store.state.username,
      });
    }
    specialKey.value = '';
    newRole.value = ''; // Reset after successful save
    setTimeout(() => success.value = '', 3000);
  } catch (e) {
    error.value = e.response?.data?.error || 'Update failed.';
  }
};

const getRoleIcon = (role) => {
  switch (role.toLowerCase()) {
    case 'admin': return 'fas fa-user-shield';
    case 'donor': return 'fas fa-hand-holding-heart';
    case 'requester': return 'fas fa-hand-paper';
    case 'volunteer': return 'fas fa-hands-helping';
    default: return 'fas fa-user';
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
  z-index: 1050;
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-modal {
  width: 100%;
  max-width: 420px;
  border-radius: 16px;
  border: none;
}

.profile-picture-wrapper {
  width: 100px;
  height: 100px;
  margin: 0 auto;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #e9ecef;
  overflow: hidden;
}

.profile-picture-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.badge .btn-close {
  font-size: 0.6em;
  padding: 0.5em;
}

.badge.bg-donor { background-color: #0d6efd; }
.badge.bg-requester { background-color: #198754; }
.badge.bg-volunteer { background-color: #ffc107; color: #000 !important; }
.badge.bg-admin { background-color: #6f42c1; }

</style>
