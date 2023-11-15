<template>
  <div v-if="outputType == 'Value'" class="text-center text-4xl py-16">
    {{ getUniqueValueOfTable }}
  </div>
  <BaseTable v-else-if="outputType == 'Table'" :data="props.data" :count="props.count"></BaseTable>
  <fusioncharts v-else :type="visType" width="100%" dataFormat="json" :dataSource="dataSource" />
</template>

<script setup lang="ts">
import { defineComponent, computed, ref, watch, defineEmits } from 'vue'
import BaseTable from '@/components/BaseTable.vue'

const props = defineProps<{
  data: any[]
  count: number
  visualisationParams: any
}>()

const outputType = computed(() => props.visualisationParams.type ?? 'Table')
const columns = computed(() => (props.data.length ? Object.keys(props.data[0]) : ['a', 'b']))
const visType = computed(() => outputType.value.toLocaleLowerCase())

const getUniqueValueOfTable = computed(() => {
  return props.data[0][Object.keys(props.data[0])[0]]
})

const dataSource = computed(() => {
  return {
    chart: {
      caption: props.visualisationParams.caption, //Set the chart caption
      xAxisName: props.visualisationParams.xAxisName ?? columns.value[0], // Set the x-axis name
      yAxisName: props.visualisationParams.yAxisName ?? columns.value[1], // Set the y-axis name
      // numberSuffix: "K",
      theme: 'fusion'
    },
    // Chart Data - from step 2
    // { id: 2, name: "911" }
    data: props.data?.map((dict) => {
      if (props.visualisationParams.xKey && props.visualisationParams.yKey) {
        return {
          label: dict[props.visualisationParams.xKey],
          value: dict[props.visualisationParams.yKey]
        }
      }

      // If "count" is in the dictionary, use it as the y-axis value.
      // Otherwise, use the value of the first key in the dictionary.
      const keysSet = new Set(Object.keys(dict))
      const yDefaultKeys = ['count', 'total', 'sum', 'average', 'percentage']
      const xDefaultKeys = ['year', 'id', 'name']
      let yDefaultKey = yDefaultKeys.find((key) => keysSet.has(key))
      let xDefaultKey = xDefaultKeys.find((key) => keysSet.has(key))
      keysSet.delete(xDefaultKey)
      keysSet.delete(yDefaultKey)

      if (xDefaultKey === undefined) {
        // If there is no x-axis key, use the first key in the dictionary.
        xDefaultKey = keysSet.values().next().value
        keysSet.delete(xDefaultKey)
      }
      if (yDefaultKey === undefined) {
        // If there is no y-axis key, use the last key in the dictionary.
        yDefaultKey = keysSet.values().next().value
      }

      return {
        label: dict[xDefaultKey],
        value: dict[yDefaultKey]
      }
    })
  }
})
</script>
