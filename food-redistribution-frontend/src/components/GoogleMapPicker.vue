<template>
  <div class="map-container" :style="{ aspectRatio: aspectRatio }">
    <input ref="input" class="form-control mb-2" :placeholder="placeholder" />
    <div ref="map" class="map" style="width: 100%; height: 100%; min-height: 220px;"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, defineProps, defineEmits } from 'vue';
const props = defineProps({
  modelValue: Object,
  aspectRatio: { type: String, default: '16/9' },
  placeholder: { type: String, default: 'Search address...' }
});
const emit = defineEmits(['update:modelValue']);
const input = ref();
const map = ref();
let marker = null;
let autocomplete = null;

onMounted(() => {
  // Wait for Google Maps SDK
  if (!window.google) return;
  const center = props.modelValue?.lat && props.modelValue?.lng
    ? { lat: props.modelValue.lat, lng: props.modelValue.lng }
    : { lat: 20.5937, lng: 78.9629 }; // India center
  const gmap = new google.maps.Map(map.value, {
    center,
    zoom: 13,
    mapTypeControl: false,
    streetViewControl: false,
    fullscreenControl: false
  });
  marker = new google.maps.Marker({
    position: center,
    map: gmap,
    draggable: true
  });
  gmap.addListener('click', e => {
    marker.setPosition(e.latLng);
    emit('update:modelValue', { lat: e.latLng.lat(), lng: e.latLng.lng() });
  });
  marker.addListener('dragend', e => {
    emit('update:modelValue', { lat: e.latLng.lat(), lng: e.latLng.lng() });
  });
  autocomplete = new google.maps.places.Autocomplete(input.value);
  autocomplete.addListener('place_changed', () => {
    const place = autocomplete.getPlace();
    if (place.geometry) {
      gmap.setCenter(place.geometry.location);
      marker.setPosition(place.geometry.location);
      emit('update:modelValue', {
        lat: place.geometry.location.lat(),
        lng: place.geometry.location.lng(),
        address: place.formatted_address
      });
    }
  });
});

watch(() => props.modelValue, val => {
  if (marker && val?.lat && val?.lng) {
    marker.setPosition({ lat: val.lat, lng: val.lng });
  }
});
</script>

<style scoped>
.map-container { width: 100%; position: relative; }
.map { width: 100%; height: 100%; border-radius: 8px; min-height: 220px; }
</style>
