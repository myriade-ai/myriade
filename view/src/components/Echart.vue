<template>
  <v-chart class="chart" :option="chartOption" />
</template>

<script setup lang="ts">
import { useQueryStore } from '@/stores/query'
import 'echarts'
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
const chartOption = computed(() => {
  return {
    ...props.option,
    dataset: {
      source: rows.value
    },
    grid: { containLabel: true },
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
