<template>
  <div class="home-container d-flex flex-column align-items-center justify-content-center py-5">
    <div class="welcome-card card shadow-lg p-4 mb-4 text-center">
      <i class="fas fa-hands-helping fa-3x mb-3" style="color: #4F46E5;"></i>
      <h1 class="mb-3">Welcome to Food Redistribution!</h1>
      <p class="lead mb-0">Together, we can reduce food waste and fight hunger.</p>
      <blockquote class="blockquote mt-4 mb-0">
        <p>"The best way to find yourself is to lose yourself in the service of others."</p>
        <footer class="blockquote-footer">Mahatma Gandhi</footer>
      </blockquote>
    </div>
  </div>
</template>

<script setup>
// No script needed for static home
</script>

<style scoped>
.home-container {
  min-height: 70vh;
}
.welcome-card {
  max-width: 600px;
  background: #fff;
  border-radius: 18px;
  border: none;
}
.blockquote {
  font-size: 1.1rem;
  color: #4F46E5;
}
</style>
