<script setup>
import NavBar from './components/NavBar.vue';
</script>

<template>
  <div>
    <NavBar />
    <div class="container">
      <router-view />
    </div>
  </div>
</template>

<style scoped>
</style>
