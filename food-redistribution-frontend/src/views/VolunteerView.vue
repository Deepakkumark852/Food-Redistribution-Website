<template>
  <div class="container">
    <div class="row">
      <div class="col-12">
        <h2 class="mb-4"><i class="fas fa-people-carry me-2"></i>Volunteer Dashboard</h2>
      </div>
    </div>
    <div class="row">
      <div class="col-md-6">
        <div class="card mb-4">
          <div class="card-header bg-white">
            <h5 class="my-1">Pending Requests</h5>
          </div>
          <div class="card-body">
            <!-- Pending requests list from API goes here -->
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card mb-4">
          <div class="card-header bg-white">
            <h5 class="my-1">My Assignments</h5>
          </div>
          <div class="card-body">
            <!-- My assignments list from API goes here -->
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
// You can use axios/api.js to fetch data for volunteer dashboard
</script>
<style scoped>
.card { box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px; }
.badge-pending { background-color: #FFC107; color: #000; }
.badge-assigned { background-color: #0D6EFD; }
.badge-completed { background-color: #198754; }
</style>
