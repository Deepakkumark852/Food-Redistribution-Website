<template>
  <div class="container-fluid h-100">
    <div class="row h-100">
      <!-- Map Section -->
      <div class="col-md-8 p-0">
        <div id="map" class="h-100"></div>
      </div>
      
      <!-- Sidebar -->
      <div class="col-md-4 bg-white shadow-lg">
        <div class="p-4 h-100 d-flex flex-column">
          <div class="mb-4">
            <h4 class="mb-3">
              <i class="fas fa-route me-2"></i>Assignment Details
            </h4>
            <div v-if="assignment" class="assignment-info">
              <h5 class="mb-2">{{ assignment.food_name }}</h5>
              <div class="mb-2"><b>Quantity:</b> {{ assignment.quantity }}</div>
              <div class="mb-2"><b>Status:</b> 
                <span :class="getStatusBadgeClass(assignment.status)">{{ assignment.status }}</span>
              </div>
            </div>
          </div>

          <!-- Step 1: Go to Donor -->
          <div v-if="currentStep === 'pickup'" class="step-section flex-grow-1">
            <div class="step-header mb-3">
              <h5><i class="fas fa-user-friends me-2 text-primary"></i>Step 1: Pickup from Donor</h5>
            </div>
            <div class="donor-info mb-3">
              <div class="mb-2"><b>Donor:</b> {{ assignment?.donor_name }}</div>
              <div class="mb-2"><b>Address:</b> {{ assignment?.pickup_address }}</div>
              <div v-if="distanceToDonor" class="mb-2"><b>Distance:</b> {{ distanceToDonor.toFixed(2) }} km</div>
              <div v-if="estimatedTime" class="mb-2"><b>Est. Time:</b> {{ estimatedTime }} mins</div>
            </div>
            <div class="d-grid">
              <button class="btn btn-success btn-lg mb-2" @click="confirmPickup" :disabled="confirmingPickup">
                <i v-if="confirmingPickup" class="fas fa-spinner fa-spin me-2"></i>
                <i v-else class="fas fa-check me-2"></i>
                {{ confirmingPickup ? 'Confirming...' : 'Received from Donor' }}
              </button>
              <button class="btn btn-outline-secondary" @click="goBack">
                <i class="fas fa-arrow-left me-2"></i>Back to Dashboard
              </button>
            </div>
          </div>

          <!-- Step 2: Go to Requester -->
          <div v-if="currentStep === 'delivery'" class="step-section flex-grow-1">
            <div class="step-header mb-3">
              <h5><i class="fas fa-home me-2 text-success"></i>Step 2: Deliver to Requester</h5>
            </div>
            <div class="requester-info mb-3">
              <div class="mb-2"><b>Requester:</b> {{ assignment?.requester_name }}</div>
              <div class="mb-2"><b>Address:</b> {{ assignment?.delivery_address }}</div>
              <div v-if="distanceToRequester" class="mb-2"><b>Distance:</b> {{ distanceToRequester.toFixed(2) }} km</div>
              <div v-if="deliveryTime" class="mb-2"><b>Est. Time:</b> {{ deliveryTime }} mins</div>
            </div>
            <div class="d-grid">
              <button class="btn btn-success btn-lg mb-2" @click="completeAssignment" :disabled="completingAssignment">
                <i v-if="completingAssignment" class="fas fa-spinner fa-spin me-2"></i>
                <i v-else class="fas fa-flag-checkered me-2"></i>
                {{ completingAssignment ? 'Completing...' : 'Assignment Complete' }}
              </button>
              <button class="btn btn-outline-secondary" @click="goBack">
                <i class="fas fa-arrow-left me-2"></i>Back to Dashboard
              </button>
            </div>
          </div>

          <!-- Progress Indicator -->
          <div class="progress-section mt-4">
            <div class="progress mb-2" style="height: 8px;">
              <div class="progress-bar" :style="{ width: progressPercentage + '%' }"></div>
            </div>
            <small class="text-muted">{{ progressText }}</small>
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
const currentStep = ref('pickup'); // 'pickup' or 'delivery'
const map = ref(null);
const directionsService = ref(null);
const directionsRenderer = ref(null);
const userLocation = ref(null);
const confirmingPickup = ref(false);
const completingAssignment = ref(false);

const distanceToDonor = ref(null);
const distanceToRequester = ref(null);
const estimatedTime = ref(null);
const deliveryTime = ref(null);

const progressPercentage = computed(() => {
  return currentStep.value === 'pickup' ? 25 : 75;
});

const progressText = computed(() => {
  return currentStep.value === 'pickup' ? 'Going to pickup location' : 'Delivering to requester';
});

const getStatusBadgeClass = (status) => {
  const classes = {
    'assigned': 'badge bg-primary',
    'in_progress': 'badge bg-warning',
    'completed': 'badge bg-success'
  };
  return classes[status] || 'badge bg-secondary';
};

