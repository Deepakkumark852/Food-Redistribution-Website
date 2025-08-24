<template>
  <div class="container">
    <VerificationPanel />
    <div class="row">
      <div class="col-md-4 mb-3 mb-md-0">
        <HistorySidebar />
      </div>
      <div class="col-md-8">
        <div class="card mb-4">
          <div class="card-header bg-white">
            <h4 class="my-1"><i class="fas fa-donate me-2"></i> Donate Food</h4>
          </div>
          <div class="card-body">
            <form @submit.prevent="donate">
              <div class="row mb-3">
                <div class="col-md-6">
                  <label for="food_name" class="form-label">Food Item Name</label>
                  <input v-model="food_name" type="text" class="form-control" id="food_name" required />
                </div>
                <div class="col-md-6">
                  <label for="quantity" class="form-label">Quantity</label>
                  <div class="input-group">
                    <input v-model.number="quantity" type="number" class="form-control" id="quantity" min="1" required />
                    <span class="input-group-text">servings</span>
                  </div>
                </div>
              </div>
              <div class="row mb-3">
                <div class="col-md-6">
                  <label for="expiry_date" class="form-label">Best Before</label>
                  <input v-model="expiry_date" type="date" class="form-control" id="expiry_date" required />
                </div>
                <div class="col-md-6">
                  <label for="pickup_time" class="form-label">Pickup Time</label>
                  <input v-model="pickup_time" type="time" class="form-control" id="pickup_time" required />
                </div>
              </div>
              <div class="mb-3">
                <label class="form-label">Pickup Location</label>
                <GoogleMapPicker v-model="location" aspect-ratio="16/9" placeholder="Search or pick location..." />
              </div>
              <div class="mb-3">
                <label for="special_instructions" class="form-label">Special Instructions</label>
                <textarea v-model="special_instructions" class="form-control" id="special_instructions" rows="2"></textarea>
              </div>
              <div class="mb-3">
                <FoodImageUploader v-model="food_image_base64" />
              </div>
              <div class="d-grid">
                <button type="submit" class="btn btn-primary">Submit Donation</button>
              </div>
              <div v-if="error" class="alert alert-danger mt-3">{{ error }}</div>
              <div v-if="success" class="alert alert-success mt-3">{{ success }}</div>
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
import VerificationPanel from '../components/VerificationPanel.vue';

const food_name = ref('');
const quantity = ref(1);
const expiry_date = ref('');
const pickup_time = ref('');
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
      quantity: quantity.value,
      expiry_date: expiry_date.value,
      pickup_address: location.value.address,
      pickup_time: pickup_time.value,
      special_instructions: special_instructions.value,
      latitude: location.value.lat,
      longitude: location.value.lng
    };
    if (food_image_base64.value) {
      payload.food_image_base64 = food_image_base64.value;
    }
    await api.post('/donate', payload);
    success.value = 'Donation submitted!';
    food_name.value = '';
    quantity.value = 1;
    expiry_date.value = '';
    pickup_time.value = '';
    special_instructions.value = '';
    location.value = { address: '', lat: null, lng: null };
    food_image_base64.value = '';
  } catch (e) {
    error.value = e.response?.data?.error || 'Donation failed';
  }
};
</script>
<style scoped>
.card { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.btn-primary { background-color: #4F46E5; border-color: #4F46E5; }
</style>
