<template>
  <div class="home-container container-fluid px-0">
    <!-- Hero Section -->
    <section class="hero-section text-white text-center d-flex flex-column justify-content-center align-items-center">
      <h1 class="display-5 fw-bold text-white animate__animated animate__fadeInDown mb-4">Welcome, {{ username }}!</h1>
      <p class="lead mb-4 animate__animated animate__fadeInUp">Your actions today can fill a plate tomorrow. Let's make a difference together.</p>
      <div class="d-flex gap-3 animate__animated animate__fadeInUp animate__delay-1s">
        <button v-if="isDonorOrAdmin" @click="goTo('/donate')" class="btn btn-lg btn-light"><i class="fas fa-gift me-2"></i>Donate Food</button>
        <button v-if="isRequesterOrAdmin" @click="goTo('/request')" class="btn btn-lg btn-outline-light"><i class="fas fa-hand-holding-heart me-2"></i>Request Food</button>
      </div>
    </section>

    <!-- Main Content -->
    <div class="container py-5">
      <!-- Verification Panel for Donors and Requesters -->
      <VerificationPanel v-if="isDonorOrRequester" class="mb-5" />

      <!-- Quick Stats -->
      <section class="quick-stats text-center mb-5">
        <div class="row">
          <div class="col-md-4 mb-3">
            <div class="stat-card card h-100">
              <div class="card-body">
                <i class="fas fa-hands-helping fa-3x text-primary mb-3"></i>
                <h3 class="card-title">5,000+</h3>
                <p class="card-text">Meals Shared</p>
              </div>
            </div>
          </div>
          <div class="col-md-4 mb-3">
            <div class="stat-card card h-100">
              <div class="card-body">
                <i class="fas fa-users fa-3x text-success mb-3"></i>
                <h3 class="card-title">1,200+</h3>
                <p class="card-text">Community Members</p>
              </div>
            </div>
          </div>
          <div class="col-md-4 mb-3">
            <div class="stat-card card h-100">
              <div class="card-body">
                <i class="fas fa-truck fa-3x text-info mb-3"></i>
                <h3 class="card-title">800+</h3>
                <p class="card-text">Deliveries Completed</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <blockquote class="blockquote text-center mt-4 mb-0">
        <p class="fs-4">"The best way to find yourself is to lose yourself in the service of others."</p>
        <footer class="blockquote-footer fs-6">Mahatma Gandhi</footer>
      </blockquote>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import VerificationPanel from '../components/VerificationPanel.vue';

const store = useStore();
const router = useRouter();
const username = computed(() => store.getters.username);
const userRoles = computed(() => store.getters.roles);

const isDonorOrAdmin = computed(() => userRoles.value.includes('donor') || userRoles.value.includes('admin'));
const isRequesterOrAdmin = computed(() => userRoles.value.includes('requester') || userRoles.value.includes('admin'));

const goTo = (path) => {
  router.push(path);
};

const isDonorOrRequester = computed(() => {
  return userRoles.value.includes('donor') || userRoles.value.includes('requester');
});
</script>

<style scoped>
@import url('https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css');

.hero-section {
  min-height: 60vh;
  background: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url('https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?q=80&w=2070&auto=format&fit=crop') no-repeat center center;
  background-size: cover;
}

.stat-card.card {
  border: none;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card.card:hover {
  transform: translateY(-10px);
  box-shadow: 0 1rem 3rem rgba(0,0,0,.175)!important;
}

.blockquote {
  color: var(--text-light);
}

.blockquote-footer {
  color: var(--text-light);
}
</style>