const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
};

const initMap = () => {
  if (!window.google || !assignment.value) {
    console.log('Google Maps not loaded or assignment not available');
    return;
  }

  console.log('Initializing map with assignment:', assignment.value);

  map.value = new window.google.maps.Map(document.getElementById('map'), {
    zoom: 13,
    center: { lat: 13.0827, lng: 80.2707 } // Default to Chennai
  });

  directionsService.value = new window.google.maps.DirectionsService();
  directionsRenderer.value = new window.google.maps.DirectionsRenderer({
    draggable: false,
    panel: null,
    suppressMarkers: false
  });
  directionsRenderer.value.setMap(map.value);

  // Get user's current location and show directions
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      position => {
        userLocation.value = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        console.log('User location obtained:', userLocation.value);
        updateDirections();
      },
      error => {
        console.error('Geolocation error:', error);
        // Use default location if geolocation fails
        userLocation.value = { lat: 13.0827, lng: 80.2707 };
        updateDirections();
      }
    );
  } else {
    // Use default location if geolocation not supported
    userLocation.value = { lat: 13.0827, lng: 80.2707 };
    updateDirections();
  }
};

const updateDirections = () => {
  if (!directionsService.value || !userLocation.value || !assignment.value) {
    console.log('Missing required data for directions:', {
      directionsService: !!directionsService.value,
      userLocation: !!userLocation.value,
      assignment: !!assignment.value
    });
    return;
  }

  let destination;
  let destinationAddress;
  
  if (currentStep.value === 'pickup') {
    // For pickup step, go to donor location
    if (assignment.value.donor_lat && assignment.value.donor_lng) {
      destination = {
        lat: parseFloat(assignment.value.donor_lat),
        lng: parseFloat(assignment.value.donor_lng)
      };
    } else {
      // Fallback to geocoding the pickup address
      destinationAddress = assignment.value.pickup_address;
    }
    
    if (destination && userLocation.value) {
      distanceToDonor.value = calculateDistance(
        userLocation.value.lat, userLocation.value.lng,
        destination.lat, destination.lng
      );
      estimatedTime.value = Math.round(distanceToDonor.value * 3); // Rough estimate: 3 min per km
    }
  } else {
    // For delivery step, go to requester location
    if (assignment.value.delivery_latitude && assignment.value.delivery_longitude) {
      destination = {
        lat: parseFloat(assignment.value.delivery_latitude),
        lng: parseFloat(assignment.value.delivery_longitude)
      };
    } else {
      // Fallback to geocoding the delivery address
      destinationAddress = assignment.value.delivery_address;
    }
    
    // Calculate distance from current location (or donor location) to requester
    if (destination && userLocation.value) {
      distanceToRequester.value = calculateDistance(
        userLocation.value.lat, userLocation.value.lng,
        destination.lat, destination.lng
      );
      deliveryTime.value = Math.round(distanceToRequester.value * 3);
    }
  }

  const request = {
    origin: userLocation.value,
    destination: destination || destinationAddress,
    travelMode: window.google.maps.TravelMode.DRIVING,
  };

  console.log('Requesting directions:', request);

  directionsService.value.route(request, (result, status) => {
    console.log('Directions result:', status, result);
    if (status === 'OK') {
      directionsRenderer.value.setDirections(result);
      
      // Update distance and time from actual route
      const route = result.routes[0];
      if (route && route.legs[0]) {
        const leg = route.legs[0];
        if (currentStep.value === 'pickup') {
          distanceToDonor.value = leg.distance.value / 1000; // Convert to km
          estimatedTime.value = Math.round(leg.duration.value / 60); // Convert to minutes
        } else {
          distanceToRequester.value = leg.distance.value / 1000;
          deliveryTime.value = Math.round(leg.duration.value / 60);
        }
      }
    } else {
      console.error('Directions request failed:', status);
      // Fallback to showing static markers
      showStaticMarkers();
    }
  });
};

const showStaticMarkers = () => {
  if (!map.value || !assignment.value) return;
  
  // Clear existing markers
  if (directionsRenderer.value) {
    directionsRenderer.value.setDirections({routes: []});
  }
  
  let targetLocation;
  if (currentStep.value === 'pickup' && assignment.value.donor_lat && assignment.value.donor_lng) {
    targetLocation = {
      lat: parseFloat(assignment.value.donor_lat),
      lng: parseFloat(assignment.value.donor_lng)
    };
  } else if (currentStep.value === 'delivery' && assignment.value.delivery_latitude && assignment.value.delivery_longitude) {
    targetLocation = {
      lat: parseFloat(assignment.value.delivery_latitude),
      lng: parseFloat(assignment.value.delivery_longitude)
    };
  }
  
  if (targetLocation) {
    // Add marker for destination
    new window.google.maps.Marker({
      position: targetLocation,
      map: map.value,
      title: currentStep.value === 'pickup' ? 'Pickup Location' : 'Delivery Location',
      icon: {
        url: currentStep.value === 'pickup' ? 'https://maps.google.com/mapfiles/ms/icons/green-dot.png' : 'https://maps.google.com/mapfiles/ms/icons/red-dot.png'
      }
    });
    
    // Center map on destination
    map.value.setCenter(targetLocation);
    map.value.setZoom(15);
  }
};

