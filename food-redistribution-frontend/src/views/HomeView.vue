<template>
  <div class="home-container container py-5">
    <div class="welcome-card card shadow-lg p-4 mb-4 text-center">
      <i class="fas fa-hands-helping fa-3x mb-3" style="color: #4F46E5;"></i>
      <h1 class="mb-3">Welcome, {{ username }}!</h1>
      <p class="lead mb-0">Together, we can reduce food waste and fight hunger.</p>
    </div>

    <!-- Verification Panel for Donors and Requesters -->
    <VerificationPanel v-if="isDonorOrRequester" />

    <blockquote class="blockquote text-center mt-4 mb-0">
      <p>"The best way to find yourself is to lose yourself in the service of others."</p>
      <footer class="blockquote-footer">Mahatma Gandhi</footer>
    </blockquote>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useStore } from 'vuex';
import VerificationPanel from '../components/VerificationPanel.vue';

const store = useStore();
const username = computed(() => store.getters.username);
const userRoles = computed(() => store.getters.roles);

const isDonorOrRequester = computed(() => {
  return userRoles.value.includes('donor') || userRoles.value.includes('requester');
});
</script>

<style scoped>
.home-container {
  min-height: 70vh;
}
.welcome-card {
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
  background: #fff;
  border-radius: 18px;
  border: none;
}
.blockquote {
  font-size: 1.1rem;
  color: #4F46E5;
}
</style>
