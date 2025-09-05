<template>
  <div class="container-fluid py-4 px-lg-5">
    <div class="row">
      <!-- Filters Sidebar -->
      <div class="col-lg-3">
        <div class="filters-sidebar card p-3 sticky-top">
          <h4 class="mb-3"><i class="fas fa-filter me-2"></i>Filters</h4>
          <div class="mb-3">
            <label for="search-food" class="form-label">Food Name</label>
            <input v-model="filterFood" @input="fetchDonations" class="form-control" id="search-food" placeholder="e.g., Pizza, Salad" />
          </div>
          <div class="mb-3">
            <label for="expiry-date" class="form-label">Expires After</label>
            <input v-model="filterExpiry" @input="fetchDonations" type="date" class="form-control" id="expiry-date" :min="today" />
          </div>
          <div class="mb-3">
            <label for="address-search" class="form-label">Your Location</label>
            <input ref="addressInput" class="form-control" id="address-search" placeholder="Search for a location..." />
            <div v-if="locationError" class="text-danger small mt-1">{{ locationError }}</div>
          </div>
          <button class="btn btn-primary w-100" @click="fetchDonations"><i class="fas fa-sync-alt me-2"></i>Refresh Results</button>
        </div>
      </div>

      <!-- Main Content -->
      <div class="col-lg-9">
        <!-- Map View -->
        <div class="card map-card mb-4">
          <GoogleMapMultiMarker
            :userLocation="userLocation"
            :donors="donations"
            :highlightId="highlightedId"
            @marker-click="onMarkerClick"
            aspectRatio="21/9"
          />
        </div>

        <!-- List View -->
        <div class="list-view">
          <div v-if="donations.length === 0" class="alert alert-info text-center">
            No donations found matching your criteria. Try expanding your search!
          </div>
          <div v-else class="row g-4 row-cols-1 row-cols-md-2 row-cols-xl-3">
            <div v-for="donation in filteredDonations" :key="donation.id" class="col">
              <div
                :ref="el => cardRefs[donation.id] = el"
                class="donation-card card h-100 d-flex flex-column"
                :class="{ 'highlighted': highlightedId === donation.id }"
                @mouseenter="highlightedId = donation.id"
                @mouseleave="highlightedId = null"
              >
                <img v-if="donation.food_image_url" :src="donation.food_image_url" class="card-img-top" alt="Food image" @click="goToDetails(donation.id)" style="cursor: pointer;">
                <div v-else class="card-img-top no-image d-flex align-items-center justify-content-center bg-light" @click="goToDetails(donation.id)" style="cursor: pointer;">
                  <i class="fas fa-utensils fa-3x text-muted"></i>
                </div>
                <div class="card-body d-flex flex-column flex-grow-1">
                  <h5 class="card-title">{{ donation.food_name }}</h5>
                  <p class="card-text mb-1">
                    <i class="fas fa-box me-2"></i><strong>Quantity:</strong> {{ donation.remaining_quantity }} servings
                  </p>
                  <p class="card-text mb-1">
                    <i class="fas fa-calendar-times me-2"></i><strong>Expires:</strong> {{ formatDate(donation.expiry_date) }}
                  </p>
                  <p v-if="donation.distance" class="card-text mb-2">
                    <i class="fas fa-road me-2"></i><strong>Distance:</strong> {{ donation.distance.toFixed(2) }} km away
                  </p>
                  <div class="mt-auto pt-2">
                    <span class="badge" :class="getDonationStatusClass(donation.status)">{{ formatStatus(donation.status) }}</span>
                  </div>
                </div>
                <div class="card-footer bg-transparent border-0 pt-0">
                   <button @click="goToDetails(donation.id)" class="btn btn-primary w-100">View Details</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, computed, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api';
import GoogleMapMultiMarker from '../components/GoogleMapMultiMarker.vue';
const router = useRouter();
const userLocation = ref({ address: '', lat: null, lng: null });
const donations = ref([]);
const filterFood = ref('');
const filterExpiry = ref('');
const highlightedId = ref(null);
const cardRefs = ref({});
const addressInput = ref();
const locationError = ref('');
const today = new Date().toISOString().split('T')[0];

const fetchDonations = async () => {
  let params = {};
  if (userLocation.value.lat && userLocation.value.lng) {
    params.latitude = userLocation.value.lat;
    params.longitude = userLocation.value.lng;
  }
  if (filterFood.value) params.food_name = filterFood.value;
  if (filterExpiry.value) params.expiry_date = filterExpiry.value;
  try {
    const res = await api.get('/donations', { params });
    donations.value = res.data.donations || [];
  } catch (error) {
    console.error("Failed to fetch donations:", error);
    donations.value = [];
  }
};

const getUserLocationAndFetch = () => {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      pos => {
        userLocation.value.lat = pos.coords.latitude;
        userLocation.value.lng = pos.coords.longitude;
        locationError.value = '';
        fetchDonations(); // Fetch with location
      },
      err => {
        console.warn(`Geolocation error: ${err.message}`);
        locationError.value = `Could not get location: ${err.message}. Please enable location services or use the search bar.`;
        fetchDonations(); // Fetch without location as a fallback
      }
    );
  } else {
    locationError.value = "Geolocation is not supported by this browser.";
    fetchDonations(); // Fetch without location
  }
};

onMounted(() => {
  getUserLocationAndFetch(); // This function now orchestrates the initial data load.
  
  // Google Maps Places Autocomplete for address search
  const waitForGoogle = setInterval(() => {
    if (window.google && window.google.maps && window.google.maps.places) {
      clearInterval(waitForGoogle);
      const autocomplete = new google.maps.places.Autocomplete(addressInput.value, {
        fields: ["address_components", "geometry", "icon", "name"],
      });
      autocomplete.addListener('place_changed', () => {
        const place = autocomplete.getPlace();
        if (place.geometry) {
          userLocation.value.lat = place.geometry.location.lat();
          userLocation.value.lng = place.geometry.location.lng();
          fetchDonations();
        }
      });
    }
  }, 200);
  setTimeout(() => clearInterval(waitForGoogle), 10000); // Stop trying after 10s
});

const filteredDonations = computed(() => donations.value);

function onMarkerClick(id) {
  highlightedId.value = id;
  const card = cardRefs.value[id];
  if (card) {
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

function goToDetails(id) {
  router.push(`/food/${id}`);
}

function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString(undefined, {
    year: 'numeric', month: 'long', day: 'numeric'
  });
}

function getDonationStatusClass(status) {
  switch (status) {
    case 'available': return 'bg-success';
    case 'partially_claimed': return 'bg-warning text-dark';
    case 'fully_claimed': return 'bg-danger';
    default: return 'bg-secondary';
  }
}

function formatStatus(status) {
  return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}
</script>
<style scoped>
.donation-card {
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
  border-radius: 12px;
  overflow: hidden;
}
.donation-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.12);
}
.donation-card.highlighted {
  box-shadow: 0 0 0 3px var(--primary-color, #4F46E5), 0 8px 24px rgba(0,0,0,0.15);
  border: 1px solid var(--primary-color, #4F46E5);
}
.card-img-top {
  height: 180px;
  object-fit: cover;
}
.no-image {
  height: 180px;
}
.card-footer {
  padding-top: 0;
}
</style>
