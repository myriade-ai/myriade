<template>
  <div class="block hover:bg-gray-50 group" @click="$emit('click')">
    <div class="px-4 py-4 space-y-2">
      <div class="flex items-center justify-between relative">
        <div
          :class="
            cn('text-sm truncate ', {
              'font-medium': props.isUsed
            })
          "
        >
          {{ props.table.schema }}.{{ props.table.name }}
        </div>

        <Button
          @click.stop="$emit('search', table)"
          title="Select all from table"
          variant="ghost"
          class="absolute right-0 opacity-0 group-hover:opacity-100"
          size="sm"
        >
          <Search class="text-gray-600" />
        </Button>
      </div>
      <div v-if="props.showColumns" class="flex justify-between">
        <div class="sm:flex">
          <div class="flex items-center text-sm text-muted-foreground">
            {{ table.description }}
          </div>
        </div>
      </div>
      <div v-if="props.showColumns" class="space-y-1">
        <div v-for="column in table.columns" :key="column.id" class="space-y-1">
          <div class="flex justify-between text-muted-foreground text-sm">
            <span>{{ column.name }}</span>
            <span>{{ column.type }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { cn } from '@/lib/utils'
import type { Table } from '@/stores/tables'
import { defineProps } from 'vue'
import { Search } from 'lucide-vue-next'
import { Button } from './ui/button'

const props = defineProps({
  table: {
    type: Object as () => Table,
    required: true
  },
  showColumns: {
    type: Boolean,
    default: false
  },
  isUsed: {
    type: Boolean,
    default: false
  }
})

defineEmits(['search', 'click'])
</script>
