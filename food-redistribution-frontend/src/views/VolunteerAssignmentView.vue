<template>
  <div class="assignment-view-container container-fluid py-4 px-lg-5">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-3">Loading assignment details...</p>
    </div>
    <div v-else-if="error" class="alert alert-danger" role="alert">
      {{ error }}
    </div>
    <div v-else-if="assignment" class="animate__animated animate__fadeIn">
      <!-- Page Header -->
      <div class="page-header d-flex justify-content-between align-items-center mb-4">
        <div>
          <h1 class="fw-bold mb-1">Assignment Details</h1>
          <p class="text-muted mb-0">Manage your pickup and delivery.</p>
        </div>
        <button class="btn btn-outline-secondary" @click="goBack">
          <i class="fas fa-arrow-left me-2"></i>Back to List
        </button>
      </div>

      <!-- Main Assignment Card -->
      <div class="card main-assignment-card shadow-lg border-0 mb-4">
        <div class="card-body p-4">
          <div class="row align-items-center">
            <div class="col-lg-8">
              <h3 class="fw-bold mb-2">{{ assignment.food_name }}</h3>
              <p class="mb-3">
                <span class="me-4"><strong>Quantity:</strong> {{ assignment.quantity }}</span>
                <span><strong>Assigned:</strong> {{ formatDate(assignment.assigned_at) }}</span>
              </p>
              <p v-if="assignment.special_instructions" class="special-instructions p-3 rounded">
                <i class="fas fa-info-circle me-2"></i>
                <strong>Instructions:</strong> {{ assignment.special_instructions }}
              </p>
            </div>
            <div class="col-lg-4 text-lg-end mt-3 mt-lg-0">
              <div class="status-display">
                <p class="mb-1 text-muted">STATUS</p>
                <span :class="statusBadgeClass" class="badge fs-5 px-3 py-2 shadow-sm">{{ formattedStatus }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Bar -->
      <div class="card action-bar shadow-sm mb-4">
        <div class="card-body d-flex justify-content-center align-items-center p-3">
          <button v-if="assignment.status === 'assigned'" 
                  class="btn btn-primary btn-lg"
                  @click="initiatePickup"
                  :disabled="isSubmitting">
            <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            <i v-else class="fas fa-box-open me-2"></i>
            {{ isSubmitting ? 'Processing...' : 'Confirm Pickup' }}
          </button>
          <button v-if="assignment.status === 'in_transit'" 
                  class="btn btn-success btn-lg"
                  @click="initiateDelivery"
                  :disabled="isSubmitting">
            <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            <i v-else class="fas fa-flag-checkered me-2"></i>
            {{ isSubmitting ? 'Processing...' : 'Confirm Delivery' }}
          </button>
          <div v-if="['pickup_verification_pending', 'delivery_verification_pending'].includes(assignment.status)" class="text-center text-muted">
            <i class="fas fa-hourglass-half fa-spin me-2"></i>
            Awaiting confirmation from the other party...
          </div>
          <div v-if="assignment.status === 'completed'" class="text-center text-success">
            <i class="fas fa-check-circle fa-2x me-2"></i>
            <h5 class="d-inline-block mb-0">Assignment Completed!</h5>
          </div>
        </div>
      </div>

      <!-- Map and Details Row -->
      <div class="row g-4">
        <!-- Left Column: Map -->
        <div class="col-lg-7">
          <div class="card shadow-sm h-100">
            <div class="card-header">
              <h5 class="mb-0 fw-bold"><i class="fas fa-route me-2"></i>Delivery Route</h5>
            </div>
            <div class="card-body p-2">
              <div id="route-map" style="height: 500px; border-radius: 8px;" ref="routeMap"></div>
            </div>
          </div>
        </div>

        <!-- Right Column: Pickup & Delivery -->
        <div class="col-lg-5">
          <!-- Pickup Card -->
          <div class="card info-card shadow-sm mb-4">
            <div class="card-header bg-light">
              <h5 class="mb-0 fw-bold"><i class="fas fa-box me-2 text-primary"></i>Pickup Details</h5>
            </div>
            <div class="card-body">
              <p class="fs-5 fw-bold mb-1">{{ assignment.donor_name }}</p>
              <p class="mb-2"><i class="fas fa-map-marker-alt me-2 text-muted"></i>{{ assignment.pickup_address }}</p>
              <p class="mb-2"><i class="fas fa-phone me-2 text-muted"></i>{{ assignment.donor_mobile }}</p>
              <p class="mb-3"><i class="fas fa-envelope me-2 text-muted"></i>{{ assignment.donor_email }}</p>
              <a :href="'https://www.google.com/maps/dir/?api=1&destination=' + encodeURIComponent(assignment.pickup_address)" 
                 class="btn btn-outline-primary w-100" 
                 target="_blank">
                <i class="fas fa-directions me-2"></i>Get Directions
              </a>
            </div>
          </div>

          <!-- Delivery Card -->
          <div class="card info-card shadow-sm">
            <div class="card-header bg-light">
              <h5 class="mb-0 fw-bold"><i class="fas fa-home me-2 text-success"></i>Delivery Details</h5>
            </div>
            <div class="card-body">
              <p class="fs-5 fw-bold mb-1">{{ assignment.requester_name }}</p>
              <p class="mb-2"><i class="fas fa-map-marker-alt me-2 text-muted"></i>{{ assignment.delivery_address }}</p>
              <p class="mb-2"><i class="fas fa-phone me-2 text-muted"></i>{{ assignment.requester_mobile }}</p>
              <p class="mb-3"><i class="fas fa-envelope me-2 text-muted"></i>{{ assignment.requester_email }}</p>
              <a :href="'https://www.google.com/maps/dir/?api=1&destination=' + encodeURIComponent(assignment.delivery_address)" 
                 class="btn btn-outline-success w-100" 
                 target="_blank">
                <i class="fas fa-directions me-2"></i>Get Directions
              </a>
            </div>
          </div>
        </div>
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
    await api.post(`/assignments/initiate-pickup/${assignmentId}`);
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
    await api.post(`/assignments/initiate-delivery/${assignmentId}`);
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
@import url('https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css');

.assignment-view-container {
  background-color: #f8f9fa;
}

.main-assignment-card {
  background: white;
  border-radius: 16px;
}

.special-instructions {
  background-color: #e9ecef;
  font-style: italic;
  font-size: 0.95rem;
}

.status-display .badge {
  border-radius: 10px;
}

.action-bar {
  border-radius: 12px;
}

.info-card {
  border-radius: 12px;
}

.info-card .card-header {
  border-bottom: none;
  border-radius: 12px 12px 0 0;
}

#route-map {
  width: 100%;
  height: 100%;
  min-height: 500px;
}

.badge.bg-info {
  color: #000 !important;
}
.badge.bg-warning {
  color: #000 !important;
}
</style>
