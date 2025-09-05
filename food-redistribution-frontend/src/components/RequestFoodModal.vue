<template>
  <div class="modal fade" :id="'requestModal' + foodId" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-lg">
      <div class="modal-content" style="border-radius: 16px;">
        <div class="modal-header border-0">
          <h4 class="modal-title fw-bold" id="modalTitle">
            <i class="fas fa-hand-holding-heart me-2 text-primary"></i>Request Food
          </h4>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body p-4">
          <div v-if="error" class="alert alert-danger" role="alert">
            {{ error }}
          </div>
          
          <div v-if="!submitted">
            <div class="row g-4">
              <!-- Left Column: Form -->
              <div class="col-md-6">
                <div class="mb-3">
                  <label for="servings" class="form-label fw-bold">How many servings do you need?</label>
                  <input 
                    type="number" 
                    class="form-control" 
                    id="servings"
                    v-model="servings" 
                    min="1" 
                    :max="maxServings"
                    required
                  >
                  <div class="form-text">Up to {{ maxServings }} servings available.</div>
                </div>
                
                <div class="mb-3">
                  <label class="form-label fw-bold">How will you get it?</label>
                  <div class="form-check form-check-inline">
                    <input class="form-check-input" type="radio" id="pickup" value="pickup" v-model="deliveryType">
                    <label class="form-check-label" for="pickup">I'll pick it up</label>
                  </div>
                  <div class="form-check form-check-inline">
                    <input class="form-check-input" type="radio" id="delivery" value="delivery" v-model="deliveryType">
                    <label class="form-check-label" for="delivery">I need delivery</label>
                  </div>
                </div>

                <div v-if="deliveryType === 'delivery'" class="mb-3 animate__animated animate__fadeIn">
                  <label for="deliveryAddress" class="form-label fw-bold">Delivery Address</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    id="deliveryAddress"
                    v-model="deliveryAddress"
                    placeholder="Start typing your address..."
                    ref="addressInput"
                    required
                  >
                </div>
              </div>

              <!-- Right Column: Map -->
              <div class="col-md-6">
                <div class="map-info-box h-100 p-3 rounded">
                  <h6 class="fw-bold">
                    <i class="fas fa-map-marked-alt me-2"></i>
                    {{ deliveryType === 'pickup' ? 'Pickup Location' : 'Delivery Location' }}
                  </h6>
                  <p v-if="deliveryType === 'pickup'" class="small text-muted">{{ pickupAddress }}</p>
                  
                  <div class="map-container-modal rounded overflow-hidden">
                    <GoogleMapSingleMarker 
                      v-if="mapLocation.lat"
                      :key="`${mapLocation.lat}-${mapLocation.lng}`"
                      :lat="mapLocation.lat" 
                      :lng="mapLocation.lng" 
                      :markerTitle="deliveryType === 'pickup' ? 'Pickup' : 'Delivery'"
                      aspect-ratio="16/9"
                    />
                    <div v-else class="d-flex align-items-center justify-content-center h-100 bg-light">
                      <p class="text-muted">Map will appear here.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Submission Success -->
          <div v-else class="text-center p-5">
            <i class="fas fa-check-circle text-success fa-4x mb-3"></i>
            <h3 class="fw-bold">Request Submitted!</h3>
            <p class="text-muted">Your request has been sent. You will be notified of the next steps.</p>
          </div>
        </div>
        
        <div class="modal-footer border-0 p-3" v-if="!submitted">
          <button type="button" class="btn btn-light" data-bs-dismiss="modal">Cancel</button>
          <button 
            type="button" 
            class="btn btn-primary" 
            @click="submitRequest"
            :disabled="loading || !isFormValid"
          >
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            {{ loading ? 'Submitting...' : 'Confirm Request' }}
          </button>
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
let modalInstance = null;
let autocomplete = null;

const mapLocation = computed(() => {
  if (deliveryType.value === 'delivery' && deliveryLocation.value.lat) {
    return deliveryLocation.value;
  }
  return props.initialLocation;
});

