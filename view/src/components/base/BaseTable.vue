<template>
  <div class="relative">
    <button
      class="absolute px-2 py-1 text-sm font-medium text-black bg-gray-100 rounded-md shadow-xs hover:bg-gray-300 focus:outline-hidden focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
      style="top: 10px; right: 10px; z-index: 100"
      @click="copyToClipboard"
    >
      {{ copyText }}
    </button>
    <div ref="table"></div>
  </div>
</template>

<script setup lang="ts">
import { TabulatorFull as Tabulator } from 'tabulator-tables' //import Tabulator library
import 'tabulator-tables/dist/css/tabulator_semanticui.min.css'
import { defineProps, onMounted, ref, watch } from 'vue'

const table = ref(null) // reference to your table element
const tabulator = ref(null) // variable to hold your table

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
    required: true
  },
  count: {
    type: Number,
    default: 0
  }
})

const copyText = ref('copy')
const copyToClipboard = () => {
  tabulator.value?.copyToClipboard('all')
  copyText.value = 'copied'
  setTimeout(() => {
    copyText.value = 'copy'
  }, 1000)
}

watch(
  props,
  () => {
    tabulator.value?.setData(hideEncryptedFields(props.data))
  },
  { deep: true }
)
const hideEncryptedFields = (rows: any[]) => {
  return rows.map((row) => {
    const newRow = { ...row }
    for (const key in newRow) {
      if (typeof newRow[key] === 'string' && newRow[key].startsWith('encrypted:')) {
        newRow[key] = '***hidden***'
      }
    }
    return newRow
  })
}

onMounted(() => {
  tabulator.value = new Tabulator(table.value, {
    clipboard: true,
    data: hideEncryptedFields(props.data),
    reactiveData: true,
    autoColumns: true,
    layout: 'fitDataStretch',
    columnDefaults: {
      maxWidth: 500
    },
    pagination: true,
    paginationSize: 10,
    paginationCounter: (pageSize: number, currentRow: number) => {
      return `Showing ${currentRow}-${currentRow + pageSize} of ${props.count} rows`
    }
  })
})
</script>
<style>
.tabulator .tabulator-footer .tabulator-page.active {
  color: black;
  background-color: #f3f4f6;
}
.tabulator {
  margin-top: 0.5rem;
}
</style>
