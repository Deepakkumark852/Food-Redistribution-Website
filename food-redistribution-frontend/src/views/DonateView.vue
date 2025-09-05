<template>
  <div class="container py-5">
    <div class="row g-5">
      <div class="col-lg-4 order-lg-2">
        <h3 class="mb-4">Donation History</h3>
        <HistorySidebar />
      </div>
      <div class="col-lg-8 order-lg-1">
        <div class="card form-card">
          <div class="card-body p-4 p-md-5">
            <h2 class="card-title text-center mb-4"><i class="fas fa-gift me-2 text-primary"></i>Create a Donation</h2>
            <form @submit.prevent="donate" class="needs-validation" novalidate>
              <div class="row g-3">
                <div class="col-md-6">
                  <div class="form-floating">
                    <input v-model="food_name" type="text" class="form-control" id="food_name" placeholder="e.g., Bread, Apples" required />
                    <label for="food_name">Food Item Name</label>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="form-floating">
                    <input v-model.number="original_quantity" type="number" class="form-control" id="original_quantity" min="1" placeholder="10" required />
                    <label for="original_quantity">Quantity (servings)</label>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="form-floating">
                    <input v-model="expiry_date" type="date" class="form-control" id="expiry_date" required :min="today" />
                    <label for="expiry_date">Best Before</label>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="form-floating">
                    <input type="datetime-local" class="form-control" id="pickup_window_start" v-model="pickup_window_start" required :min="now">
                    <label for="pickup_window_start">Pickup From</label>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="form-floating">
                    <input type="datetime-local" class="form-control" id="pickup_window_end" v-model="pickup_window_end" required :min="pickup_window_start">
                    <label for="pickup_window_end">Pickup Until</label>
                  </div>
                </div>
                 <div class="col-12">
                  <label class="form-label">Pickup Location</label>
                  <GoogleMapPicker v-model="location" aspect-ratio="16/9" placeholder="Search or pick location..." />
                </div>
                <div class="col-12">
                  <div class="form-floating">
                    <textarea v-model="special_instructions" class="form-control" id="special_instructions" placeholder="Instructions" style="height: 100px"></textarea>
                    <label for="special_instructions">Special Instructions (optional)</label>
                  </div>
                </div>
                <div class="col-12">
                  <FoodImageUploader v-model="food_image_base64" />
                </div>
              </div>

              <div v-if="error" class="alert alert-danger mt-4">{{ error }}</div>
              <div v-if="success" class="alert alert-success mt-4">{{ success }}</div>

              <div class="d-grid mt-4">
                <button type="submit" class="btn btn-primary btn-lg">
                  <i class="fas fa-paper-plane me-2"></i>Submit Donation
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue';
import api from '../api';
import HistorySidebar from '../components/HistorySidebar.vue';
import GoogleMapPicker from '../components/GoogleMapPicker.vue';
import FoodImageUploader from '../components/FoodImageUploader.vue';

const food_name = ref('');
const original_quantity = ref(1);
const expiry_date = ref('');
const pickup_window_start = ref('');
const pickup_window_end = ref('');
const special_instructions = ref('');
const error = ref('');
const success = ref('');
const location = ref({ address: '', lat: null, lng: null });
const food_image_base64 = ref('');

const donate = async () => {
  error.value = '';
  success.value = '';
  try {
    const payload = {
      food_name: food_name.value,
      original_quantity: original_quantity.value,
      expiry_date: expiry_date.value,
      pickup_address: location.value.address,
      pickup_window_start: pickup_window_start.value,
      pickup_window_end: pickup_window_end.value,
      special_instructions: special_instructions.value,
      latitude: location.value.lat,
      longitude: location.value.lng,
    };
    if (food_image_base64.value) {
      payload.food_image_base64 = food_image_base64.value;
    }
    await api.post('/donate', payload);
    success.value = 'Donation submitted successfully!';
    // Reset form
    food_name.value = '';
    original_quantity.value = 1;
    expiry_date.value = '';
    pickup_window_start.value = '';
    pickup_window_end.value = '';
    special_instructions.value = '';
    location.value = { address: '', lat: null, lng: null };
    food_image_base64.value = '';
  } catch (e) {
    error.value = e.response?.data?.error || 'An error occurred.';
  }
};
</script>
<style scoped>
.card { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.btn-primary { background-color: #4F46E5; border-color: #4F46E5; }
</style>
