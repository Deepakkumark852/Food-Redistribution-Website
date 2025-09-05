<template>
  <div class="history-view-container container-fluid py-4 px-lg-5">
    <!-- Page Header -->
    <div class="page-header d-flex justify-content-between align-items-center mb-4">
      <div>
        <h1 class="fw-bold mb-1">History</h1>
        <p class="text-muted mb-0">Review your past activity.</p>
      </div>
    </div>

    <!-- Filter Card -->
    <div class="card shadow-sm mb-4 filter-card">
      <div class="card-body d-flex flex-wrap align-items-center gap-3">
        <div class="flex-grow-1">
          <input v-model="search" class="form-control" placeholder="Search across all fields...">
        </div>
        <div class="filter-group d-flex gap-3">
          <input v-model="date" type="date" class="form-control">
          <select v-model="statusFilter" class="form-select" v-if="isDonorOrVolunteer">
            <option value="">All Statuses</option>
            <option v-for="status in availableStatuses" :key="status" :value="status">{{ formatStatus(status) }}</option>
          </select>
        </div>
        <button class="btn btn-outline-secondary" @click="fetchHistory" title="Refresh Data">
          <i class="fas fa-sync-alt"></i>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-3 fs-5">Loading your history...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredList.length === 0" class="text-center py-5 my-5 card bg-light">
      <i class="fas fa-history fa-4x text-muted mb-3"></i>
      <h4 class="text-muted">No History Found</h4>
      <p>Your activity will be recorded here once you start.</p>
    </div>

    <!-- History Table -->
    <div v-else class="card shadow-sm">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover table-striped mb-0">
            <thead class="table-light">
              <tr>
                <th v-for="col in columns" :key="col.key" class="py-3 px-3">{{ col.label }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in filteredList" :key="item.id">
                <td v-for="col in columns" :key="col.key" class="py-3 px-3">
                  <span v-if="col.key === 'status'">
                    <span class="badge rounded-pill" :class="statusBadgeClass(item[col.key])">
                      {{ formatStatus(item[col.key]) }}
                    </span>
                  </span>
                  <span v-else-if="col.isDate">
                    {{ formatDate(item[col.key]) }}
                  </span>
                  <span v-else>
                    {{ item[col.key] || 'N/A' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api from '../api';
import { useStore } from 'vuex';

const store = useStore();
const roles = store.getters.roles;

let endpoint = '';
const isDonorOrVolunteer = ref(false);
const availableStatuses = ref([]);

// Define role-specific configurations
const roleConfig = {
  donor: {
    endpoint: '/history/donations',
    columns: [
      { key: 'food_name', label: 'Food' },
      { key: 'original_quantity', label: 'Quantity' },
      { key: 'status', label: 'Status' },
      { key: 'created_at', label: 'Donated On', isDate: true },
      { key: 'expiry_date', label: 'Expires On', isDate: true },
    ],
    statuses: ['available', 'partially_claimed', 'fully_claimed', 'completed', 'expired']
  },
  requester: {
    endpoint: '/history/requests',
    columns: [
      { key: 'food_name', label: 'Food' },
      { key: 'quantity', label: 'Quantity' },
      { key: 'status', label: 'Status' },
      { key: 'requested_at', label: 'Requested On', isDate: true },
      { key: 'donor_name', label: 'From Donor' },
    ]
  },
  volunteer: {
    endpoint: '/history/volunteering',
    columns: [
      { key: 'food_name', label: 'Food' },
      { key: 'quantity', label: 'Quantity' },
      { key: 'status', label: 'Status' },
      { key: 'assigned_at', label: 'Assigned On', isDate: true },
      { key: 'donor_name', label: 'Donor' },
      { key: 'requester_name', label: 'Requester' },
    ],
    statuses: ['assigned', 'in_transit', 'pickup_verification_pending', 'delivery_verification_pending', 'completed', 'cancelled']
  }
};

// Determine current role config
let currentRoleKey = '';
if (roles.includes('admin')) { // Admin sees donor history by default, can be expanded later
  currentRoleKey = 'donor';
} else if (roles.includes('donor')) {
  currentRoleKey = 'donor';
} else if (roles.includes('volunteer')) {
  currentRoleKey = 'volunteer';
} else if (roles.includes('requester')) {
  currentRoleKey = 'requester';
}

const currentConfig = roleConfig[currentRoleKey] || {};
endpoint = currentConfig.endpoint || '';
if (currentRoleKey === 'donor' || currentRoleKey === 'volunteer') {
  isDonorOrVolunteer.value = true;
  availableStatuses.value = currentConfig.statuses || [];
}


const historyList = ref([]);
const loading = ref(false);
const search = ref('');
const date = ref('');
const statusFilter = ref('');

const columns = computed(() => currentConfig.columns || []);

const filteredList = computed(() => {
  let arr = historyList.value;
  if (search.value) {
    const searchTerm = search.value.toLowerCase();
    arr = arr.filter(item => Object.values(item).some(v => String(v).toLowerCase().includes(searchTerm)));
  }
  if (date.value) {
    arr = arr.filter(item => {
      const itemDate = (item.created_at || item.assigned_at || item.requested_at || '').slice(0, 10);
      return itemDate === date.value;
    });
  }
  if (statusFilter.value) {
    arr = arr.filter(item => item.status === statusFilter.value);
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
    console.error("Failed to fetch history:", e);
    historyList.value = [];
  } finally {
    loading.value = false;
  }
}

const formatStatus = (status) => {
  return (status || '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const options = { year: 'numeric', month: 'short', day: 'numeric' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

const statusBadgeClass = (status) => {
  switch (status) {
    case 'completed':
    case 'fully_claimed':
      return 'bg-success';
    case 'available':
      return 'bg-primary';
    case 'in_transit':
      return 'bg-info text-dark';
    case 'pickup_verification_pending':
    case 'delivery_verification_pending':
    case 'partially_claimed':
      return 'bg-warning text-dark';
    case 'expired':
    case 'cancelled':
      return 'bg-danger';
    default:
      return 'bg-secondary';
  }
};

onMounted(fetchHistory);
</script>

<style scoped>
.history-view-container {
  background-color: #f8f9fa;
}

.filter-card {
  border-radius: 12px;
}

.table {
  font-size: 0.95rem;
}

.table th {
  text-transform: uppercase;
  font-weight: 600;
  color: #666;
}

.table-hover tbody tr:hover {
  background-color: #f1f3f5;
}

.badge.rounded-pill {
  padding: 0.4em 0.8em;
  font-weight: 500;
}
</style>
