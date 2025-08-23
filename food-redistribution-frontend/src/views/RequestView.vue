<template>
  <div class="container">
    <div class="row mb-4">
      <div class="col-12">
        <h2 class="mb-3"><i class="fas fa-utensils me-2"></i>Available Food Donations</h2>
        <!-- Search and Filters UI can be added here -->
      </div>
    </div>
    <div class="row">
      <!-- List of donations would go here, fetched from API -->
    </div>
    <div class="row justify-content-center">
      <div class="col-lg-8">
        <div class="card mb-4">
          <div class="card-header bg-white">
            <h4 class="my-1"><i class="fas fa-hands-helping me-2"></i> Request Food</h4>
          </div>
          <div class="card-body">
            <form @submit.prevent="requestFood">
              <div class="row mb-3">
                <div class="col-md-6">
                  <label for="food_id" class="form-label">Food ID</label>
                  <input v-model.number="food_id" type="number" class="form-control" id="food_id" required />
                </div>
                <div class="col-md-6">
                  <label for="quantity" class="form-label">Quantity</label>
                  <input v-model.number="quantity" type="number" class="form-control" id="quantity" min="1" required />
                </div>
              </div>
              <div class="mb-3">
                <label for="delivery_address" class="form-label">Delivery Address</label>
                <input v-model="delivery_address" class="form-control" id="delivery_address" required />
              </div>
              <div class="mb-3">
                <label for="transport" class="form-label">Transport</label>
                <select v-model="transport" class="form-select" id="transport">
                  <option value="self">Self</option>
                  <option value="arranged">Arranged</option>
                </select>
              </div>
              <div class="d-grid">
                <button type="submit" class="btn btn-primary">Request</button>
              </div>
              <div v-if="error" class="alert alert-danger mt-3">{{ error }}</div>
              <div v-if="success" class="alert alert-success mt-3">{{ success }}</div>
            </form>
          </div>
        </div>
      </div>
      <div class="col-md-4 mb-3 mb-md-0">
        <HistorySidebar />
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue';
import api from '../api';
import HistorySidebar from '../components/HistorySidebar.vue';
const food_id = ref('');
const quantity = ref(1);
const delivery_address = ref('');
const transport = ref('self');
const error = ref('');
const success = ref('');
const requestFood = async () => {
  error.value = '';
  success.value = '';
  try {
    await api.post('/request', { food_id: food_id.value, quantity: quantity.value, delivery_address: delivery_address.value, transport: transport.value });
    success.value = 'Request submitted!';
    food_id.value = '';
    quantity.value = 1;
    delivery_address.value = '';
    transport.value = 'self';
  } catch (e) {
    error.value = e.response?.data?.error || 'Request failed';
  }
};
</script>
<style scoped>
.card { box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px; }
.btn-primary { background-color: #4F46E5; border-color: #4F46E5; }
</style>
