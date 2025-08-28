<template>
  <div class="container py-3">
    <!-- Current Assignment Section -->
    <div v-if="myAssignments.length > 0" class="row mb-4">
      <div class="col-12">
        <h3 class="mb-3"><i class="fas fa-clipboard-check me-2"></i>Current Assignment</h3>
        <div v-for="assignment in myAssignments" :key="assignment.id" class="card p-3 mb-3 shadow-sm assignment-card">
          <div class="d-flex flex-column flex-md-row align-items-md-center justify-content-between">
            <div class="flex-grow-1">
              <h5 class="mb-2">{{ assignment.food_name }}</h5>
              <div class="mb-1"><b>Quantity:</b> {{ assignment.quantity }}</div>
              <div class="mb-1"><b>Donor:</b> {{ assignment.donor_name }}</div>
              <div class="mb-1"><b>Pickup:</b> {{ assignment.pickup_address }}</div>
              <div class="mb-1"><b>Requester:</b> {{ assignment.requester_name }}</div>
              <div class="mb-1"><b>Delivery:</b> {{ assignment.delivery_address || 'Address pending' }}</div>
              <div class="mb-1"><b>Status:</b> <span class="badge bg-primary">{{ assignment.status }}</span></div>
            </div>
            <div class="ms-md-4 mt-2 mt-md-0">
              <button class="btn btn-success btn-lg" @click="goToAssignmentDetails(assignment.id)">
                <i class="fas fa-map-marked-alt me-2"></i>Start Delivery
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Filters and Sort -->
    <div class="row mb-3">
      <div class="col-12 d-flex flex-wrap align-items-center gap-2">
        <input v-model="filterFood" @input="applyFilters" class="form-control w-auto" placeholder="Search food name..." />
        <select v-model="filterQuantity" @change="applyFilters" class="form-select w-auto">
          <option value="">All Quantities</option>
          <option value="small">Small (1-5)</option>
          <option value="medium">Medium (6-15)</option>
          <option value="large">Large (16+)</option>
        </select>
        <select v-model="sortBy" @change="applyFilters" class="form-select w-auto">
          <option value="">Sort by...</option>
          <option value="nearest_donor">Nearest Donor</option>
          <option value="nearest_requester">Nearest Requester</option>
          <option value="shortest_total">Shortest Total Distance</option>
          <option value="quantity_asc">Quantity (Low to High)</option>
          <option value="quantity_desc">Quantity (High to Low)</option>
        </select>
        <input ref="addressInput" class="form-control w-auto" placeholder="Your location..." style="min-width:220px;" />
        <button class="btn btn-outline-secondary" @click="fetchData">Refresh</button>
      </div>
    </div>

    <!-- Pending Requests Section -->
    <div class="row mb-3">
      <div class="col-12">
        <h3 class="mb-3">
          <i class="fas fa-hand-paper me-2"></i>Pending Requests
          <span v-if="myAssignments.length > 0" class="badge bg-warning ms-2">Complete current assignment first</span>
        </h3>
      </div>
    </div>

    <div class="row g-2">
      <div class="col-12">
        <div v-if="filteredRequests.length === 0" class="text-center py-5">
          <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
          <p class="text-muted">No pending requests available</p>
        </div>
        <div v-for="request in filteredRequests" :key="request.id" 
             :class="['request-card', { 'disabled': hasActiveAssignment }]">
          <div class="card p-3 mb-2 shadow-sm w-100">
            <div class="d-flex flex-column flex-md-row align-items-md-center justify-content-between">
              <div class="flex-grow-1">
                <h5 class="mb-2">{{ request.food_name }}</h5>
                <div class="mb-1"><b>Quantity:</b> {{ request.quantity }}</div>
                <div class="mb-1"><b>Requester:</b> {{ request.requester_name }}</div>
                <div class="mb-1"><b>Pickup from:</b> {{ request.pickup_address }}</div>
                <div class="mb-1"><b>Deliver to:</b> {{ request.delivery_address || 'Address pending' }}</div>
                <div v-if="request.donor_distance" class="mb-1"><b>Distance to Donor:</b> {{ request.donor_distance.toFixed(2) }} km</div>
                <div v-if="request.requester_distance" class="mb-1"><b>Distance to Requester:</b> {{ request.requester_distance.toFixed(2) }} km</div>
                <div v-if="request.total_distance" class="mb-1"><b>Total Distance:</b> {{ request.total_distance.toFixed(2) }} km</div>
                <div v-if="request.special_instructions" class="small text-muted mt-2">{{ request.special_instructions }}</div>
              </div>
              <div class="ms-md-4 mt-2 mt-md-0">
                <button 
                  class="btn btn-primary btn-lg"
                  :disabled="hasActiveAssignment || acceptingRequest === request.id"
                  @click="acceptRequest(request.id)"
                >
                  <i v-if="acceptingRequest === request.id" class="fas fa-spinner fa-spin me-2"></i>
                  <i v-else class="fas fa-check me-2"></i>
                  {{ acceptingRequest === request.id ? 'Accepting...' : 'Accept' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api';

const router = useRouter();
const pendingRequests = ref([]);
const myAssignments = ref([]);
const userLocation = ref({ lat: null, lng: null });
const acceptingRequest = ref(null);

// Filter and sort states
const filterFood = ref('');
const filterQuantity = ref('');
const sortBy = ref('');
const addressInput = ref();

const hasActiveAssignment = computed(() => myAssignments.value.length > 0);

const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371; // Earth's radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
};

const processRequestsWithDistances = (requests) => {
  if (!userLocation.value.lat || !userLocation.value.lng) return requests;
  
  return requests.map(request => {
    const processed = { ...request };
    
    // Calculate distance to donor
    if (request.donor_lat && request.donor_lng) {
      processed.donor_distance = calculateDistance(
        userLocation.value.lat, userLocation.value.lng,
        request.donor_lat, request.donor_lng
      );
    }
    
    // Calculate distance to requester
    if (request.delivery_latitude && request.delivery_longitude) {
      processed.requester_distance = calculateDistance(
        userLocation.value.lat, userLocation.value.lng,
        request.delivery_latitude, request.delivery_longitude
      );
    }
    
    // Calculate total distance (volunteer -> donor -> requester)
    if (processed.donor_distance && processed.requester_distance && 
        request.donor_lat && request.donor_lng && 
        request.delivery_latitude && request.delivery_longitude) {
      const donorToRequester = calculateDistance(
        request.donor_lat, request.donor_lng,
        request.delivery_latitude, request.delivery_longitude
      );
      processed.total_distance = processed.donor_distance + donorToRequester;
    }
    
    return processed;
  });
};

const filteredRequests = computed(() => {
  let filtered = processRequestsWithDistances(pendingRequests.value);
  
  // Apply filters
  if (filterFood.value) {
    filtered = filtered.filter(req => 
      req.food_name.toLowerCase().includes(filterFood.value.toLowerCase())
    );
  }
  
  if (filterQuantity.value) {
    filtered = filtered.filter(req => {
      const qty = parseInt(req.quantity);
      switch (filterQuantity.value) {
        case 'small': return qty >= 1 && qty <= 5;
        case 'medium': return qty >= 6 && qty <= 15;
        case 'large': return qty >= 16;
        default: return true;
      }
    });
  }
  
  // Apply sorting
  if (sortBy.value) {
    filtered.sort((a, b) => {
      switch (sortBy.value) {
        case 'nearest_donor':
          return (a.donor_distance || Infinity) - (b.donor_distance || Infinity);
        case 'nearest_requester':
          return (a.requester_distance || Infinity) - (b.requester_distance || Infinity);
        case 'shortest_total':
          return (a.total_distance || Infinity) - (b.total_distance || Infinity);
        case 'quantity_asc':
          return parseInt(a.quantity) - parseInt(b.quantity);
        case 'quantity_desc':
          return parseInt(b.quantity) - parseInt(a.quantity);
        default:
          return 0;
      }
    });
  }
  
  return filtered;
});

const fetchData = async () => {
  try {
    const pending = await api.get('/volunteer/pending');
    const assigned = await api.get('/volunteer/assignments');
    pendingRequests.value = pending.data.pending_requests || [];
    myAssignments.value = assigned.data.assignments || [];
    console.log('Fetched pending requests:', pendingRequests.value.length);
    console.log('Fetched assignments:', myAssignments.value.length);
  } catch (error) {
    console.error('Error fetching volunteer data:', error);
  }
};

const acceptRequest = async (requestId) => {
  if (hasActiveAssignment.value) return;
  
  acceptingRequest.value = requestId;
  try {
    await api.post('/volunteer/accept', { request_id: requestId });
    await fetchData(); // Refresh data
  } catch (error) {
    console.error('Error accepting request:', error);
    alert(error.response?.data?.error || 'Failed to accept request');
  } finally {
    acceptingRequest.value = null;
  }
};

const goToAssignmentDetails = (assignmentId) => {
  router.push(`/volunteer/assignment/${assignmentId}`);
};

const applyFilters = () => {
  // Filters are applied automatically via computed property
};

onMounted(() => {
  fetchData();
  
  // Get user's current location
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(pos => {
      userLocation.value.lat = pos.coords.latitude;
      userLocation.value.lng = pos.coords.longitude;
    });
  }
  
  // Setup Google Places Autocomplete
  const waitForGoogle = setInterval(() => {
    if (window.google?.maps?.places) {
      clearInterval(waitForGoogle);
      const autocomplete = new window.google.maps.places.Autocomplete(addressInput.value, {
        fields: ['formatted_address', 'geometry']
      });
      
      autocomplete.addListener('place_changed', () => {
        const place = autocomplete.getPlace();
        if (place.geometry) {
          userLocation.value.lat = place.geometry.location.lat();
          userLocation.value.lng = place.geometry.location.lng();
        }
      });
    }
  }, 200);
});
</script>

<style scoped>
.assignment-card {
  border-left: 4px solid #28a745;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.request-card {
  transition: all 0.2s ease;
}

.request-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

.request-card.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.request-card.disabled .card {
  background-color: #f8f9fa;
}

.card {
  border: none;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.btn-lg {
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  border-radius: 8px;
}

.form-control, .form-select {
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.form-control:focus, .form-select:focus {
  border-color: #4f46e5;
  box-shadow: 0 0 0 0.2rem rgba(79, 70, 229, 0.25);
}

.badge {
  font-size: 0.75rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
}
</style>
