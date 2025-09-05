<template>
  <div class="map-container" :style="{ aspectRatio: aspectRatio }">
    <div ref="map" class="map" style="width: 100%; height: 100%; min-height: 200px;"></div>
  </div>
</template>
<script setup>
import { ref, onMounted, watch, defineProps } from 'vue';
const props = defineProps({
  lat: Number,
  lng: Number,
  aspectRatio: { type: String, default: '16/9' },
  markerTitle: { type: String, default: '' }
});
const map = ref();
let gmap = null;
let marker = null;
function renderMap() {
  if (!window.google || !props.lat || !props.lng) return;
  const center = { lat: props.lat, lng: props.lng };

  if (!gmap) {
    gmap = new google.maps.Map(map.value, {
      center,
      zoom: 15,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false
    });
    marker = new google.maps.Marker({
      position: center,
      map: gmap,
      title: props.markerTitle || 'Location'
    });
  } else {
    gmap.setCenter(center);
    marker.setPosition(center);
  }
}

onMounted(() => {
  if (window.google) {
    renderMap();
  } else {
    const interval = setInterval(() => {
      if (window.google) {
        clearInterval(interval);
        renderMap();
      }
    }, 200);
  }
});

watch(() => [props.lat, props.lng], () => {
  if (gmap) {
    renderMap();
  }
});
</script>
<style scoped>
.map-container { width: 100%; position: relative; }
.map { width: 100%; height: 100%; border-radius: 8px; min-height: 200px; }
</style>
