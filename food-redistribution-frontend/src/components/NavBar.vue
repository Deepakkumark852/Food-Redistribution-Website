<template>
  <nav class="navbar navbar-expand-lg fixed-top navbar-dark">
    <div class="container-fluid">
      <router-link class="navbar-brand d-flex align-items-center" to="/home">
        <i class="fas fa-hands-helping me-2"></i> FoodShare
      </router-link>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item">
            <router-link class="nav-link" to="/home">Home</router-link>
          </li>
          <li v-if="isDonorOrAdmin" class="nav-item">
            <router-link class="nav-link" to="/donate">Donate</router-link>
          </li>
          <li v-if="isRequesterOrAdmin" class="nav-item">
            <router-link class="nav-link" to="/request">Request</router-link>
          </li>
          <li v-if="isVolunteerOrAdmin" class="nav-item">
            <router-link class="nav-link" to="/volunteer">Volunteer</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/history">History</router-link>
          </li>
        </ul>
        <ul class="navbar-nav ms-auto align-items-center">
          <template v-if="store.getters.isAuthenticated">
            <li class="nav-item d-flex align-items-center me-3">
              <span class="nav-link d-flex align-items-center">
                <i class="fas fa-user-circle me-2 fs-5"></i>
                <span>{{ username }}</span>
              </span>
            </li>
            <li class="nav-item">
              <a class="nav-link" href="#" @click.prevent="showProfile = true" title="Profile">
                <i class="fas fa-id-badge fs-5"></i>
              </a>
            </li>
            <li class="nav-item">
              <a class="nav-link" href="#" @click.prevent="logout" title="Logout">
                <i class="fas fa-sign-out-alt fs-5"></i>
              </a>
            </li>
          </template>
          <template v-else>
            <li class="nav-item">
              <router-link class="btn btn-outline-light btn-sm" to="/login">Login</router-link>
            </li>
          </template>
        </ul>
      </div>
    </div>
    <ProfileModal v-if="showProfile && store.getters.isAuthenticated" :show="showProfile" @close="showProfile = false" />
  </nav>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import ProfileModal from './ProfileModal.vue';
import api from '../api';

const store = useStore();
const router = useRouter();
const roles = computed(() => store.state.roles || []);
const username = computed(() => store.state.username);
const showProfile = ref(false);

const notifications = ref([]);
const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length);

const isDonorOrAdmin = computed(() => roles.value.includes('donor') || roles.value.includes('admin'));
const isRequesterOrAdmin = computed(() => roles.value.includes('requester') || roles.value.includes('admin'));
const isVolunteerOrAdmin = computed(() => roles.value.includes('volunteer') || roles.value.includes('admin'));

const fetchNotifications = async () => {
  if (store.getters.isAuthenticated) {
    try {
      const response = await api.get('/notifications');
      notifications.value = response.data.notifications;
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      notifications.value = []; // Ensure it's an array on failure
    }
  }
};

const markAsRead = async (notification) => {
  if (!notification.is_read) {
    try {
      await api.post(`/notifications/${notification.id}/read`);
      notification.is_read = true;
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  }
  // Optional: navigate to a relevant page
  // router.push(notification.link);
};

const timeAgo = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);
  let interval = seconds / 31536000;
  if (interval > 1) return Math.floor(interval) + " years ago";
  interval = seconds / 2592000;
  if (interval > 1) return Math.floor(interval) + " months ago";
  interval = seconds / 86400;
  if (interval > 1) return Math.floor(interval) + " days ago";
  interval = seconds / 3600;
  if (interval > 1) return Math.floor(interval) + " hours ago";
  interval = seconds / 60;
  if (interval > 1) return Math.floor(interval) + " minutes ago";
  return Math.floor(seconds) + " seconds ago";
};

onMounted(() => {
  if (store.getters.isAuthenticated) {
    fetchNotifications();
  }
});

const logout = () => {
  store.commit('logout');
  router.push('/login');
};
</script>

<style scoped>
.navbar {
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  transition: background 0.3s ease;
}

.navbar-brand {
  font-weight: 700;
  font-size: 1.5rem;
}

.nav-link {
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  transition: color 0.2s;
  position: relative;
}

.nav-link:hover,
.nav-link.router-link-exact-active {
  color: white;
}

.nav-link.router-link-exact-active::after {
  content: '';
  position: absolute;
  bottom: -5px;
  left: 10%;
  width: 80%;
  height: 2px;
  background: var(--secondary-color);
  border-radius: 2px;
}

.notification-badge {
  position: absolute;
  top: 10px;
  right: -5px;
  font-size: 0.6em;
}

.notification-dropdown {
  width: 350px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 20px var(--shadow-color);
  padding: 0;
}

.notification-dropdown .dropdown-item {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  white-space: normal;
  cursor: pointer;
}

.notification-dropdown .dropdown-item:last-child {
  border-bottom: none;
}

.notification-dropdown .dropdown-item.unread {
  background-color: #f0f8ff;
}

.notification-dropdown .dropdown-item:hover {
  background-color: #f8f9fa;
}

.dropdown-menu {
  border-radius: 12px;
  box-shadow: 0 8px 20px var(--shadow-color);
}
</style>
