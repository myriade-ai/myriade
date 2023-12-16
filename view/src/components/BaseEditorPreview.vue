<template>
  <div>
    <BaseEditor :modelValue="sqlQuery" />
    <BaseTable :data="rows" :count="count" />
  </div>
</template>

<script lang="ts" setup>
import BaseEditor from './BaseEditor.vue'
import BaseTable from './BaseTable.vue'
import { executeQuery } from '../stores/query'
import { defineProps, ref, watch } from 'vue'

const props = defineProps({
  sqlQuery: String
})

const rows = ref([])
const count = ref(0)

const fetchData = async (query) => {
  try {
    const response = await executeQuery(2, query) // Assuming databaseId is static for now
    rows.value = response.rows
    count.value = response.count
  } catch (error) {
    console.error('Error fetching data:', error)
  }
}

watch(
  () => props.sqlQuery,
  (newQuery) => {
    if (newQuery) {
      fetchData(newQuery)
    }
  },
  { immediate: true }
)
</script>
