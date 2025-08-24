<template>
  <div class="container">
    <div class="row">
      <div class="col-md-4 mb-3 mb-md-0">
        <HistorySidebar />
      </div>
      <div class="col-md-8">
        <div class="row">
          <div class="col-12">
            <h2 class="mb-4"><i class="fas fa-people-carry me-2"></i>Volunteer Dashboard</h2>
          </div>
        </div>
        <div class="row">
          <div class="col-md-6">
            <div class="card mb-4">
              <div class="card-header bg-white">
                <h5 class="my-1">Pending Requests</h5>
              </div>
              <div class="card-body">
                <div v-for="req in pendingRequests" :key="req.id" class="mb-3">
                  <div><b>Food:</b> {{ req.food_name }}</div>
                  <div><b>Pickup:</b> {{ req.pickup_address }}</div>
                  <div v-if="req.latitude && req.longitude" class="mt-2">
                    <iframe
                      :src="`https://www.google.com/maps?q=${req.latitude},${req.longitude}&z=15&output=embed`"
                      width="100%" height="120" style="border-radius:8px; border:0; min-width:180px; min-height:100px; aspect-ratio:16/9;"
                      allowfullscreen loading="lazy"></iframe>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-md-6">
            <div class="card mb-4">
              <div class="card-header bg-white">
                <h5 class="my-1">My Assignments</h5>
              </div>
              <div class="card-body">
                <div v-for="assign in myAssignments" :key="assign.id" class="mb-3">
                  <div><b>Food:</b> {{ assign.food_name }}</div>
                  <div><b>Pickup:</b> {{ assign.pickup_address }}</div>
                  <div v-if="assign.latitude && assign.longitude" class="mt-2">
                    <iframe
                      :src="`https://www.google.com/maps?q=${assign.latitude},${assign.longitude}&z=15&output=embed`"
                      width="100%" height="120" style="border-radius:8px; border:0; min-width:180px; min-height:100px; aspect-ratio:16/9;"
                      allowfullscreen loading="lazy"></iframe>
                  </div>
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
import { ref, onMounted } from 'vue';
import api from '../api';
import HistorySidebar from '../components/HistorySidebar.vue';

const pendingRequests = ref([]);
const myAssignments = ref([]);

const fetchData = async () => {
  const pending = await api.get('/volunteer/pending');
  const assigned = await api.get('/volunteer/assignments');
  pendingRequests.value = pending.data.requests || [];
  myAssignments.value = assigned.data.assignments || [];
};
onMounted(fetchData);
</script>
<style scoped>
.card { box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px; }
.badge-pending { background-color: #FFC107; color: #000; }
.badge-assigned { background-color: #0D6EFD; }
.badge-completed { background-color: #198754; }
</style>
