<template>
  <aside
    v-if="!collapsed"
    class="flex flex-col h-full border-r border-slate-200 bg-gradient-to-b from-slate-50 to-stone-50 transition-all duration-300"
  >
    <div
      class="flex items-center justify-between border-b border-slate-200 bg-slate-50/80 px-6 py-4 flex-shrink-0"
    >
      <div>
        <p class="text-sm font-medium">Explorer</p>
        <p class="text-xs text-muted-foreground">Browse by schema and table</p>
      </div>
      <Button
        variant="ghost"
        size="icon"
        @click="$emit('update:collapsed', true)"
        title="Collapse explorer"
        class="-m-2"
      >
        <ChevronsLeft />
      </Button>
    </div>
    <div class="flex-1 overflow-y-auto min-h-0">
      <ul v-if="tree.length" class="space-y-1 p-2">
        <li v-for="schemaNode in tree" :key="schemaNode.key">
          <ExplorerNode
            :label="schemaNode.name || 'default'"
            icon="schema"
            :expanded="isExpanded(schemaNode.key)"
            @toggle="handleSchemaClick(schemaNode.key)"
            @select="handleSchemaClick(schemaNode.key)"
          >
            <template #default>
              <ul class="space-y-2 pl-3">
                <li v-for="tableNode in schemaNode.tables" :key="tableNode.asset.id">
                  <ExplorerNode
                    :label="
                      tableNode.asset.name ||
                      tableNode.asset.table_facet?.table_name ||
                      'Unnamed table'
                    "
                    icon="table"
                    :expanded="isExpanded(tableNode.key)"
                    :is-selected="selectedAssetId === tableNode.asset.id"
                    @toggle="toggleNode(tableNode.key)"
                    @select="$emit('select-asset', tableNode.asset.id)"
                  >
                    <template #default>
                      <transition-group name="fade" tag="ul" class="space-y-0.5 pl-8 mt-1">
                        <li v-for="columnNode in tableNode.columns" :key="columnNode.asset.id">
                          <ExplorerLeaf
                            :is-selected="selectedAssetId === columnNode.asset.id"
                            :label="
                              columnNode.asset.column_facet?.column_name ||
                              columnNode.asset.name ||
                              'Unnamed column'
                            "
                            type="column"
                            :meta="columnNode.meta"
                            @select="$emit('select-asset', columnNode.asset.id)"
                          />
                        </li>
                      </transition-group>
                    </template>
                  </ExplorerNode>
                </li>
              </ul>
            </template>
          </ExplorerNode>
        </li>
      </ul>
      <div v-else class="flex h-full items-center justify-center p-6 text-sm text-muted-foreground">
        No assets match the current filters.
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import ExplorerLeaf from '@/components/catalog/ExplorerLeaf.vue'
import ExplorerNode from '@/components/catalog/ExplorerNode.vue'
import { Button } from '@/components/ui/button'
import { ChevronsLeft } from 'lucide-vue-next'
import { reactive } from 'vue'
import type { ExplorerSchemaNode } from './types'

interface Props {
  tree: ExplorerSchemaNode[]
  selectedAssetId: string | null
  collapsed: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
  'select-asset': [assetId: string]
  'select-schema': [schemaKey: string]
}>()

const expandedNodes = reactive<Record<string, boolean>>({})

function isExpanded(key: string) {
  return expandedNodes[key] ?? false
}

function toggleNode(key: string) {
  expandedNodes[key] = !expandedNodes[key]
}

function handleSchemaClick(schemaKey: string) {
  // Toggle the clicked schema
  expandedNodes[schemaKey] = !expandedNodes[schemaKey]

  // If expanding, collapse all other schemas
  if (expandedNodes[schemaKey]) {
    Object.keys(expandedNodes).forEach((key) => {
      if (key.startsWith('schema:') && key !== schemaKey) {
        expandedNodes[key] = false
      }
    })
  }

  emit('select-schema', schemaKey)
}

defineExpose({
  expandNode: (key: string) => {
    expandedNodes[key] = true
  },
  collapseNode: (key: string) => {
    expandedNodes[key] = false
  }
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
