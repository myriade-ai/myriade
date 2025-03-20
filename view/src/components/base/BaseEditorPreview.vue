<template>
  <div>
    <BaseEditor :modelValue="sqlQuery" :readOnly="true" />
    <BaseTable :data="rows" :count="count" />
  </div>
</template>

<script lang="ts" setup>
import BaseEditor from '@/components/base/BaseEditor.vue'
import BaseTable from '@/components/base/BaseTable.vue'
import { executeQuery } from '@/stores/query'
import { defineProps, ref, watch } from 'vue'

const props = defineProps({
  sqlQuery: String,
  databaseId: Number
})

const rows = ref([])
const count = ref(0)

const fetchData = async (query) => {
  try {
    const response = await executeQuery(props.databaseId, query) // Assuming databaseId is static for now
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
