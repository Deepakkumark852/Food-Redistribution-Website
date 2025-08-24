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
              <div class="mb-1"><b>Quantity:</b> {{ food.quantity }}</div>
              <div class="mb-1"><b>Expires:</b> {{ formatDate(food.expiry_date) }}</div>
              <div class="mb-1"><b>Pickup Address:</b> {{ food.pickup_address }}</div>
              <div class="mb-1"><b>Pickup Time:</b> {{ food.pickup_time }}</div>
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
          <div class="d-flex justify-content-between">
            <router-link to="/request" class="btn btn-outline-secondary">
              <i class="bi bi-arrow-left me-1"></i> Back to List
            </router-link>
            <button 
              @click="showRequestModal" 
              class="btn btn-primary"
              :disabled="!isAuthenticated"
            >
              <i class="bi bi-bag-plus me-1"></i> Request Food
            </button>
          </div>
          
          <!-- Request Food Modal -->
          <RequestFoodModal 
            v-if="food"
            ref="requestModal"
            :food-id="food.id"
            :max-servings="parseInt(food.quantity)"
            :pickup-address="food.pickup_address"
            :initial-location="userLocation"
            @request-submitted="onRequestSubmitted"
          />
        </div>
      </div>
    </div>
    <div v-else class="alert alert-danger text-center">Food not found.</div>
  </div>
</template>
<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useStore } from 'vuex';
import api from '../api';
import GoogleMapSingleMarker from '../components/GoogleMapSingleMarker.vue';
import RequestFoodModal from '../components/RequestFoodModal.vue';

const route = useRoute();
const router = useRouter();
const store = useStore();
const food = ref(null);
const loading = ref(true);
const requestModal = ref(null);
const userLocation = ref({ lat: null, lng: null, address: '' });

const isAuthenticated = computed(() => store.getters.isAuthenticated);

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  });
};

const formatDateTime = (dateStr) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleString(undefined, { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  });
};

// Get user's current location if available
const getCurrentLocation = () => {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        userLocation.value.lat = position.coords.latitude;
        userLocation.value.lng = position.coords.longitude;
        // Try to get the address using reverse geocoding
        if (window.google?.maps) {
          const geocoder = new window.google.maps.Geocoder();
          geocoder.geocode(
            { 
              location: { 
                lat: userLocation.value.lat, 
                lng: userLocation.value.lng 
              } 
            },
            (results, status) => {
              if (status === 'OK' && results[0]) {
                userLocation.value.address = results[0].formatted_address;
              }
            }
          );
        }
      },
      (error) => {
        console.error('Error getting location:', error);
      }
    );
  }
};

// Show the request modal
const showRequestModal = () => {
  if (!isAuthenticated.value) {
    router.push('/login?redirect=' + encodeURIComponent(route.fullPath));
    return;
  }
  
  if (requestModal.value) {
    requestModal.value.show();
  }
};

// Handle successful request submission
const onRequestSubmitted = () => {
  console.log('Request submitted successfully');
};

onMounted(async () => {
  loading.value = true;
  try {
    const res = await api.get(`/food/${route.params.id}`);
    food.value = res.data;
    
    // Get user's current location
    getCurrentLocation();
    
    // If there's a stored location from the request view, use that
    const storedLocation = localStorage.getItem('lastSearchedLocation');
    if (storedLocation) {
      try {
        const location = JSON.parse(storedLocation);
        if (location.lat && location.lng) {
          userLocation.value = { ...location };
        }
      } catch (e) {
        console.error('Error parsing stored location:', e);
      }
    }
  } catch (e) {
    console.error('Error fetching food details:', e);
    food.value = null;
  } finally {
    loading.value = false;
  }
});
</script>
<style scoped>
.card { border-radius: 14px; }
</style>
