<template>
  <v-chart class="chart" :option="chartOption" />
</template>

<script setup lang="ts">
import { useQueryStore } from '@/stores/query'
import 'echarts'
import type { ECBasicOption } from 'echarts/types/dist/shared'
import { computed, onMounted, ref } from 'vue'
import VChart from 'vue-echarts'

const { fetchQueryResults } = useQueryStore()

const rows = ref([])

// Define the prop
const props = defineProps({
  option: {
    type: Object,
    required: true
  }
})

// Create a computed property that watches the input option
const chartOption = computed<ECBasicOption>(() => {
  return {
    ...props.option,
    title: {
      text: props.option.title.text || '',
      top: 5
    },
    // Keep it empty, it looks better
    grid: {},
    dataset: {
      source: rows.value
    },
    tooltip: { extraCssText: 'width:200px; white-space:pre-wrap;' }
  }
})

onMounted(async () => {
  const results = await fetchQueryResults(props.option.query_id)
  rows.value = results.rows
})
</script>

<style scoped>
.chart {
  min-height: 400px;
  background-color: white;
  border-radius: 0.28571rem;
}
</style>
