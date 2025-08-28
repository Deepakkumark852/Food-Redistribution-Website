<template>
  <div class="history-sidebar card">
    <div class="card-header d-flex justify-content-between align-items-center">
      <span>History</span>
      <button class="btn btn-link p-0" @click="$router.push({ name: 'History' })" title="View full history">
        <i class="fas fa-angle-double-right"></i>
      </button>
    </div>
    <ul class="list-group list-group-flush">
      <li v-for="item in previewList" :key="item.id" class="list-group-item">
        <slot :item="item">{{ itemLabel(item) }}</slot>
      </li>
      <li v-if="previewList.length === 0" class="list-group-item text-muted">No history yet.</li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../api';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';

const router = useRouter();
const store = useStore();
const previewList = ref([]);

const roles = store.getters.roles;
let endpoint = '';
if (roles.includes('donor')) endpoint = '/history/donations';
else if (roles.includes('requester')) endpoint = '/history/requests';
else if (roles.includes('volunteer')) endpoint = '/history/volunteering';

function itemLabel(item) {
  if (roles.includes('donor')) return `${item.food_name} (${item.original_quantity})`;
  if (roles.includes('requester')) return `${item.food_name} requested (${item.quantity})`;
  if (roles.includes('volunteer')) return `${item.food_name} assigned (${item.status})`;
  return '';
}

onMounted(async () => {
  if (!endpoint) return;
  try {
    const res = await api.get(endpoint);
    const arr = res.data.donations || res.data.requests || res.data.volunteering || [];
    previewList.value = arr.slice(0, 5);
  } catch (e) {
    previewList.value = [];
  }
});
</script>

<style scoped>
.history-sidebar {
  min-width: 220px;
  max-width: 300px;
  margin-bottom: 1rem;
}
</style>
