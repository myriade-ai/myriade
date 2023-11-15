<template>
  <BaseTabs
    :tabs="visualisationOptions"
    :selected="visualisationType"
    @change="updateVisualisationParams"
  />
  <Chart :data="props.data" :count="props.count" :visualisationParams="visualisationParams" />
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import BaseTabs from '@/components/BaseTabs.vue'
import Chart from '@/components/Chart.vue'

const props = defineProps(['data', 'count', 'visualisationParams'])
const emit = defineEmits(['updateVisualisationParamsEvent'])

const hasOneValue = computed(
  () => props.data.length === 1 && Object.keys(props.data[0]).length === 1
)

const visualisationOptions = computed(() => {
  const defaultOptions = ['Table', 'Line', 'Doughnut2d', 'Column2d']
  return defaultOptions.concat(hasOneValue.value ? ['Value'] : []) // if hasOneValue, add 'Value' to options
})

const visualisationType = ref(props.visualisationParams?.type ?? 'Table')
const visualisationParams = computed(() => {
  return {
    ...props.visualisationParams,
    type: visualisationType.value
  }
})

const updateVisualisationParams = (type: string) => {
  visualisationType.value = type
  emit('updateVisualisationParamsEvent', {
    ...props.visualisationParams,
    type: type
  })
}
</script>
