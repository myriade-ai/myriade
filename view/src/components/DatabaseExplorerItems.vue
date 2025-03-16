<template>
  <div class="block hover:bg-gray-50">
    <!--  @click="onClick" v-on:dblclick="onDblClick" -->
    <div class="px-4 py-4 sm:px-6">
      <div class="flex items-center justify-between">
        <div class="text-sm font-medium truncate text-gray-600">
          {{ props.table.schema }}.{{ props.table.name }}
        </div>
      </div>
      <div class="flex justify-between">
        <div class="sm:flex">
          <div class="flex items-center text-sm text-gray-500">
            {{ table.description }}
          </div>
        </div>
      </div>
      <div v-if="props.showColumns">
        <div v-for="column in table.columns" :key="column.id">
          <div class="mt-2 flex justify-between">
            <div class="sm:flex">
              <div class="flex items-center text-sm text-gray-500">
                {{ column.name }}: {{ column.type }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Table } from '@/stores/tables'
import { defineProps } from 'vue'

const props = defineProps({
  table: {
    type: Object as () => Table,
    required: true
  },
  showColumns: {
    type: Boolean,
    default: false
  }
})
</script>
