<template>
  <div class="food-detail-container container-fluid py-4 px-lg-5">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;"></div>
      <p class="mt-3 fs-5">Loading food details...</p>
    </div>
    
    <div v-else-if="food" class="animate__animated animate__fadeIn">
      <!-- Page Header -->
      <div class="page-header d-flex justify-content-between align-items-center mb-4">
        <div>
          <h1 class="fw-bold mb-1">{{ food.food_name }}</h1>
          <p class="text-muted mb-0">Donated by {{ food.donor_name || 'Anonymous' }}</p>
        </div>
        <router-link to="/request" class="btn btn-outline-secondary">
          <i class="fas fa-arrow-left me-2"></i>Back to Listings
        </router-link>
      </div>

      <div class="row g-4">
        <!-- Left Column: Image & Map -->
        <div class="col-lg-5">
          <div class="card shadow-sm h-100">
            <div v-if="food.food_image_base64" class="food-image-wrapper">
              <img :src="`data:image/jpeg;base64,${food.food_image_base64}`" alt="Food Image" class="food-image" />
            </div>
            <div class="card-body">
              <h5 class="card-title fw-bold"><i class="fas fa-map-marker-alt me-2 text-primary"></i>Pickup Location</h5>
              <p>{{ food.pickup_address }}</p>
              <div class="map-wrapper">
                <GoogleMapSingleMarker 
                  v-if="food.latitude && food.longitude"
                  :lat="Number(food.latitude)" 
                  :lng="Number(food.longitude)" 
                  :markerTitle="food.food_name" 
                  aspect-ratio="16/9" />
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: Details & Actions -->
        <div class="col-lg-7">
          <div class="card shadow-sm">
            <div class="card-body p-4">
              <div class="d-flex justify-content-between align-items-start mb-3">
                <div>
                  <h3 class="fw-bold">Item Details</h3>
                </div>
                <span class="badge fs-6 rounded-pill" :class="statusInfo.badgeClass">{{ statusInfo.text }}</span>
              </div>

              <div class="row g-3 detail-grid">
                <div class="col-md-6">
                  <div class="detail-item">
                    <i class="fas fa-cubes text-muted"></i>
                    <div>
                      <strong>Quantity Available</strong>
                      <p>{{ food.remaining_quantity }} / {{ food.original_quantity }} servings</p>
                    </div>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="detail-item">
                    <i class="fas fa-calendar-times text-muted"></i>
                    <div>
                      <strong>Expires On</strong>
                      <p>{{ formatDate(food.expiry_date) }}</p>
                    </div>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="detail-item">
                    <i class="fas fa-clock text-muted"></i>
                    <div>
                      <strong>Best Pickup Time</strong>
                      <p>{{ formatTime(food.pickup_window_start) }} - {{ formatTime(food.pickup_window_end) }}</p>
                    </div>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="detail-item">
                    <i class="fas fa-calendar-plus text-muted"></i>
                    <div>
                      <strong>Listed On</strong>
                      <p>{{ formatDateTime(food.created_at) }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="food.special_instructions" class="mt-4">
                <h5 class="fw-bold">Special Instructions</h5>
                <p class="fst-italic bg-light p-3 rounded">{{ food.special_instructions }}</p>
              </div>

              <div class="mt-4 d-grid">
                <button class="btn btn-primary btn-lg" @click="showRequestModal" :disabled="food.remaining_quantity <= 0">
                  <i class="fas fa-hand-holding-heart me-2"></i>
                  {{ food.remaining_quantity > 0 ? 'Request This Food' : 'Fully Claimed' }}
                </button>
              </div>
            </div>
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
    
    <div v-else-if="!loading" class="alert alert-danger text-center">
      <h4 class="alert-heading">Not Found</h4>
      <p>The food item you are looking for does not exist or has been removed.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../api';
import GoogleMapSingleMarker from '../components/GoogleMapSingleMarker.vue';
import RequestFoodModal from '../components/RequestFoodModal.vue';

const route = useRoute();
const router = useRouter();
const food = ref(null);
const loading = ref(true);
const requestModal = ref();

const statusInfo = computed(() => {
  if (!food.value) return { text: 'N/A', badgeClass: 'bg-secondary' };
  const { status, remaining_quantity } = food.value;
  if (status === 'fully_claimed' || remaining_quantity <= 0) {
    return { text: 'Fully Claimed', badgeClass: 'bg-danger' };
  }
  if (status === 'partially_claimed') {
    return { text: 'Partially Claimed', badgeClass: 'bg-warning text-dark' };
  }
  return { text: 'Available', badgeClass: 'bg-success' };
});

function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
}

function formatTime(dateStr) {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

function formatDateTime(dateStr) {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

function showRequestModal() {
  requestModal.value?.show();
}

function onRequestSubmitted() {
  // Refresh food details to show updated quantity
  fetchFoodDetails();
}

async function fetchFoodDetails() {
  loading.value = true;
  try {
    const res = await api.get(`/food/${route.params.id}`);
    food.value = res.data;
  } catch (e) {
    console.error("Failed to fetch food details:", e);
    food.value = null;
  }
  loading.value = false;
}

onMounted(fetchFoodDetails);
</script>

<style scoped>
@import url('https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css');

.food-detail-container {
  background-color: #f8f9fa;
}

.food-image-wrapper {
  width: 100%;
  aspect-ratio: 16 / 10;
  overflow: hidden;
}

.food-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.map-wrapper {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #dee2e6;
}

.detail-grid {
  font-size: 1rem;
}

.detail-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.detail-item i {
  font-size: 1.5rem;
  margin-top: 0.25rem;
}

.detail-item p {
  margin-bottom: 0;
  font-size: 0.95rem;
}
</style>
