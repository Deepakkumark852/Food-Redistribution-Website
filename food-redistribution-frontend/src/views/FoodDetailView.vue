<template>
  <div class="container py-4">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
    </div>
    <div v-else-if="food" class="row justify-content-center">
      <div class="col-lg-8">
        <div class="card shadow-lg p-4">
          <div class="d-flex flex-column flex-md-row align-items-md-center justify-content-between mb-3">
            <div style="min-width:0;">
              <h2 class="mb-2">{{ food.food_name }}</h2>
              <div class="mb-1"><b>Quantity Available:</b> {{ food.remaining_quantity }} / {{ food.original_quantity }}</div>
              <div class="mb-1"><b>Expires:</b> {{ formatDate(food.expiry_date) }}</div>
              <div class="mb-1"><b>Pickup Address:</b> {{ food.pickup_address }}</div>
              <div class="mb-1"><b>Pickup Window:</b> {{ formatDateTime(food.pickup_window_start) }} - {{ formatDateTime(food.pickup_window_end) }}</div>
              <div class="mb-1"><b>Donor:</b> {{ food.donor_name || food.donor_id }}</div>
              <div v-if="food.donor_email" class="mb-1"><b>Email:</b> <a :href="`mailto:${food.donor_email}`">{{ food.donor_email }}</a></div>
              <div v-if="food.donor_mobile" class="mb-1"><b>Mobile:</b> <a :href="`tel:${food.donor_mobile}`">{{ food.donor_mobile }}</a></div>
              <div v-if="food.special_instructions" class="mb-1"><b>Instructions:</b> {{ food.special_instructions }}</div>
              <div v-if="food.created_at" class="mb-1"><b>Listed:</b> {{ formatDateTime(food.created_at) }}</div>
              <div v-if="food.latitude && food.longitude" class="mb-1">
                <a :href="`https://www.google.com/maps/dir/?api=1&destination=${food.latitude},${food.longitude}`" target="_blank" class="btn btn-sm btn-outline-success mt-2">Get Directions</a>
              </div>
            </div>
            <div v-if="food.food_image_base64" class="ms-md-4 mb-3 mb-md-0 text-center">
              <img :src="`data:image/jpeg;base64,${food.food_image_base64}`" alt="Food Image" style="max-width:180px; max-height:180px; border-radius:8px; object-fit:cover;" />
            </div>
            <div v-else-if="food.latitude && food.longitude" class="ms-md-4 mt-3 mt-md-0" style="min-width:180px;">
              <GoogleMapSingleMarker :lat="Number(food.latitude)" :lng="Number(food.longitude)" :markerTitle="food.food_name" aspect-ratio="16/9" />
            </div>
          </div>
          <div class="d-flex justify-content-between align-items-center mt-3">
            <router-link to="/request" class="btn btn-outline-primary">Back to List</router-link>
            <button class="btn btn-primary" @click="showRequestModal" v-if="food.remaining_quantity > 0">Request This Food</button>
          </div>
        </div>
      </div>
    </div>
    <RequestFoodModal
      v-if="food"
      ref="requestModal"
      :food-id="food.id"
      :max-servings="food.remaining_quantity"
      :pickup-address="food.pickup_address"
      :initial-location="{ lat: food.latitude, lng: food.longitude, address: food.pickup_address }"
      @request-submitted="onRequestSubmitted"
    />
    <div v-else class="alert alert-danger text-center">Food not found.</div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import api from '../api';
import GoogleMapSingleMarker from '../components/GoogleMapSingleMarker.vue';
import RequestFoodModal from '../components/RequestFoodModal.vue';
const route = useRoute();
const food = ref(null);
const loading = ref(true);
const requestModal = ref();
function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}
function formatDateTime(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}
function showRequestModal() {
  requestModal.value?.show();
}
function onRequestSubmitted() {
  // Optionally refresh food details or show a toast
}
onMounted(async () => {
  loading.value = true;
  try {
    const res = await api.get(`/food/${route.params.id}`);
    food.value = res.data;
  } catch (e) {
    food.value = null;
  }
  loading.value = false;
});
</script>
<style scoped>
.card { border-radius: 14px; }
</style>
