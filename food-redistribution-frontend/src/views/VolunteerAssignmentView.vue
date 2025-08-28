<template>
  <div class="container py-4">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-3">Loading assignment details...</p>
    </div>
    
    <div v-else-if="error" class="alert alert-danger" role="alert">
      {{ error }}
    </div>
    
    <div v-else-if="assignment" class="assignment-details">
      <!-- Assignment Header -->
      <div class="card mb-4 shadow-sm">
        <div class="card-body p-4">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h2 class="mb-0">
              <i class="fas fa-truck-loading me-2"></i>
              Delivery Assignment
            </h2>
            <span :class="statusBadgeClass" class="badge fs-5">{{ formattedStatus }}</span>
          </div>
          
          <div class="row">
            <div class="col-md-8">
              <h4 class="mb-2">{{ assignment.food_name }}</h4>
              <div class="mb-1"><b>Quantity:</b> {{ assignment.quantity }} of {{ assignment.original_quantity }}</div>
              <div class="mb-1"><b>Assigned at:</b> {{ formatDate(assignment.assigned_at) }}</div>
              <div v-if="assignment.special_instructions" class="mb-3 p-2 bg-light rounded">
                <b>Special Instructions:</b> {{ assignment.special_instructions }}
              </div>
            </div>
            <div class="col-md-4 text-md-end mt-3 mt-md-0">
              <!-- Action Buttons based on status -->
              <button v-if="assignment.status === 'assigned'" 
                      class="btn btn-primary btn-lg"
                      @click="initiatePickup"
                      :disabled="isSubmitting">
                <span v-if="isSubmitting" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                <i v-else class="fas fa-box-open me-2"></i>
                Initiate Pickup
              </button>
              <button v-if="assignment.status === 'in_transit'" 
                      class="btn btn-success btn-lg"
                      @click="initiateDelivery"
                      :disabled="isSubmitting">
                <span v-if="isSubmitting" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                <i v-else class="fas fa-flag-checkered me-2"></i>
                Initiate Delivery
              </button>
              <div v-if="['pickup_pending_verification', 'delivery_pending_verification'].includes(assignment.status)" class="text-muted">
                <i class="fas fa-hourglass-half me-1"></i>
                Awaiting Confirmation...
              </div>
              <div v-if="assignment.status === 'completed'" class="text-success">
                <i class="fas fa-check-circle me-1"></i>
                Assignment Completed
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Delivery Route Map -->
      <div class="card mb-4 shadow-sm">
        <div class="card-body p-4">
          <h3 class="mb-3">Delivery Route</h3>
          <div id="route-map" style="height: 400px; border-radius: 12px;" ref="routeMap"></div>
        </div>
      </div>
      
      <!-- Pickup & Delivery Info -->
      <div class="row g-4 mb-4">
        <!-- Pickup Information -->
        <div class="col-md-6">
          <div class="card h-100 shadow-sm" style="border-left: 4px solid #0d6efd;">
            <div class="card-body p-4">
              <h3 class="mb-3"><i class="fas fa-box me-2"></i>Pickup Information</h3>
              
              <h5 class="mb-2">{{ assignment.donor_name }}</h5>
              <div class="mb-1">
                <i class="fas fa-map-marker-alt text-primary me-2"></i>
                {{ assignment.pickup_address }}
              </div>
              <div class="mb-1">
                <i class="fas fa-phone text-primary me-2"></i>
                {{ assignment.donor_mobile }}
              </div>
              <div class="mb-1">
                <i class="fas fa-envelope text-primary me-2"></i>
                {{ assignment.donor_email }}
              </div>
              
              <div class="mt-3">
                <a :href="'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(assignment.pickup_address)" 
                   class="btn btn-outline-primary" 
                   target="_blank">
                  <i class="fas fa-directions me-2"></i>
                  Get Directions
                </a>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Delivery Information -->
        <div class="col-md-6">
          <div class="card h-100 shadow-sm" style="border-left: 4px solid #28a745;">
            <div class="card-body p-4">
              <h3 class="mb-3"><i class="fas fa-home me-2"></i>Delivery Information</h3>
              
              <h5 class="mb-2">{{ assignment.requester_name }}</h5>
              <div class="mb-1">
                <i class="fas fa-map-marker-alt text-success me-2"></i>
                {{ assignment.delivery_address }}
              </div>
              <div class="mb-1">
                <i class="fas fa-phone text-success me-2"></i>
                {{ assignment.requester_mobile }}
              </div>
              <div class="mb-1">
                <i class="fas fa-envelope text-success me-2"></i>
                {{ assignment.requester_email }}
              </div>
              
              <div class="mt-3">
                <a :href="'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(assignment.delivery_address)" 
                   class="btn btn-outline-success" 
                   target="_blank">
                  <i class="fas fa-directions me-2"></i>
                  Get Directions
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Food Details -->
      <div class="card mb-4 shadow-sm">
        <div class="card-body p-4">
          <h3 class="mb-3">Food Details</h3>
          
          <div class="row align-items-center">
            <div class="col-md-6">
              <div class="mb-2"><b>Expiry Date:</b> {{ formatDate(assignment.expiry_date) }}</div>
              <div class="mb-2"><b>Original Quantity:</b> {{ assignment.original_quantity }}</div>
              <div class="mb-2"><b>Requested Quantity:</b> {{ assignment.quantity }}</div>
            </div>
            <div class="col-md-6 text-center">
              <div v-if="assignment.food_image_base64" class="food-image-container">
                <img :src="'data:image/jpeg;base64,' + assignment.food_image_base64" 
                     class="img-fluid rounded" 
                     alt="Food Image"
                     style="max-height: 200px;" />
              </div>
              <div v-else class="no-image">
                <i class="fas fa-image fa-3x text-muted mb-2"></i>
                <p class="text-muted">No image available</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Back Button -->
      <div class="text-center mb-4">
        <button class="btn btn-outline-secondary" @click="goBack">
          <i class="fas fa-arrow-left me-2"></i>
          Back to Volunteer Dashboard
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../api';

