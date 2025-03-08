<template>
  <v-chart class="chart" :option="chartOption" />
</template>

<script setup>
import 'echarts'
import VChart from 'vue-echarts'
import { computed } from 'vue'

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
    grid: { containLabel: true },
    tooltip: { extraCssText: 'width:200px; white-space:pre-wrap;' }
  }
})
</script>

<style scoped>
.chart {
  min-height: 400px;
  background-color: white;
  border-radius: 0.28571rem;
}
</style>
