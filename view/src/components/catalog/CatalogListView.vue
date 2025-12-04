<template>
  <div ref="scrollElement" class="flex-1 overflow-y-auto bg-background">
    <div v-if="!assets.length" class="p-12 text-center">
      <p class="text-muted-foreground">No assets found matching the current filters.</p>
    </div>

    <div
      v-else
      :style="{
        height: `${virtualizer.getTotalSize()}px`,
        width: '100%',
        position: 'relative'
      }"
    >
      <div
        v-for="virtualRow in virtualizer.getVirtualItems()"
        :key="String(virtualRow.key)"
        :data-index="virtualRow.index"
        :ref="(el) => measureElement(el)"
        class="px-4 py-3 cursor-pointer bg-card/50 backdrop-blur-sm border-b border-border hover:bg-muted/70 transition-all duration-200 hover:shadow-sm"
        :style="{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          transform: `translateY(${virtualRow.start}px)`
        }"
        @click="$emit('select-asset', assets[virtualRow.index].id)"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-3 flex-1 min-w-0">
            <component
              :is="getAssetIcon(assets[virtualRow.index])"
              class="h-5 w-5 text-primary-600 flex-shrink-0"
            />
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <h3 class="font-medium truncate">
                  {{ getAssetTitle(assets[virtualRow.index]) }}
                </h3>
                <!-- AI Suggestion Indicator -->
                <Tooltip v-if="hasAiSuggestion(assets[virtualRow.index])">
                  <TooltipTrigger as-child>
                    <span
                      class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-[var(--gold)]/10 text-[var(--gold)]"
                    >
                      <Sparkles class="h-3 w-3" />
                      <span class="hidden sm:inline">AI</span>
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Has AI suggestions to review</p>
                  </TooltipContent>
                </Tooltip>
              </div>
              <p class="text-sm text-muted-foreground truncate mt-1">
                {{ getAssetMetadata(assets[virtualRow.index]) }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-2 flex-shrink-0 ml-4">
            <AssetBadgeStatus
              :status="assets[virtualRow.index].status"
              :published-by="assets[virtualRow.index].published_by"
              :published-at="assets[virtualRow.index].published_at"
              badge-class="text-xs"
            />
          </div>
        </div>
        <!-- AI Suggestion Preview (if exists and no regular description) -->
        <div
          v-if="assets[virtualRow.index].ai_suggestion && !assets[virtualRow.index].description"
          class="mt-2 text-sm text-[var(--gold)] line-clamp-2 flex items-start gap-1.5"
        >
          <Sparkles class="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
          <MarkdownDisplay
            :content="assets[virtualRow.index].ai_suggestion ?? ''"
            class="italic flex-1"
          />
        </div>
        <!-- Regular Description -->
        <div
          v-else-if="assets[virtualRow.index].description"
          class="mt-2 text-sm text-muted-foreground line-clamp-2"
        >
          <MarkdownDisplay :content="assets[virtualRow.index].description ?? ''" />
        </div>
        <!-- Tags and AI Suggested Tags -->
        <div
          v-if="
            assets[virtualRow.index].tags?.length ||
            assets[virtualRow.index].ai_suggested_tags?.length
          "
          class="mt-2 flex flex-wrap gap-2"
        >
          <Badge
            v-for="tag in assets[virtualRow.index].tags"
            :key="tag.id"
            variant="secondary"
            class="text-xs"
          >
            {{ tag.name }}
          </Badge>
          <!-- AI Suggested Tags Preview -->
          <Badge
            v-for="tagName in assets[virtualRow.index].ai_suggested_tags?.slice(0, 3)"
            :key="tagName"
            variant="outline"
            class="text-xs border-[var(--gold)]/30 text-[var(--gold)] border-dashed"
          >
            <Sparkles class="h-2.5 w-2.5 mr-1" />
            {{ tagName }}
          </Badge>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import AssetBadgeStatus from '@/components/AssetBadgeStatus.vue'
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'
import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import type { CatalogAsset } from '@/stores/catalog'
import { useVirtualizer } from '@tanstack/vue-virtual'
import {
  Columns3,
  Database,
  FolderTree,
  Sparkles,
  Table as TableIcon,
  View as ViewIcon
} from 'lucide-vue-next'
import { computed, ref, watch, type Component, type ComponentPublicInstance } from 'vue'

interface Props {
  assets: CatalogAsset[]
  getColumnCount: (tableId: string) => number
}

const props = defineProps<Props>()

// Helper to check if asset has any AI suggestions
function hasAiSuggestion(asset: CatalogAsset): boolean {
  return Boolean(
    asset.ai_suggestion || (asset.ai_suggested_tags && asset.ai_suggested_tags.length > 0)
  )
}

defineEmits<{
  'select-asset': [assetId: string]
}>()

const scrollElement = ref<HTMLElement | null>(null)

// Helper functions for asset display
function getAssetIcon(asset: CatalogAsset): Component {
  if (asset.type === 'DATABASE') return Database
  if (asset.type === 'SCHEMA') return FolderTree
  if (asset.type === 'TABLE') {
    return asset.table_facet?.table_type === 'VIEW' ? ViewIcon : TableIcon
  }
  if (asset.type === 'COLUMN') return Columns3
  return TableIcon // fallback
}

function getAssetTitle(asset: CatalogAsset): string {
  if (asset.type === 'DATABASE') {
    return asset.database_facet?.database_name || asset.name || 'Unnamed database'
  }
  if (asset.type === 'SCHEMA') {
    return asset.schema_facet?.schema_name || asset.name || 'Unnamed schema'
  }
  if (asset.type === 'TABLE') {
    return asset.table_facet?.table_name || asset.name || 'Unnamed table'
  }
  if (asset.type === 'COLUMN') {
    return asset.column_facet?.column_name || asset.name || 'Unnamed column'
  }
  return asset.name || 'Unnamed asset'
}

function getAssetMetadata(asset: CatalogAsset): string {
  if (asset.type === 'DATABASE') {
    return 'Database'
  }
  if (asset.type === 'SCHEMA') {
    const dbName = asset.schema_facet?.database_name || 'unknown'
    return `Schema in ${dbName}`
  }
  if (asset.type === 'TABLE') {
    const database = asset.table_facet?.database_name || ''
    const schema = asset.table_facet?.schema || 'default'
    const tableName = asset.table_facet?.table_name || asset.name || 'unknown'
    const columnCount = props.getColumnCount(asset.id)
    const fullPath = database ? `${database}.${schema}.${tableName}` : `${schema}.${tableName}`
    return `${fullPath} · ${columnCount} columns`
  }
  if (asset.type === 'COLUMN') {
    const dataType = asset.column_facet?.data_type || 'unknown'
    // Get parent table info if available
    const parentDatabase = asset.column_facet?.parent_table_facet?.database_name || ''
    const parentSchema = asset.column_facet?.parent_table_facet?.schema || ''
    const parentTable = asset.column_facet?.parent_table_facet?.table_name || ''
    if (parentSchema && parentTable) {
      const fullPath = parentDatabase
        ? `${parentDatabase}.${parentSchema}.${parentTable}`
        : `${parentSchema}.${parentTable}`
      return `${fullPath} · ${dataType}`
    }
    return dataType
  }
  return asset.type
}

// Set up virtualizer with dynamic measurement
const virtualizer = useVirtualizer(
  computed(() => ({
    count: props.assets.length,
    getScrollElement: () => scrollElement.value,
    estimateSize: () => 100, // Initial estimate - will be measured dynamically
    overscan: 5 // Number of items to render outside visible area
  }))
)

// Helper to measure element, handling Vue component instances
function measureElement(el: Element | ComponentPublicInstance | null) {
  if (!el) return
  const element = el instanceof Element ? el : (el.$el as Element)
  virtualizer.value.measureElement(element)
}

// Reset scroll position only when asset count changes (filtering), not on updates
watch(
  () => props.assets.length,
  () => {
    virtualizer.value.scrollToIndex(0, { align: 'start' })
  }
)
</script>
