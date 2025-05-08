<template>
  <div class="flex mt-0" style="margin-top: -40px">
    <button
      class="clipboard ml-auto border border-transparent text-sm font-medium rounded-md shadow-xs text-black mt-1 px-2 py-1 bg-gray-100 hover:bg-gray-300 focus:outline-hidden focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      @click="copyToClipboard"
    >
      {{ copyText }}
    </button>
  </div>
  <div ref="table"></div>
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
  tabulator.value.copyToClipboard('all')
  copyText.value = 'copied'
  setTimeout(() => {
    copyText.value = 'copy'
  }, 1000)
}

watch(
  props,
  () => {
    tabulator.value.setData(hideEncryptedFields(props.data))
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
    paginationCounter: (pageSize, currentRow) => {
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
.clipboard {
  top: 48px;
  position: relative;
  background-color: #ccc;
  z-index: 100;
  right: 10px;
}
</style>
