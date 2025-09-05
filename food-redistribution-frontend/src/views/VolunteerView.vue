<template>
  <div class="volunteer-view-container container-fluid py-4 px-lg-5">
    <!-- Current Assignment Section -->
    <div v-if="myAssignments.length > 0" class="mb-5 animate__animated animate__fadeIn">
      <h2 class="mb-3 fw-bold">
        <i class="fas fa-clipboard-check me-2 text-primary"></i>Your Current Assignment
      </h2>
      <div v-for="assignment in myAssignments" :key="assignment.id" class="card assignment-card-new shadow-lg border-0">
        <div class="card-body p-4">
          <div class="row align-items-center">
            <div class="col-md-8">
              <h4 class="card-title fw-bold mb-3">{{ assignment.food_name }}</h4>
              <div class="row">
                <div class="col-lg-6">
                  <p class="mb-2"><strong><i class="fas fa-user-tag me-2 text-muted"></i>Donor:</strong> {{ assignment.donor_name }}</p>
                  <p class="mb-2"><strong><i class="fas fa-map-marker-alt me-2 text-muted"></i>Pickup:</strong> {{ assignment.pickup_address }}</p>
                </div>
                <div class="col-lg-6">
                  <p class="mb-2"><strong><i class="fas fa-user-check me-2 text-muted"></i>Requester:</strong> {{ assignment.requester_name }}</p>
                  <p class="mb-2"><strong><i class="fas fa-location-arrow me-2 text-muted"></i>Delivery:</strong> {{ assignment.delivery_address || 'Address pending' }}</p>
                </div>
              </div>
              <div class="mt-3">
                <span class="badge rounded-pill fs-6" :class="statusBadgeClass(assignment.status)">{{ formatStatus(assignment.status) }}</span>
                <span class="ms-3"><strong>Quantity:</strong> {{ assignment.quantity }}</span>
              </div>
            </div>
            <div class="col-md-4 text-md-end mt-4 mt-md-0">
              <button class="btn btn-primary btn-lg w-100" @click="goToAssignmentDetails(assignment.id)">
                <i class="fas fa-route me-2"></i>View Assignment
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Pending Requests Section -->
    <div class="pending-requests-section">
      <h2 class="mb-4 fw-bold"><i class="fas fa-tasks me-2 text-secondary"></i>Pending Requests</h2>

      <!-- Filters -->
      <div class="card shadow-sm mb-4 filter-card">
        <div class="card-body d-flex flex-wrap align-items-center gap-3">
          <div class="flex-grow-1">
            <input ref="addressInput" class="form-control" placeholder="Enter your location for distance calculation..." />
          </div>
          <div class="filter-group d-flex gap-3">
            <input v-model="filterFood" @input="applyFilters" class="form-control" placeholder="Filter by food..." />
            <select v-model="sortBy" @change="applyFilters" class="form-select">
              <option value="">Sort by...</option>
              <option value="shortest_total">Shortest Route</option>
              <option value="nearest_donor">Nearest Pickup</option>
              <option value="quantity_asc">Quantity (Low-High)</option>
              <option value="quantity_desc">Quantity (High-Low)</option>
            </select>
          </div>
          <button class="btn btn-outline-secondary" @click="fetchData" title="Refresh Data">
            <i class="fas fa-sync-alt me-2"></i>Refresh
          </button>
        </div>
      </div>
      
      <div v-if="hasActiveAssignment" class="alert alert-warning text-center">
        <i class="fas fa-info-circle me-2"></i>
        You must complete your current assignment before accepting a new one.
      </div>

      <!-- Requests List -->
      <div v-if="filteredRequests.length === 0 && !loading" class="text-center py-5 my-5 card bg-light">
        <i class="fas fa-inbox fa-4x text-muted mb-3"></i>
        <h4 class="text-muted">No pending requests right now.</h4>
        <p>Check back later for new opportunities!</p>
      </div>
      
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-2">Loading requests...</p>
      </div>

      <div class="row g-4">
        <div v-for="request in filteredRequests" :key="request.id" class="col-lg-6 col-xl-4 animate__animated animate__fadeInUp">
          <div class="card h-100 request-card-new" :class="{ 'disabled': hasActiveAssignment }">
            <div class="card-body d-flex flex-column">
              <h5 class="card-title fw-bold">{{ request.food_name }}</h5>
              <p class="card-subtitle mb-2 text-muted">Quantity: {{ request.quantity }}</p>
              <hr>
              <div class="flex-grow-1">
                <p class="mb-2"><i class="fas fa-map-pin me-2 text-danger"></i><strong>Pickup:</strong> {{ request.pickup_address }}</p>
                <p class="mb-3"><i class="fas fa-flag-checkered me-2 text-success"></i><strong>Dropoff:</strong> {{ request.delivery_address || 'Address pending' }}</p>
                
                <div v-if="request.total_distance" class="distance-info alert alert-light p-2 text-center">
                  <i class="fas fa-road me-2"></i>
                  Approx. <strong>{{ request.total_distance.toFixed(1) }} km</strong> total
                  <span class="d-block text-muted small">({{ request.donor_distance.toFixed(1) }}km to pickup, {{ request.requester_distance.toFixed(1) }}km to dropoff)</span>
                </div>
                
                <p v-if="request.special_instructions" class="small text-muted mt-3 fst-italic">
                  <i class="fas fa-info-circle me-1"></i> {{ request.special_instructions }}
                </p>
              </div>
              <div class="mt-4">
                <button 
                  class="btn btn-primary w-100"
                  :disabled="hasActiveAssignment || acceptingRequest === request.id"
                  @click="acceptRequest(request.id)"
                >
                  <span v-if="acceptingRequest === request.id">
                    <i class="fas fa-spinner fa-spin me-2"></i>Accepting...
                  </span>
                  <span v-else>
                    <i class="fas fa-check-circle me-2"></i>Accept Request
                  </span>
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
const loading = ref(true);

