<!-- Take chart id and display using echarts -->
<template>
  <div class="relative">
    <div class="flex justify-end mb-2">
      <button
        class="text-primary-500 hover:text-primary-700 flex items-center"
        title="Save chart to workspace"
        @click="handleToggleChartFavorite"
      >
        <ChartBarIconSolid v-if="isChartFavorite" class="h-4 w-4 text-yellow-500" />
        <ChartBarIcon v-else class="h-4 w-4" />
        <span class="ml-1 hidden lg:inline">{{ isChartFavorite ? 'saved' : 'save' }}</span>
      </button>
    </div>
    <Echart v-if="chartOption && chartOption.query_id" :option="chartOption" />
  </div>
</template>

<script setup lang="ts">
import Echart from '@/components/Echart.vue'
import { useChartStore } from '@/stores/chart'
import { ChartBarIcon } from '@heroicons/vue/24/outline'
import { ChartBarIcon as ChartBarIconSolid } from '@heroicons/vue/24/solid'
import { onMounted, ref } from 'vue'
const { fetchChart, toggleChartFavorite } = useChartStore()

const props = defineProps({
  chartId: String
})

const chartOption = ref({})
const isChartFavorite = ref(false)

const handleToggleChartFavorite = async () => {
  isChartFavorite.value = await toggleChartFavorite(props.chartId)
}

onMounted(async () => {
  const chart = await fetchChart(props.chartId)
  chart.config = { ...chart.config, query_id: chart.queryId }
  chartOption.value = chart.config
  isChartFavorite.value = chart.is_favorite
})
</script>
