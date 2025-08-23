<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import NavBar from './components/NavBar.vue';

const route = useRoute();
const showNavBar = computed(() => !['/login', '/register'].includes(route.path));
</script>

<template>
  <div class="app-root d-flex flex-column min-vh-100">
    <NavBar v-if="showNavBar" />
    <main class="flex-fill d-flex flex-column align-items-center justify-content-center main-content">
      <router-view />
    </main>
  </div>
</template>

<style>
body, html, #app {
  height: 100%;
  margin: 0;
  padding: 0;
  background: #f6f8fa;
  min-height: 100vh;
  font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
  transition: background 0.3s;
}
.app-root {
  min-height: 100vh;
  background: #f6f8fa;
  transition: background 0.3s;
}
.main-content {
  width: 100%;
  min-height: 0;
  flex: 1 1 auto;
  padding-top: 2.5rem;
  padding-bottom: 2.5rem;
  transition: padding 0.3s, min-height 0.3s;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
}
@media (max-width: 768px) {
  .main-content {
    padding-top: 1rem;
    padding-bottom: 1rem;
  }
}
</style>
