<template>
  <div class="p-6 space-y-6 max-w-5xl mx-auto">
    <!-- Page header -->
    <div>
      <h1 class="text-2xl font-semibold">Privacy Settings</h1>
      <p class="text-sm text-gray-600">Configure column-level privacy for your databases.</p>
    </div>

    <!-- Database selector -->
    <div class="flex items-center space-x-3">
      <label for="db-select" class="text-sm font-medium text-gray-700">Database</label>
      <select
        id="db-select"
        v-model="selectedDbId"
        @change="onDatabaseChange"
        class="border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
      >
        <option disabled value="">Select a database</option>
        <option v-for="db in databases" :key="db.id" :value="db.id">
          {{ db.name }}
        </option>
      </select>
    </div>

    <!-- Privacy configuration component -->
    <PrivacyConfiguration v-if="selectedDbId" :database-id="Number(selectedDbId)" />
    <div v-else class="text-sm text-gray-500">Please select a database to configure privacy.</div>
  </div>
</template>

<script setup lang="ts">
import PrivacyConfiguration from '@/components/PrivacyConfiguration.vue'
import { useDatabasesStore } from '@/stores/databases'
import { computed, onMounted, ref } from 'vue'

const dbStore = useDatabasesStore()

// Fetch databases on mount (if not already loaded)
onMounted(async () => {
  await dbStore.fetchDatabases({ refresh: false })
})

const databases = computed(() => dbStore.sortedDatabases)
const selectedDbId = ref<number | ''>('')

function onDatabaseChange() {
  // nothing else needed; component reacts to prop
}
</script>
