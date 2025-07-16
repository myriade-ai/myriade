<template>
  <div>Open Analytics List</div>
  <h1 class="text-2xl font-bold">Databases</h1>
  <div v-for="database in databasesStore.databases" :key="database.id">
    <router-link :to="`/openanalytics/${database.slug}`"> - {{ database.name }} </router-link>
  </div>
</template>
<script setup lang="ts">
import { useDatabasesStore } from '@/stores/databases'
import { onMounted } from 'vue'

const databasesStore = useDatabasesStore()

onMounted(async () => {
  await databasesStore.fetchDatabases({ refresh: false })
})
</script>