const isFormValid = computed(() => {
  if (deliveryType.value === 'pickup') {
    return servings.value > 0;
  }
  return servings.value > 0 && deliveryLocation.value.lat && deliveryLocation.value.lng;
});

const submitRequest = async () => {
  error.value = null;
  if (!isFormValid.value) {
    error.value = 'Please fill out all required fields, including a valid delivery address if needed.';
    return;
  }

  const payload = {
    food_id: props.foodId,
    quantity: servings.value,
    request_type: deliveryType.value,
    delivery_address: deliveryType.value === 'delivery' ? deliveryLocation.value.address : null,
    delivery_lat: deliveryType.value === 'delivery' ? deliveryLocation.value.lat : null,
    delivery_lng: deliveryType.value === 'delivery' ? deliveryLocation.value.lng : null,
  };

  try {
    loading.value = true;
    await api.post('/request', payload);
    submitted.value = true;
    emit('request-submitted');
  } catch (e) {
    error.value = e.response?.data?.error || 'An error occurred while submitting your request.';
  } finally {
    loading.value = false;
  }
};

const show = () => {
  if (modalInstance) {
    resetForm();
    modalInstance.show();
  }
};

const hide = () => {
  if (modalInstance) {
    modalInstance.hide();
  }
};

const resetForm = () => {
  servings.value = 1;
  deliveryType.value = 'pickup';
  deliveryAddress.value = '';
  deliveryLocation.value = { lat: null, lng: null, address: '' };
  error.value = null;
  submitted.value = false;
};

const initAutocomplete = () => {
  nextTick(() => {
    if (!addressInput.value) {
      console.error("Address input element not found for autocomplete.");
      return;
    }
    if (!window.google || !window.google.maps.places) {
      console.warn("Google Places API not ready for autocomplete.");
      return;
    }
    
    if (autocomplete) {
        google.maps.event.clearInstanceListeners(autocomplete);
    }

    autocomplete = new google.maps.places.Autocomplete(addressInput.value, {
      fields: ["address_components", "geometry", "icon", "name", "formatted_address"],
    });

    autocomplete.addListener('place_changed', () => {
      const place = autocomplete.getPlace();
      if (place.geometry) {
        deliveryLocation.value = {
          lat: place.geometry.location.lat(),
          lng: place.geometry.location.lng(),
          address: place.formatted_address,
        };
        deliveryAddress.value = place.formatted_address;
      } else {
        deliveryLocation.value = { lat: null, lng: null, address: '' };
      }
    });
  });
};

onMounted(() => {
  const modalEl = document.getElementById('requestModal' + props.foodId);
  if (modalEl) {
    modalInstance = new Modal(modalEl);
    modalEl.addEventListener('hidden.bs.modal', resetForm);
    modalEl.addEventListener('shown.bs.modal', () => {
      if (deliveryType.value === 'delivery') {
        initAutocomplete();
      }
    });
  }
});

onUnmounted(() => {
  if (modalInstance) {
    const modalEl = document.getElementById('requestModal' + props.foodId);
    if (modalEl) {
      modalEl.removeEventListener('hidden.bs.modal', resetForm);
    }
    modalInstance.dispose();
  }
  if (autocomplete && window.google) {
    google.maps.event.clearInstanceListeners(autocomplete);
  }
});

watch(deliveryType, (newVal) => {
  if (newVal === 'delivery') {
    initAutocomplete();
  }
});

defineExpose({ show, hide });
</script>

<style>
/* This will ensure the Google Places dropdown appears above the modal */
.pac-container {
  z-index: 1056 !important; /* Bootstrap modals are z-index 1055 */
}
</style>

<style scoped>
@import url('https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css');

.map-info-box {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  min-height: 250px;
  display: flex;
  flex-direction: column;
}

.map-container-modal {
  flex-grow: 1;
  min-height: 200px;
}
</style>