const route = useRoute();
const router = useRouter();
const assignment = ref(null);
const loading = ref(true);
const error = ref(null);
const isSubmitting = ref(false);
const routeMap = ref(null);
let map = null;
let directionsService = null;
let directionsRenderer = null;

const formattedStatus = computed(() => {
  if (!assignment.value) return '';
  return (assignment.value.status || '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
});

const statusBadgeClass = computed(() => {
  if (!assignment.value) return 'bg-secondary';
  const status = assignment.value.status;
  if (status === 'completed') return 'bg-success';
  if (status === 'assigned') return 'bg-primary';
  if (status === 'in_transit') return 'bg-info';
  if (status.includes('pending_verification')) return 'bg-warning text-dark';
  return 'bg-secondary';
});

const fetchAssignment = async () => {
  loading.value = true;
  error.value = null;
  
  try {
    const assignmentId = route.params.id;
    const response = await api.get(`/volunteer/assignment/${assignmentId}`);
    assignment.value = response.data.assignment;
    console.log('Fetched assignment details:', assignment.value);
    
    // Once we have the data, initialize the map
    setTimeout(() => {
      initMap();
    }, 500);
    
  } catch (err) {
    console.error('Error fetching assignment:', err);
    error.value = err.response?.data?.error || 'Failed to load assignment details';
  } finally {
    loading.value = false;
  }
};

const initiatePickup = async () => {
  if (!assignment.value || isSubmitting.value) return;
  isSubmitting.value = true;
  try {
    const assignmentId = assignment.value.id;
    await api.post(`/assignment/${assignmentId}/initiate-pickup`);
    alert('A verification email has been sent to the donor. Please wait for them to confirm the pickup.');
    await fetchAssignment(); // Refresh state
  } catch (err) {
    console.error('Error initiating pickup:', err);
    alert(err.response?.data?.error || 'Failed to initiate pickup.');
  } finally {
    isSubmitting.value = false;
  }
};

const initiateDelivery = async () => {
  if (!assignment.value || isSubmitting.value) return;
  isSubmitting.value = true;
  try {
    const assignmentId = assignment.value.id;
    await api.post(`/assignment/${assignmentId}/initiate-delivery`);
    alert('A verification email has been sent to the requester. Please wait for them to confirm the delivery.');
    await fetchAssignment(); // Refresh state
  } catch (err) {
    console.error('Error initiating delivery:', err);
    alert(err.response?.data?.error || 'Failed to initiate delivery.');
  } finally {
    isSubmitting.value = false;
  }
};

const initMap = () => {
  if (!assignment.value || !window.google || !routeMap.value) return;
  
  const donorLatLng = {
    lat: parseFloat(assignment.value.donor_lat),
    lng: parseFloat(assignment.value.donor_lng)
  };
  
  // Create the map centered on donor location
  map = new window.google.maps.Map(routeMap.value, {
    zoom: 12,
    center: donorLatLng,
  });
  
  // Initialize the directions service and renderer
  directionsService = new window.google.maps.DirectionsService();
  directionsRenderer = new window.google.maps.DirectionsRenderer({
    map: map,
    suppressMarkers: false
  });
  
  // Get directions from donor to requester
  calculateAndDisplayRoute();
};

const calculateAndDisplayRoute = () => {
  const donorAddress = assignment.value.pickup_address;
  const requesterAddress = assignment.value.delivery_address;
  
  directionsService.route({
    origin: donorAddress,
    destination: requesterAddress,
    travelMode: window.google.maps.TravelMode.DRIVING
  }, (response, status) => {
    if (status === 'OK') {
      directionsRenderer.setDirections(response);
    } else {
      console.error('Directions request failed due to ' + status);
      
      // If directions fail, fallback to simple markers
      addMarker(
        assignment.value.donor_lat,
        assignment.value.donor_lng,
        'Pickup: ' + assignment.value.pickup_address,
        'pickup'
      );
      
      // For delivery, we'll geocode the address since we might not have coords
      const geocoder = new window.google.maps.Geocoder();
      geocoder.geocode({ 'address': requesterAddress }, (results, status) => {
        if (status === 'OK') {
          addMarker(
            results[0].geometry.location.lat(),
            results[0].geometry.location.lng(),
            'Deliver to: ' + requesterAddress,
            'delivery'
          );
          
          // Adjust map to show both markers
          const bounds = new window.google.maps.LatLngBounds();
          bounds.extend(new window.google.maps.LatLng(
            parseFloat(assignment.value.donor_lat),
            parseFloat(assignment.value.donor_lng)
          ));
          bounds.extend(results[0].geometry.location);
          map.fitBounds(bounds);
        }
      });
    }
  });
};

const addMarker = (lat, lng, title, type) => {
  const iconUrl = type === 'pickup' 
    ? 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png' 
    : 'http://maps.google.com/mapfiles/ms/icons/green-dot.png';
    
  new window.google.maps.Marker({
    position: { lat: parseFloat(lat), lng: parseFloat(lng) },
    map: map,
    title: title,
    icon: iconUrl
  });
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const goBack = () => {
  router.push('/volunteer');
};

onMounted(() => {
  fetchAssignment();
});
</script>

<style scoped>
.assignment-details {
  max-width: 1200px;
  margin: 0 auto;
}

.card {
  border: none;
  border-radius: 12px;
  overflow: hidden;
}

.badge {
  padding: 0.6em 1em;
  border-radius: 8px;
}

.food-image-container {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.no-image {
  padding: 2rem;
  background-color: #f8f9fa;
  border-radius: 12px;
}

.btn {
  border-radius: 8px;
  padding: 0.5rem 1.25rem;
  font-weight: 500;
}

.btn-lg {
  padding: 0.75rem 1.5rem;
  font-weight: 600;
}

.badge.bg-warning {
  color: #000 !important;
}
</style>