const fetchAssignment = async () => {
  try {
    const response = await api.get('/volunteer/assignments');
    const assignments = response.data.assignments || [];
    assignment.value = assignments.find(a => a.id == route.params.id);
    
    if (!assignment.value) {
      router.push('/volunteer');
      return;
    }

    // Determine current step based on assignment status and verification flags
    if (assignment.value.status === 'assigned' && !assignment.value.pickup_verified_by_donor) {
      currentStep.value = 'pickup';
    } else if (assignment.value.status === 'assigned' && assignment.value.pickup_verified_by_donor) {
      currentStep.value = 'delivery';
    }
    
    initMap();
  } catch (error) {
    console.error('Error fetching assignment:', error);
    router.push('/volunteer');
  }
};

const confirmPickup = async () => {
  confirmingPickup.value = true;
  try {
    // Update assignment status to in_progress (waiting for donor verification)
    await api.post('/volunteer/pickup-confirmed', { 
      request_id: assignment.value.id 
    });
    
    assignment.value.status = 'in_progress';
    alert('Pickup confirmed! Waiting for donor verification...');
    
    // Poll for donor verification
    pollForVerification('pickup');
  } catch (error) {
    console.error('Error confirming pickup:', error);
    alert('Failed to confirm pickup');
  } finally {
    confirmingPickup.value = false;
  }
};

const completeAssignment = async () => {
  completingAssignment.value = true;
  try {
    // Request delivery verification from requester
    await api.post('/volunteer/request-delivery', { 
      request_id: assignment.value.id 
    });
    
    assignment.value.status = 'delivery_pending';
    alert('Delivery confirmation sent! Waiting for requester verification...');
    
    // Poll for requester verification
    pollForVerification('delivery');
  } catch (error) {
    console.error('Error requesting delivery verification:', error);
    alert(error.response?.data?.error || 'Failed to request delivery verification');
  } finally {
    completingAssignment.value = false;
  }
};

const pollForVerification = (verificationType) => {
  const pollInterval = setInterval(async () => {
    try {
      const response = await api.get('/volunteer/assignments');
      const assignments = response.data.assignments || [];
      const currentAssignment = assignments.find(a => a.id == route.params.id);
      
      if (currentAssignment) {
        if (verificationType === 'pickup' && currentAssignment.pickup_verified_by_donor) {
          clearInterval(pollInterval);
          assignment.value = currentAssignment;
          currentStep.value = 'delivery';
          updateDirections();
          alert('Donor verified pickup! You can now proceed to delivery.');
        } else if (verificationType === 'delivery' && currentAssignment.status === 'completed') {
          clearInterval(pollInterval);
          alert('Requester verified delivery! Assignment completed successfully!');
          router.push('/volunteer');
        }
      }
    } catch (error) {
      console.error('Error polling for verification:', error);
    }
  }, 3000); // Poll every 3 seconds
  
  // Stop polling after 5 minutes
  setTimeout(() => clearInterval(pollInterval), 300000);
};

const goBack = () => {
  router.push('/volunteer');
};

onMounted(() => {
  fetchAssignment();
  
  // Wait for Google Maps to load
  const waitForGoogle = setInterval(() => {
    if (window.google?.maps) {
      clearInterval(waitForGoogle);
      // Wait a bit more for assignment data to load
      setTimeout(() => {
        if (assignment.value) {
          initMap();
        }
      }, 500);
    }
  }, 100);
});
</script>

<style scoped>
#map {
  height: 100vh;
  width: 100%;
}

.step-section {
  border-left: 4px solid #007bff;
  padding-left: 1rem;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  padding: 1rem;
}

.step-header h5 {
  color: #495057;
  font-weight: 600;
}

.assignment-info {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.donor-info, .requester-info {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.progress-section {
  border-top: 1px solid #dee2e6;
  padding-top: 1rem;
}

.btn-lg {
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  border-radius: 8px;
}

.badge {
  font-size: 0.8rem;
  padding: 0.5rem 0.75rem;
}

.container-fluid {
  height: 100vh;
  overflow: hidden;
}

.shadow-lg {
  box-shadow: -2px 0 10px rgba(0,0,0,0.1) !important;
}
</style>
