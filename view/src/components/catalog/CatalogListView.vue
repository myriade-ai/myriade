<template>
  <div class="flex-1 overflow-y-auto bg-gradient-to-b from-slate-50/30 to-stone-50/30">
    <div>
      <div class="bg-white/50 backdrop-blur-sm divide-y divide-slate-200">
        <div
          v-for="table in tables"
          :key="table.id"
          class="px-4 py-3 cursor-pointer hover:bg-gradient-to-r hover:from-slate-50 hover:via-white hover:to-stone-50 transition-all duration-200 hover:shadow-sm"
          @click="$emit('select-table', table.id)"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3 flex-1 min-w-0">
              <component :is="TableIcon" class="h-5 w-5 text-primary-600 flex-shrink-0" />
              <div class="flex-1 min-w-0">
                <h3 class="font-medium truncate">
                  {{ table.name || table.table_facet?.table_name || 'Unnamed table' }}
                </h3>
                <p class="text-sm text-muted-foreground truncate">
                  {{ table.table_facet?.schema || 'default' }}.{{ table.table_facet?.table_name }}
                </p>
              </div>
            </div>
            <div class="flex items-center gap-4 flex-shrink-0 ml-4">
              <span class="text-sm text-muted-foreground whitespace-nowrap"
                >{{ getColumnCount(table.id) }} columns</span
              >
            </div>
          </div>
          <p v-if="table.description" class="mt-2 text-sm text-muted-foreground line-clamp-2">
            {{ table.description }}
          </p>
          <div v-if="table.tags?.length" class="mt-2 flex flex-wrap gap-2">
            <Badge v-for="tag in table.tags" :key="tag.id" variant="secondary" class="text-xs">
              {{ tag.name }}
            </Badge>
          </div>
        </div>
      </div>

      <div
        v-if="!tables.length"
        class="border-b border-slate-200 bg-gradient-to-br from-slate-50 to-stone-50 p-12 text-center"
      >
        <p class="text-muted-foreground">No tables found matching the current filters.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import type { CatalogAsset } from '@/stores/catalog'
import { Table as TableIcon } from 'lucide-vue-next'

interface Props {
  tables: CatalogAsset[]
  getColumnCount: (tableId: string) => number
}

defineProps<Props>()

defineEmits<{
  'select-table': [tableId: string]
}>()
</script>
