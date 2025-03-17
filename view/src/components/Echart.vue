<template>
  <v-chart class="chart" :option="chartOption" />
</template>

<script setup lang="ts">
import 'echarts'
import { computed } from 'vue'
import VChart from 'vue-echarts'

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
