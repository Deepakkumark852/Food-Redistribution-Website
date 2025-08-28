<template>
  <div class="container py-3">
    <div class="row mb-2">
      <div class="col-12 d-flex flex-wrap align-items-center gap-2">
        <input v-model="filterFood" @input="fetchDonations" class="form-control w-auto" placeholder="Search food name..." />
        <input v-model="filterExpiry" @input="fetchDonations" type="date" class="form-control w-auto" placeholder="Expiry date" />
        <input ref="addressInput" class="form-control w-auto" placeholder="Search location..." style="min-width:220px;" />
        <button class="btn btn-outline-secondary" @click="fetchDonations">Refresh</button>
      </div>
    </div>
    <div class="row mb-3">
      <div class="col-12">
        <GoogleMapMultiMarker
          :userLocation="userLocation"
          :donors="donations"
          :highlightId="highlightedId"
          @marker-click="onMarkerClick"
        />
      </div>
    </div>
    <div class="row g-2">
      <div class="col-12">
        <div v-for="(donation, idx) in filteredDonations" :key="donation.id" :ref="el => cardRefs[donation.id] = el" :class="['donation-card', { 'highlighted': highlightedId === donation.id }]" @click="goToDetails(donation.id)">
          <div class="card p-3 mb-2 shadow-sm w-100" style="cursor:pointer;">
            <div class="d-flex flex-column flex-md-row align-items-md-center justify-content-between">
              <div>
                <h5 class="mb-1">{{ donation.food_name }}</h5>
                <div class="mb-1"><b>Quantity:</b> {{ donation.quantity }}</div>
                <div class="mb-1"><b>Expires:</b> {{ donation.expiry_date }}</div>
                <div class="mb-1"><b>Pickup:</b> {{ donation.pickup_address }}</div>
                <div class="mb-1"><b>Time:</b> {{ donation.pickup_time }}</div>
                <div class="mb-1"><b>Donor:</b> {{ donation.donor_id }}</div>
                <div v-if="donation.distance"><b>Distance:</b> {{ donation.distance.toFixed(2) }} km</div>
                <div v-if="donation.special_instructions" class="small text-muted">{{ donation.special_instructions }}</div>
              </div>
              <div class="ms-md-4 mt-2 mt-md-0">
                <span class="badge bg-primary">ID: {{ donation.id }}</span>
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
const cardRefs = {};
const addressInput = ref();
const fetchDonations = async () => {
  let params = {};
  if (userLocation.value.lat && userLocation.value.lng) {
    params.latitude = userLocation.value.lat;
    params.longitude = userLocation.value.lng;
  }
  if (filterFood.value) params.food_name = filterFood.value;
  if (filterExpiry.value) params.expiry_date = filterExpiry.value;
  const res = await api.get('/donations', { params });
  donations.value = res.data.donations || [];
};
onMounted(() => {
  fetchDonations(); // Initial fetch
  // Try to get current location as default
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(pos => {
      userLocation.value.lat = pos.coords.latitude;
      userLocation.value.lng = pos.coords.longitude;
      fetchDonations(); // Fetch again with location
    }, (err) => {
      console.warn(`WARN: ${err.message}`);
      // fetchDonations(); // Already called initially
    });
  }
  // Google Maps Places Autocomplete for address search
  const waitForGoogle = setInterval(() => {
    if (window.google && window.google.maps && window.google.maps.places) {
      clearInterval(waitForGoogle);
      const autocomplete = new window.google.maps.places.Autocomplete(addressInput.value);
      autocomplete.addListener('place_changed', () => {
        const place = autocomplete.getPlace();
        if (place.geometry) {
          userLocation.value.lat = place.geometry.location.lat();
          userLocation.value.lng = place.geometry.location.lng();
          userLocation.value.address = place.formatted_address;
          fetchDonations();
        }
      });
    }
  }, 200);
});
const filteredDonations = computed(() => donations.value);
function onMarkerClick(id) {
  highlightedId.value = id;
  nextTick(() => {
    const el = cardRefs[id];
    if (el && el.scrollIntoView) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  });
}
function goToDetails(id) {
  router.push(`/food/${id}`);
}
</script>
<style scoped>
.donation-card { transition: box-shadow 0.2s, border 0.2s; border-radius: 8px; }
.donation-card.highlighted { box-shadow: 0 0 0 3px #4F46E5, 0 8px 24px rgba(0,0,0,0.10); border: 2px solid #4F46E5; }
.card { margin-bottom: 0.5rem; }
</style>
