<template>
  <div>
    <BaseEditor :modelValue="sqlQuery" :readOnly="true" />
    <BaseTable :data="rows" :count="count" />
  </div>
</template>

<script lang="ts" setup>
import BaseEditor from '@/components/base/BaseEditor.vue'
import BaseTable from '@/components/base/BaseTable.vue'
import { useQueryStore } from '@/stores/query'
import { defineProps, onMounted, ref } from 'vue'

const { fetchQuery, fetchQueryResults } = useQueryStore()

const props = defineProps({
  queryId: Number,
  databaseId: Number
})

const rows = ref([])
const count = ref(0)
const sqlQuery = ref('')

onMounted(async () => {
  try {
    const query = await fetchQuery(props.queryId)
    sqlQuery.value = query.sql
    const result = await fetchQueryResults(props.queryId)
    rows.value = result.rows
    count.value = result.count
  } catch (error) {
    console.error('Error fetching data:', error)
  }
})
</script>
