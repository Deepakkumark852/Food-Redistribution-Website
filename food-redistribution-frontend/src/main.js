import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import '@fortawesome/fontawesome-free/css/all.min.css';

import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';
import './style.css';

const app = createApp(App);
app.use(router);
app.use(store);
app.mount('#app');

// Dynamically inject Google Maps JS SDK
const gmapsKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
console.log('Google Maps API Key:', gmapsKey ? 'Present' : 'Missing');
if (gmapsKey) {
  const script = document.createElement('script');
  script.src = `https://maps.googleapis.com/maps/api/js?key=${gmapsKey}&libraries=places`;
  script.async = true;
  script.onload = () => {
    console.log('Google Maps API loaded successfully');
    window.googleMapsLoaded = true;
  };
  script.onerror = () => {
    console.error('Failed to load Google Maps API');
  };
  document.head.appendChild(script);
} else {
  console.error('Google Maps API key not found in environment variables');
}
