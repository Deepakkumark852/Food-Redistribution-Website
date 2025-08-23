<template>
  <nav class="navbar navbar-expand-lg navbar-dark mb-4">
    <div class="container">
      <router-link class="navbar-brand" to="/">FoodShare</router-link>
      <div class="collapse navbar-collapse">
        <ul class="navbar-nav me-auto">
          <li class="nav-item">
            <router-link class="nav-link" :class="{active: $route.path === '/donate'}" to="/donate">Donate</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" :class="{active: $route.path === '/request'}" to="/request">Request</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" :class="{active: $route.path === '/volunteer'}" to="/volunteer">Volunteer</router-link>
          </li>
        </ul>
        <ul class="navbar-nav">
          <li class="nav-item" v-if="username">
            <span class="nav-link">Hi, {{ username }}</span>
          </li>
          <li class="nav-item" v-if="username">
            <a class="nav-link" href="#" @click.prevent="logout">Logout</a>
          </li>
          <li class="nav-item" v-else>
            <router-link class="nav-link" to="/login">Login</router-link>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>
<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';
const router = useRouter();
const username = computed(() => localStorage.getItem('username'));
const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  localStorage.removeItem('role');
  router.push('/login');
};
</script>
