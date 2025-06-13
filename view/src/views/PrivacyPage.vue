<template>
  <div class="p-6 space-y-6 max-w-5xl mx-auto">
    <!-- Page header -->
    <div>
      <h1 class="text-2xl font-semibold">Zero Knowledge Protection</h1>
      <p class="text-sm text-gray-600 mt-2">
        Zero Knowledge Protection is an advanced anonymization layer that ensures sensitive
        information is securely masked before any interaction with external AI models or services.
        <br />
        By applying robust anonymization techniques, it guarantees that no private or identifiable
        data is ever exposed, transmitted, or stored outside your trusted environment.<br />
        Enhance your data privacy and compliance, with full confidence that your default security
        standards remain uncompromised.
      </p>
    </div>

    <!-- Database selector -->
    <div class="flex items-center space-x-3">
      <label for="db-select" class="text-sm font-medium text-gray-700">Database</label>
      <select
        id="db-select"
        v-model="selectedDbId"
        @change="onDatabaseChange"
        class="border-gray-300 rounded-md shadow-xs focus:border-primary-500 focus:ring-primary-500 text-sm"
      >
        <option disabled value="">Select a database</option>
        <option v-for="db in databases" :key="db.id" :value="db.id">
          {{ db.name }}
        </option>
      </select>
    </div>

    <!-- Privacy configuration component -->
    <PrivacyConfiguration v-if="selectedDbId" :database-id="selectedDbId" />
    <div v-else class="text-sm text-gray-500">
      Please select a database to configure zero knowledge protection.
    </div>
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
