<template>
  <div
    v-if="columns.length"
    class="bg-gradient-to-b from-white to-slate-50/20 divide-y divide-slate-200 shadow-sm"
  >
    <div
      v-for="column in columns"
      :key="column.asset.id"
      :class="[
        'px-4 py-2 transition-colors space-y-3 cursor-pointer',
        column.asset.id === selectedAssetId
          ? 'bg-gradient-to-r from-blue-50 to-slate-50 border-l-2 border-primary-500'
          : 'hover:bg-gradient-to-r hover:from-slate-50 hover:to-stone-50/50'
      ]"
      @click="$emit('select-column', column.asset.id)"
    >
      <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div class="flex-1 min-w-0 space-y-2">
          <div class="flex items-center gap-2">
            <span class="font-medium text-foreground">{{ column.label }}</span>
            <Badge variant="secondary" class="text-xs">{{
              column.asset.column_facet?.data_type || 'N/A'
            }}</Badge>
          </div>
          <p class="text-sm text-muted-foreground leading-6 line-clamp-4">
            {{ column.asset.description || 'No column documentation yet.' }}
          </p>
          <div class="space-y-2">
            <div class="flex flex-wrap gap-2">
              <Badge
                v-for="tag in column.asset.tags"
                :key="tag.id"
                variant="outline"
                class="text-xs"
              >
                {{ tag.name }}
              </Badge>
              <span v-if="!column.asset.tags?.length" class="text-sm text-muted-foreground">
                No tags
              </span>
            </div>
          </div>
        </div>
        <div class="flex-shrink-0">
          <AssetBadgeStatus :status="column.asset.status" badge-class="text-xs" />
        </div>
      </div>
    </div>
  </div>
  <div
    v-else
    class="border border-slate-200 border-dashed bg-gradient-to-br from-slate-50 to-stone-50 p-8 text-center text-sm text-muted-foreground shadow-sm"
  >
    No columns documented for this table yet.
  </div>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import AssetBadgeStatus from '@/components/AssetBadgeStatus.vue'
import type { ExplorerColumnNode } from './types'

interface Props {
  columns: ExplorerColumnNode[]
  selectedAssetId: string | null
}

defineProps<Props>()

defineEmits<{
  'select-column': [columnId: string]
}>()
</script>