// Filter and sort states
const filterFood = ref('');
const filterQuantity = ref('');
const sortBy = ref('');
const addressInput = ref();

const hasActiveAssignment = computed(() => myAssignments.value.length > 0);

const formatStatus = (status) => {
  return (status || '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

const statusBadgeClass = (status) => {
  if (status === 'completed') return 'bg-success';
  if (status === 'assigned') return 'bg-primary';
  if (status === 'in_transit') return 'bg-info text-dark';
  if (status === 'pickup_verification_pending') return 'bg-warning text-dark';
  if (status === 'delivery_verification_pending') return 'bg-warning text-dark';
  return 'bg-secondary';
};

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

    // Calculate total distance if both are available
    if (processed.donor_distance && processed.requester_distance) {
      // This is a simple sum, not a route calculation. For a real app, use Directions API.
      processed.total_distance = processed.donor_distance + processed.requester_distance;
    }
    
    return processed;
  });
};

const filteredRequests = computed(() => {
  let filtered = processRequestsWithDistances(pendingRequests.value);

  // Filter by food name
  if (filterFood.value) {
    filtered = filtered.filter(req =>
      req.food_name.toLowerCase().includes(filterFood.value.toLowerCase())
    );
  }

  // Sort
  if (sortBy.value) {
    switch (sortBy.value) {
      case 'shortest_total':
        filtered.sort((a, b) => (a.total_distance || Infinity) - (b.total_distance || Infinity));
        break;
      case 'nearest_donor':
        filtered.sort((a, b) => (a.donor_distance || Infinity) - (b.donor_distance || Infinity));
        break;
      case 'quantity_asc':
        filtered.sort((a, b) => a.quantity - b.quantity);
        break;
      case 'quantity_desc':
        filtered.sort((a, b) => b.quantity - a.quantity);
        break;
    }
  }

  return filtered;
});

const fetchData = async () => {
  loading.value = true;
  try {
    const [pendingRes, assignmentsRes] = await Promise.allSettled([
      api.get('/volunteer/pending'),
      api.get('/volunteer/assignments')
    ]);

    if (pendingRes.status === 'fulfilled') {
      pendingRequests.value = pendingRes.value.data.pending_requests || [];
    } else {
      console.error("Error fetching pending requests:", pendingRes.reason);
      pendingRequests.value = [];
    }

    if (assignmentsRes.status === 'fulfilled') {
      myAssignments.value = assignmentsRes.value.data.assignments || [];
    } else {
      console.error("Error fetching assignments:", assignmentsRes.reason);
      myAssignments.value = [];
    }
  } catch (error) {
      console.error("Unexpected error in fetchData:", error);
  } finally {
    loading.value = false;
  }
};

const acceptRequest = async (requestId) => {
  acceptingRequest.value = requestId;
  try {
    await api.post(`/volunteer/accept/${requestId}`);
    await fetchData(); // Refresh data
  } catch (error) {
    console.error("Error accepting request:", error);
  } finally {
    acceptingRequest.value = null;
  }
};

const getUserLocation = () => {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      pos => {
        userLocation.value = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        };
      },
      err => {
        console.warn(`Geolocation error: ${err.message}`);
      }
    );
  }
};

const goToAssignmentDetails = (assignmentId) => {
  router.push(`/volunteer/assignment/${assignmentId}`);
};

const applyFilters = () => {
  // The computed property handles filtering automatically.
};

onMounted(() => {
  fetchData();
  getUserLocation();

  const waitForGoogle = setInterval(() => {
    if (window.google && window.google.maps && window.google.maps.places) {
      clearInterval(waitForGoogle);
      const autocomplete = new google.maps.places.Autocomplete(addressInput.value, {
        fields: ["geometry"],
      });
      autocomplete.addListener('place_changed', () => {
        const place = autocomplete.getPlace();
        if (place.geometry) {
          userLocation.value = {
            lat: place.geometry.location.lat(),
            lng: place.geometry.location.lng(),
          };
        }
      });
    }
  }, 200);
  setTimeout(() => clearInterval(waitForGoogle), 10000);
});
</script>

<style scoped>
@import url('https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css');

.volunteer-view-container {
  background-color: #f8f9fa;
}

.assignment-card-new {
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
  color: white;
  border-radius: 16px;
}

.assignment-card-new .btn-primary {
  background-color: #fff;
  color: var(--primary-color);
  border: none;
  font-weight: bold;
}

.filter-card {
  border-radius: 12px;
  background-color: var(--card-background);
}

.request-card-new {
  border-radius: 12px;
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
  border: 1px solid var(--border-color);
}

.request-card-new:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px var(--shadow-color);
}

.request-card-new.disabled {
  opacity: 0.6;
  pointer-events: none;
  background-color: #e9ecef;
}

.distance-info {
  border-radius: 8px;
  font-size: 0.9rem;
}

.badge.rounded-pill {
  padding: 0.5em 1em;
}
</style>
