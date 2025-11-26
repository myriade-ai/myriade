<template>
  <div
    v-if="tables.length"
    class="bg-gradient-to-b from-card to-muted/20 divide-y divide-border shadow-sm"
  >
    <div
      v-for="table in tables"
      :key="table.asset.id"
      :class="[
        'px-4 py-2 transition-colors space-y-3 cursor-pointer',
        table.asset.id === selectedAssetId
          ? 'bg-gradient-to-r from-primary-50 to-muted/50 dark:from-primary-900/20 dark:to-muted/20 border-l-2 border-primary-500'
          : 'hover:bg-gradient-to-r hover:from-muted/50 hover:to-muted/30 dark:hover:from-muted/20 dark:hover:to-muted/10'
      ]"
      @click="$emit('select-table', table.asset.id)"
    >
      <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div class="flex-1 min-w-0 space-y-2">
          <div class="flex items-center gap-2">
            <span class="font-medium text-foreground">
              {{ table.asset.name || table.asset.table_facet?.table_name || 'Unnamed table' }}
            </span>
            <Badge variant="secondary" class="text-xs">
              {{ table.asset.table_facet?.table_type || 'TABLE' }}
            </Badge>
            <Badge variant="outline" class="text-xs">
              {{ table.columns.length }} {{ table.columns.length === 1 ? 'column' : 'columns' }}
            </Badge>
          </div>
          <p class="text-sm text-muted-foreground leading-6 line-clamp-4">
            {{ table.asset.description || 'No table documentation yet.' }}
          </p>
          <div class="space-y-2">
            <div class="flex flex-wrap gap-2">
              <Badge
                v-for="tag in table.asset.tags"
                :key="tag.id"
                variant="outline"
                class="text-xs"
              >
                {{ tag.name }}
              </Badge>
              <span v-if="!table.asset.tags?.length" class="text-sm text-muted-foreground">
                No tags
              </span>
            </div>
          </div>
        </div>
        <div class="flex-shrink-0">
          <AssetBadgeStatus :status="table.asset.status" badge-class="text-xs" />
        </div>
      </div>
    </div>
  </div>
  <div
    v-else
    class="border border-border border-dashed bg-gradient-to-br from-muted/50 to-muted/30 dark:from-muted/20 dark:to-muted/10 p-8 text-center text-sm text-muted-foreground shadow-sm"
  >
    No tables documented for this schema yet.
  </div>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import AssetBadgeStatus from '@/components/AssetBadgeStatus.vue'
import type { ExplorerTableNode } from './types'

interface Props {
  tables: ExplorerTableNode[]
  selectedAssetId: string | null
}

defineProps<Props>()

defineEmits<{
  'select-table': [tableId: string]
}>()
</script>
