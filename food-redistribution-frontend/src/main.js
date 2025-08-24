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
if (gmapsKey) {
  const script = document.createElement('script');
  script.src = `https://maps.googleapis.com/maps/api/js?key=${gmapsKey}&libraries=places`;
  script.async = true;
  document.head.appendChild(script);
}
