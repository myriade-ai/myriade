<template>
  <div
    v-if="schemas.length"
    class="bg-gradient-to-b from-card to-muted/20 divide-y divide-border shadow-sm"
  >
    <div
      v-for="schema in schemas"
      :key="schema.key"
      :class="[
        'px-4 py-2 transition-colors space-y-3 cursor-pointer',
        schema.asset && schema.asset.id === selectedAssetId
          ? 'bg-gradient-to-r from-primary-50 to-muted/50 dark:from-primary-900/20 dark:to-muted/20 border-l-2 border-primary-500'
          : 'hover:bg-gradient-to-r hover:from-muted/50 hover:to-muted/30 dark:hover:from-muted/20 dark:hover:to-muted/10'
      ]"
      @click="schema.asset && $emit('select-schema', schema.asset.id)"
    >
      <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div class="flex-1 min-w-0 space-y-2">
          <div class="flex items-center gap-2">
            <span class="font-medium text-foreground">{{ schema.name || 'default' }}</span>
            <Badge variant="secondary" class="text-xs">
              {{ schema.tables.length }} {{ schema.tables.length === 1 ? 'table' : 'tables' }}
            </Badge>
          </div>
          <p v-if="schema.asset" class="text-sm text-muted-foreground leading-6 line-clamp-4">
            {{ schema.asset.description || 'No schema documentation yet.' }}
          </p>
          <div v-if="schema.asset" class="space-y-2">
            <div class="flex flex-wrap gap-2">
              <Badge
                v-for="tag in schema.asset.tags"
                :key="tag.id"
                variant="outline"
                class="text-xs"
              >
                {{ tag.name }}
              </Badge>
              <span v-if="!schema.asset.tags?.length" class="text-sm text-muted-foreground">
                No tags
              </span>
            </div>
          </div>
        </div>
        <div v-if="schema.asset" class="flex-shrink-0">
          <AssetBadgeStatus :status="schema.asset.status" badge-class="text-xs" />
        </div>
      </div>
    </div>
  </div>
  <div
    v-else
    class="border border-border border-dashed bg-gradient-to-br from-muted/50 to-muted/30 dark:from-muted/20 dark:to-muted/10 p-8 text-center text-sm text-muted-foreground shadow-sm"
  >
    No schemas documented for this database yet.
  </div>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import AssetBadgeStatus from '@/components/AssetBadgeStatus.vue'
import type { ExplorerSchemaNode } from './types'

interface Props {
  schemas: ExplorerSchemaNode[]
  selectedAssetId: string | null
}

defineProps<Props>()

defineEmits<{
  'select-schema': [schemaId: string]
}>()
</script>
