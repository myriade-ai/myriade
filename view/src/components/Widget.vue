<template>
  <Chart
    :data="queryResults"
    :context="props.context"
    :count="queryCount"
    :visualisationParams="props.context.visualisationParams"
  ></Chart>
</template>

<script setup lang="ts">
import Chart from '@/components/Chart.vue'
import { executeQuery } from '../stores/query'

import { defineProps, onMounted } from 'vue'
import { ref } from 'vue'

// Define your props
const props = defineProps({
  databaseId: {
    type: Number,
    required: true
  },
  sql: {
    type: String,
    required: true
  },
  context: {
    type: Object,
    required: true
  }
})

const queryResults = ref([] as Array<{ [key: string]: string | number | boolean | null }>)
const queryCount = ref(null as number | null)

onMounted(async () => {
  const { rows, count } = await executeQuery(props.databaseId, props.sql)
  queryResults.value = rows
  queryCount.value = count
})
</script>
