<template>
  <div class="map-container" :style="{ aspectRatio: aspectRatio }">
    <div ref="map" class="map" style="width: 100%; height: 100%; min-height: 260px;"></div>
  </div>
</template>
<script setup>
import { ref, onMounted, watch, defineProps, defineEmits } from 'vue';
const props = defineProps({
  userLocation: Object, // {lat, lng}
  donors: Array, // [{lat, lng, id, ...}]
  aspectRatio: { type: String, default: '16/9' },
  highlightId: [String, Number]
});
const emit = defineEmits(['marker-click']);
const map = ref();
let gmap = null;
let userMarker = null;
let donorMarkers = [];
const userIcon = {
  url: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
  scaledSize: new google.maps.Size(40, 40)
};
const donorIcon = {
  url: 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png',
  scaledSize: new google.maps.Size(36, 36)
};
const donorIconHighlight = {
  url: 'https://maps.google.com/mapfiles/ms/icons/green-dot.png',
  scaledSize: new google.maps.Size(40, 40)
};
function renderMap() {
  if (!window.google) return;
  const center = props.userLocation?.lat && props.userLocation?.lng
    ? { lat: props.userLocation.lat, lng: props.userLocation.lng }
    : (props.donors[0] ? { lat: props.donors[0].latitude, lng: props.donors[0].longitude } : { lat: 20.5937, lng: 78.9629 });
  gmap = new google.maps.Map(map.value, {
    center,
    zoom: 12,
    mapTypeControl: false,
    streetViewControl: false,
    fullscreenControl: false
  });
  // User marker (red)
  if (props.userLocation?.lat && props.userLocation?.lng) {
    userMarker = new google.maps.Marker({
      position: { lat: props.userLocation.lat, lng: props.userLocation.lng },
      map: gmap,
      icon: userIcon,
      title: 'Your Location'
    });
  }
  // Donor markers (blue, green if highlighted)
  donorMarkers = props.donors.map(donor => {
    if (!donor.latitude || !donor.longitude) return null;
    const marker = new google.maps.Marker({
      position: { lat: donor.latitude, lng: donor.longitude },
      map: gmap,
      icon: donor.id === props.highlightId ? donorIconHighlight : donorIcon,
      title: donor.food_name || 'Donor'
    });
    marker.addListener('click', () => emit('marker-click', donor.id));
    return marker;
  }).filter(Boolean);
}
onMounted(() => {
  if (window.google) renderMap();
  else {
    const interval = setInterval(() => {
      if (window.google) {
        clearInterval(interval);
        renderMap();
      }
    }, 200);
  }
});
watch(() => [props.userLocation, props.donors, props.highlightId], () => {
  if (gmap) renderMap();
});
</script>
<style scoped>
.map-container { width: 100%; position: relative; }
.map { width: 100%; height: 100%; border-radius: 8px; min-height: 260px; }
</style>
