<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
    <div class="container-fluid">
      <router-link class="navbar-brand d-flex align-items-center" to="/home">
        <i class="fas fa-utensils me-2"></i> Food Redistribution
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
        <ul class="navbar-nav ms-auto">
          <template v-if="store.getters.isAuthenticated">
            <li class="nav-item d-flex align-items-center me-2">
              <span class="navbar-text text-light fw-semibold">
                <i class="fas fa-user-circle me-1"></i> {{ username }} <span v-if="role">({{ role }})</span>
              </span>
            </li>
            <li class="nav-item">
              <button class="btn btn-link text-light p-0 me-2" @click="showProfile = true" title="Profile">
                <i class="fas fa-id-badge fa-lg"></i>
              </button>
            </li>
            <li class="nav-item">
              <button class="btn btn-outline-light btn-sm" @click="logout">
                <i class="fas fa-sign-out-alt"></i> Logout
              </button>
            </li>
            <li class="nav-item dropdown" v-if="unreadCount > 0">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                <i class="fas fa-bell"></i>
                <span class="badge rounded-pill bg-danger">{{ unreadCount }}</span>
              </a>
              <ul class="dropdown-menu dropdown-menu-end">
                <li v-for="notification in notifications" :key="notification.id" class="dropdown-item" :class="{ 'text-muted': notification.is_read }" @click="markAsRead(notification)">
                  <small>
                    <template v-if="!notification.is_read">
                      <strong>{{ notification.title }}</strong>
                      <div>{{ notification.message }}</div>
                    </template>
                    <template v-else>
                      {{ notification.message }}
                    </template>
                  </small>
                </li>
                <li>
                  <hr class="dropdown-divider">
                </li>
                <li>
                  <a class="dropdown-item text-center" href="#" @click="markAllAsRead">Mark all as read</a>
                </li>
              </ul>
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
const role = computed(() => roles.value.length > 0 ? roles.value.join(', ') : '');
const showProfile = ref(false);

const notifications = ref([]);
const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length);

const isDonorOrAdmin = computed(() => roles.value.includes('donor') || roles.value.includes('admin'));
const isRequesterOrAdmin = computed(() => roles.value.includes('requester') || roles.value.includes('admin'));
const isVolunteerOrAdmin = computed(() => roles.value.includes('volunteer') || roles.value.includes('admin'));

const fetchNotifications = async () => {
  if (store.getters.isAuthenticated) {
    try {
      const response = await api.getNotifications();
      notifications.value = response.data.notifications;
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  }
};

const markAsRead = async (notification) => {
  if (!notification.is_read) {
    try {
      await api.markNotificationAsRead(notification.id);
      notification.is_read = true;
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  }
  // Navigate to the link if it exists
  if (notification.link) {
    router.push(notification.link);
  }
};

onMounted(() => {
  fetchNotifications();
  // Poll for new notifications every 60 seconds
  setInterval(fetchNotifications, 60000);
});

const logout = () => {
  store.commit('logout');
  router.push('/login');
};
</script>

<style scoped>
.navbar {
  font-size: 1.08rem;
  background: linear-gradient(90deg, #4F46E5 60%, #6366F1 100%);
}
.navbar-brand {
  font-weight: 700;
  font-size: 1.3rem;
  letter-spacing: 1px;
}
.nav-link {
  color: #fff !important;
  transition: color 0.2s;
}
.nav-link.router-link-exact-active, .nav-link.active {
  color: #FFD700 !important;
  font-weight: 600;
}
.btn-outline-light {
  border-radius: 20px;
  padding: 0.3rem 1.1rem;
  font-weight: 500;
}
.navbar-text {
  font-size: 1rem;
}
.btn-link {
  color: #fff;
  text-decoration: none;
}
.btn-link:hover {
  color: #FFD700;
}
.dropdown-item {
  cursor: pointer;
}
</style>
