<template>
  <div
    ref="scrollElement"
    class="flex-1 overflow-y-auto bg-gradient-to-b from-slate-50/30 to-stone-50/30"
  >
    <div v-if="!tables.length" class="p-12 text-center">
      <p class="text-muted-foreground">No tables found matching the current filters.</p>
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
        class="px-4 py-3 cursor-pointer bg-white/50 backdrop-blur-sm border-b border-slate-200 hover:bg-gradient-to-r hover:from-slate-50 hover:via-white hover:to-stone-50 transition-all duration-200 hover:shadow-sm"
        :style="{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          transform: `translateY(${virtualRow.start}px)`
        }"
        @click="$emit('select-table', tables[virtualRow.index].id)"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-3 flex-1 min-w-0">
            <component :is="TableIcon" class="h-5 w-5 text-primary-600 flex-shrink-0" />
            <div class="flex-1 min-w-0">
              <h3 class="font-medium truncate">
                {{
                  tables[virtualRow.index].name ||
                  tables[virtualRow.index].table_facet?.table_name ||
                  'Unnamed table'
                }}
              </h3>
              <div class="flex items-center gap-2 mt-1">
                <span class="text-sm text-muted-foreground whitespace-nowrap"
                  >{{ getColumnCount(tables[virtualRow.index].id) }} columns</span
                >
                <span class="text-muted-foreground">·</span>
                <p class="text-sm text-muted-foreground truncate">
                  {{ tables[virtualRow.index].table_facet?.schema || 'default' }}.{{
                    tables[virtualRow.index].table_facet?.table_name
                  }}
                </p>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-2 flex-shrink-0 ml-4">
            <AssetBadgeStatus :status="tables[virtualRow.index].status" badge-class="text-xs" />
          </div>
        </div>
        <p
          v-if="tables[virtualRow.index].description"
          class="mt-2 text-sm text-muted-foreground line-clamp-2"
        >
          {{ tables[virtualRow.index].description }}
        </p>
        <div v-if="tables[virtualRow.index].tags?.length" class="mt-2 flex flex-wrap gap-2">
          <Badge
            v-for="tag in tables[virtualRow.index].tags"
            :key="tag.id"
            variant="secondary"
            class="text-xs"
          >
            {{ tag.name }}
          </Badge>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import AssetBadgeStatus from '@/components/AssetBadgeStatus.vue'
import { Badge } from '@/components/ui/badge'
import type { CatalogAsset } from '@/stores/catalog'
import { useVirtualizer } from '@tanstack/vue-virtual'
import { Table as TableIcon } from 'lucide-vue-next'
import { computed, ref, watch, type ComponentPublicInstance } from 'vue'

interface Props {
  tables: CatalogAsset[]
  getColumnCount: (tableId: string) => number
}

const props = defineProps<Props>()

defineEmits<{
  'select-table': [tableId: string]
}>()

const scrollElement = ref<HTMLElement | null>(null)

// Set up virtualizer with dynamic measurement
const virtualizer = useVirtualizer(
  computed(() => ({
    count: props.tables.length,
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

// Reset scroll position only when table count changes (filtering), not on updates
watch(
  () => props.tables.length,
  () => {
    virtualizer.value.scrollToIndex(0, { align: 'start' })
  }
)
</script>
