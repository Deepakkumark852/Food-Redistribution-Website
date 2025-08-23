<template>
  <div class="container mt-4">
    <h2>Full History</h2>
    <div class="mb-3 d-flex flex-wrap align-items-end">
      <input v-model="search" class="form-control me-2" style="max-width: 250px;" placeholder="Search...">
      <input v-model="date" type="date" class="form-control me-2" style="max-width: 180px;">
      <button class="btn btn-primary" @click="fetchHistory">Filter</button>
    </div>
    <div v-if="loading" class="text-center my-4">
      <div class="spinner-border"></div>
    </div>
    <table v-if="filteredList.length" class="table table-striped">
      <thead>
        <tr>
          <th v-for="col in columns" :key="col">{{ col }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in filteredList" :key="item.id">
          <td v-for="col in columns" :key="col">{{ item[col] }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else-if="!loading" class="alert alert-info">No history found.</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api from '../api';
import { useStore } from 'vuex';

const store = useStore();
const roles = store.getters.roles;
let endpoint = '';
if (roles.includes('donor')) endpoint = '/history/donations';
else if (roles.includes('requester')) endpoint = '/history/requests';
else if (roles.includes('volunteer')) endpoint = '/history/volunteering';

const historyList = ref([]);
const loading = ref(false);
const search = ref('');
const date = ref('');

const columns = computed(() => {
  if (!historyList.value.length) return [];
  return Object.keys(historyList.value[0]);
});

const filteredList = computed(() => {
  let arr = historyList.value;
  if (search.value) {
    arr = arr.filter(item => Object.values(item).some(v => String(v).toLowerCase().includes(search.value.toLowerCase())));
  }
  if (date.value) {
    arr = arr.filter(item => (item.created_at || item.assigned_at || '').slice(0, 10) === date.value);
  }
  return arr;
});

async function fetchHistory() {
  if (!endpoint) return;
  loading.value = true;
  try {
    const res = await api.get(endpoint);
    historyList.value = res.data.donations || res.data.requests || res.data.volunteering || [];
  } catch (e) {
    historyList.value = [];
  } finally {
    loading.value = false;
  }
}

onMounted(fetchHistory);
</script>
