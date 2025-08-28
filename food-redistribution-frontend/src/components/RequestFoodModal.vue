<template>
  <div class="modal fade" :id="'requestModal' + foodId" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Request Food</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
      <!-- Error message -->
      <div v-if="error" class="alert alert-danger" role="alert">
        {{ error }}
      </div>
          <div v-if="!submitted">
            <div class="mb-3">
              <label class="form-label">Number of Servings</label>
              <input 
                type="number" 
                class="form-control" 
                v-model="servings" 
                min="1" 
                :max="maxServings"
                required
              >
              <div class="form-text">Available: {{ maxServings }} servings</div>
            </div>
            
            <div class="mb-3">
              <div class="form-check mb-2">
                <input 
                  class="form-check-input" 
                  type="radio" 
                  id="pickup" 
                  value="pickup" 
                  v-model="deliveryType"
                >
                <label class="form-check-label" for="pickup">
                  Self Pickup
                </label>
              </div>
              <div class="form-check mb-3">
                <input 
                  class="form-check-input" 
                  type="radio" 
                  id="delivery" 
                  value="delivery" 
                  v-model="deliveryType"
                >
                <label class="form-check-label" for="delivery">
                  Delivery Required
                </label>
              </div>
            </div>

            <div v-if="deliveryType === 'delivery'" class="mb-3">
              <label class="form-label">Delivery Address</label>
              <input 
                type="text" 
                class="form-control mb-2" 
                v-model="deliveryAddress"
                placeholder="Enter delivery address"
                ref="addressInput"
                required
              >
              <div class="form-text">
                <GoogleMapSingleMarker 
                  v-if="deliveryLocation.lat"
                  :lat="deliveryLocation.lat" 
                  :lng="deliveryLocation.lng" 
                  :markerTitle="'Delivery Location'"
                  height="200px"
                />
              </div>
            </div>

            <div class="alert alert-info">
              <strong>Pickup Location:</strong> {{ pickupAddress }}
            </div>
          </div>
          
          <div v-else class="text-center p-4">
            <div class="spinner-border text-primary mb-3" role="status" v-if="loading"></div>
            <div v-else>
              <i class="bi bi-check-circle-fill text-success" style="font-size: 3rem;"></i>
              <h5 class="mt-3">Request Submitted Successfully!</h5>
              <p>Your request has been received. The donor will contact you soon.</p>
            </div>
          </div>
        </div>
        
        <div class="modal-footer" v-if="!submitted">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button 
            type="button" 
            class="btn btn-primary" 
            @click="submitRequest"
            :disabled="loading"
          >
            <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
            Submit Request
          </button>
        </div>
        <div class="modal-footer" v-else>
          <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { Modal } from 'bootstrap';
import api from '../api';
import GoogleMapSingleMarker from './GoogleMapSingleMarker.vue';

const props = defineProps({
  foodId: {
    type: [String, Number],
    required: true
  },
  maxServings: {
    type: Number,
    required: true
  },
  pickupAddress: {
    type: String,
    required: true
  },
  initialLocation: {
    type: Object,
    default: () => ({
      lat: null,
      lng: null,
      address: ''
    })
  }
});

const emit = defineEmits(['request-submitted']);

const servings = ref(1);
const deliveryType = ref('pickup');
const deliveryAddress = ref('');
const deliveryLocation = ref({ lat: null, lng: null, address: '' });
const loading = ref(false);
const submitted = ref(false);
const error = ref(null);
const addressInput = ref(null);
let autocomplete = null;
let modal = null;

const isFormValid = computed(() => {
  if (deliveryType.value === 'delivery') {
    return servings.value > 0 && deliveryAddress.value.trim() !== '' && deliveryLocation.value.lat !== null;
  }
  return servings.value > 0;
});

// Initialize Google Places Autocomplete
const initAutocomplete = () => {
  console.log('Attempting to initialize autocomplete...');
  console.log('Google available:', !!window.google);
  console.log('Google Maps available:', !!(window.google && window.google.maps));
  console.log('Google Places available:', !!(window.google && window.google.maps && window.google.maps.places));
  console.log('Address input available:', !!addressInput.value);
  
  if (window.google && window.google.maps && window.google.maps.places && addressInput.value) {
    console.log('Creating autocomplete instance...');
    autocomplete = new window.google.maps.places.Autocomplete(
      addressInput.value,
      { 
        types: ['establishment', 'geocode'],
        componentRestrictions: { country: 'IN' }
      }
    );
    
    console.log('Autocomplete created successfully');
    
    autocomplete.addListener('place_changed', () => {
      const place = autocomplete.getPlace();
      console.log('Place changed:', place);
      if (place.geometry) {
        deliveryAddress.value = place.formatted_address || place.name;
        deliveryLocation.value = {
          lat: place.geometry.location.lat(),
          lng: place.geometry.location.lng(),
          address: place.formatted_address || place.name
        };
      }
    });
  } else {
    console.log('Prerequisites not met, retrying in 100ms...');
    setTimeout(initAutocomplete, 100);
  }
};

