<!-- Take chart id and display using echarts -->
<template>
  <div class="relative">
    <div class="flex justify-end -mr-2">
      <Button
        title="Save chart to workspace"
        variant="ghost"
        size="icon"
        @click="handleToggleChartFavorite"
      >
        <Star :class="isChartFavorite ? 'text-yellow-500 fill-yellow-500' : ''" />
      </Button>
    </div>
    <Echart v-if="chartOption && chartOption.query_id" :option="chartOption" />
  </div>
</template>

<script setup lang="ts">
import Echart from '@/components/Echart.vue'
import { useChartStore } from '@/stores/chart'
import { Star } from 'lucide-vue-next'
import { onMounted, ref } from 'vue'
import { Button } from './ui/button'
const { fetchChart, toggleChartFavorite } = useChartStore()

const props = defineProps({
  chartId: {
    type: String,
    required: true
  }
})

interface ChartConfig {
  query_id?: string
  [key: string]: unknown
}

const chartOption = ref<ChartConfig>({})
const isChartFavorite = ref(false)

const handleToggleChartFavorite = async () => {
  if (props.chartId) {
    isChartFavorite.value = await toggleChartFavorite(props.chartId)
  }
}

onMounted(async () => {
  const chart = await fetchChart(props.chartId)
  chart.config = { ...chart.config, query_id: chart.queryId }
  chartOption.value = chart.config
  isChartFavorite.value = chart.is_favorite
})
</script>
