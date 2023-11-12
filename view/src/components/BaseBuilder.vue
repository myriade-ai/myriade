<template>
  <BaseTabs :tabs="options" :selected="outputType" @change="updateVisualisationParams" />
  <Chart
    :data="data2"
    :context="context"
    :count="count"
    :visualisationParams="visualisationParams"
  />
</template>

<script lang="ts">
import { defineComponent, computed, ref, watch, defineEmits } from 'vue'
import BaseTable from '@/components/BaseTable.vue'
import BaseTabs from '@/components/BaseTabs.vue'

export default defineComponent({
  name: 'BaseBuilder',
  props: ['data', 'context', 'count', 'visualisationParams'],
  components: {
    BaseTable,
    BaseTabs
  },
  emits: ['updateVisualisationParamsEvent'],
  setup: (props, context) => {
    const options = computed(() => {
      const defaultOptions = ['Table', 'Line', 'Doughnut2d', 'Column2d']
      return defaultOptions.concat(hasOneValue.value ? ['Value'] : [])
    })
    const outputType = ref('Table')

    const hasOneValue = computed(() => {
      return props.data.length === 1 && Object.keys(props.data[0]).length === 1
    })
    const hasTwoKeys = computed(() => {
      return props.data.length >= 1 && Object.keys(props.data[0]).length === 2
    })

    const defaultVisualisation = computed(() => {
      if (props.visualisationParams) {
        return props.visualisationParams.type
      }
      if (hasOneValue.value) {
        return 'Value'
      } else if (hasTwoKeys.value) {
        return 'Line'
      } else {
        return 'Table'
      }
    })

    outputType.value = props.context.outputType ?? defaultVisualisation.value

    // update defaultVisualisation when props.data changes
    watch(
      () => props.data,
      () => {
        console.log('props.context.outputType', props.context.outputType)
        outputType.value = props.context.outputType ?? defaultVisualisation.value
      }
    )

    // TODO: remove ?
    // outputType.value = defaultVisualisation.value
    const updateVisualisationParams = (type: string) => {
      console.log('updateType', type)
      outputType.value = type
      context.emit('updateVisualisationParamsEvent', {
        ...props.visualisationParams,
        type: type
      })
    }

    const data2 = computed(() => props.data)
    const count = computed(() => props.count)

    const visType = computed(() => outputType.value.toLocaleLowerCase())
    return {
      updateVisualisationParams,
      outputType,
      options,
      data2,
      hasOneValue,
      type: visType, // "doughnut2d", // "line", // "column2d",
      count
    }
  }
})
</script>