// Set initial delivery location from props or localStorage
const setInitialLocation = () => {
  // First try to get from localStorage (from search in RequestView)
  const storedLocation = localStorage.getItem('lastSearchedLocation');
  if (storedLocation) {
    try {
      const location = JSON.parse(storedLocation);
      if (location.address) {
        deliveryAddress.value = location.address;
        deliveryLocation.value = { ...location };
        return;
      }
    } catch (e) {
      console.error('Error parsing stored location:', e);
    }
  }

  // Then try to get from props (passed from parent)
  if (props.initialLocation?.address) {
    deliveryAddress.value = props.initialLocation.address;
    deliveryLocation.value = { ...props.initialLocation };
    return;
  }
  
  // If still no location, try to get current location
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const newLocation = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        
        // Try to get address from coordinates
        if (window.google?.maps) {
          const geocoder = new window.google.maps.Geocoder();
          geocoder.geocode(
            { location: newLocation },
            (results, status) => {
              if (status === 'OK' && results[0]) {
                deliveryLocation.value = {
                  ...newLocation,
                  address: results[0].formatted_address
                };
                deliveryAddress.value = results[0].formatted_address;
              }
            }
          );
        }
      },
      (error) => {
        console.error('Error getting current location:', error);
      }
    );
  }
};

const submitRequest = async () => {
  console.log('Submit button clicked!');
  console.log('Form valid:', isFormValid.value);
  console.log('Servings:', servings.value);
  console.log('Delivery type:', deliveryType.value);
  console.log('Delivery address:', deliveryAddress.value);
  
  if (!isFormValid.value) {
    console.log('Form is not valid, returning early');
    return;
  }
  
  loading.value = true;
  error.value = null;
  
  try {
    const requestData = {
      food_id: props.foodId,
      quantity: parseInt(servings.value),
      delivery_address: deliveryType.value === 'delivery' ? deliveryAddress.value : '',
      transport_arranged: deliveryType.value === 'pickup',
      status: 'pending'
    };

    // Include delivery location if it's a delivery
    if (deliveryType.value === 'delivery' && deliveryLocation.value.lat && deliveryLocation.value.lng) {
      requestData.delivery_latitude = deliveryLocation.value.lat;
      requestData.delivery_longitude = deliveryLocation.value.lng;
    }
    
    console.log('Submitting request with data:', requestData);
    
    const response = await api.post('/requests', requestData);
    console.log('Request submitted successfully:', response.data);
    
    submitted.value = true;
    emit('request-submitted');
    
    // Show success message and close modal after a short delay
    setTimeout(() => {
      const modal = Modal.getInstance(document.getElementById(`requestModal${props.foodId}`));
      if (modal) modal.hide();
    }, 1500);
    
  } catch (error) {
    console.error('Error submitting request:', error);
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        'Failed to submit request. Please try again.';
    error.value = errorMessage;
    console.error('Error details:', error.response?.data);
  } finally {
    loading.value = false;
  }
};

// Initialize modal when component is mounted
onMounted(() => {
  console.log('RequestFoodModal mounted');
  modal = new Modal(document.getElementById(`requestModal${props.foodId}`));
  setInitialLocation();
});

// Clean up autocomplete when component is unmounted
onUnmounted(() => {
  if (autocomplete) {
    window.google.maps.event.clearInstanceListeners(autocomplete);
  }
});

// Watch for delivery type changes to initialize autocomplete
watch(deliveryType, (newType) => {
  if (newType === 'delivery') {
    // Wait for DOM to update and show the input field
    nextTick(() => {
      console.log('Delivery type changed to delivery, initializing autocomplete...');
      setTimeout(() => {
        if (addressInput.value) {
          console.log('Address input now available, initializing...');
          initAutocomplete();
        }
      }, 100);
    });
  }
});

// Watch for changes in delivery address
watch(deliveryAddress, (newVal) => {
  if (!newVal) {
    deliveryLocation.value = { lat: null, lng: null, address: '' };
  }
});

// Expose show and hide methods
const show = () => modal?.show();
const hide = () => modal?.hide();

defineExpose({
  show,
  hide
});
</script>

<style scoped>
.modal-content {
  border-radius: 12px;
}
.modal-header {
  border-bottom: 1px solid #dee2e6;
  background-color: #f8f9fa;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
}
.modal-footer {
  border-top: 1px solid #dee2e6;
  background-color: #f8f9fa;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
}
</style>

<style>
/* Global styles for Google Places Autocomplete dropdown */
.pac-container {
  z-index: 9999 !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
  border: 1px solid #dee2e6 !important;
}

.pac-item {
  padding: 12px 16px !important;
  border-bottom: 1px solid #f1f3f4 !important;
  cursor: pointer !important;
}

.pac-item:hover {
  background-color: #f8f9fa !important;
}

.pac-item-selected {
  background-color: #e3f2fd !important;
}

.pac-matched {
  font-weight: 600 !important;
  color: #1976d2 !important;
}

.pac-item-query {
  font-size: 14px !important;
  color: #333 !important;
}

.pac-secondary {
  font-size: 12px !important;
  color: #666 !important;
}

/* Ensure modal doesn't interfere with autocomplete */
.modal {
  overflow: visible !important;
}

.modal-dialog {
  overflow: visible !important;
}

.modal-content {
  overflow: visible !important;
}

.modal-body {
  overflow: visible !important;
}
</style>
