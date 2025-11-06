<template>
  <aside
    v-if="!props.collapsed"
    class="flex flex-col h-full border-r border-slate-200 bg-gradient-to-b from-slate-50 to-stone-50 transition-all duration-300"
  >
    <div
      class="flex items-center justify-between border-b border-slate-200 bg-slate-50/80 px-6 py-4 flex-shrink-0"
    >
      <div>
        <p class="text-sm font-medium">Explorer</p>
        <p class="text-xs text-muted-foreground">Browse by database, schema, and table</p>
      </div>
      <Button
        v-if="props.showCollapseButton"
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
      <ul v-if="props.tree.length" class="space-y-1 p-2">
        <li v-for="databaseNode in props.tree" :key="databaseNode.key">
          <ExplorerNode
            v-if="databaseNode.asset"
            :label="databaseNode.name"
            icon="database"
            :expanded="isExpanded(databaseNode.key)"
            :is-selected="props.selectedAssetId === databaseNode.asset.id"
            @toggle="handleDatabaseClick(databaseNode.key)"
            @select="$emit('select-asset', databaseNode.asset.id)"
          >
            <template #default>
              <ul class="space-y-1 pl-3">
                <li v-for="schemaNode in databaseNode.schemas" :key="schemaNode.key">
                  <ExplorerNode
                    :label="schemaNode.name || 'default'"
                    icon="schema"
                    :expanded="isExpanded(schemaNode.key)"
                    :is-selected="schemaNode.asset && props.selectedAssetId === schemaNode.asset.id"
                    @toggle="handleSchemaClick(schemaNode.key)"
                    @select="
                      schemaNode.asset
                        ? $emit('select-asset', schemaNode.asset.id)
                        : handleSchemaClick(schemaNode.key)
                    "
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
                            :icon="
                              tableNode.asset.table_facet?.table_type === 'VIEW' ? 'view' : 'table'
                            "
                            :expanded="isExpanded(tableNode.key)"
                            :is-selected="props.selectedAssetId === tableNode.asset.id"
                            @toggle="toggleNode(tableNode.key)"
                            @select="$emit('select-asset', tableNode.asset.id)"
                          >
                            <template #default>
                              <transition-group name="fade" tag="ul" class="space-y-0.5 pl-8 mt-1">
                                <li
                                  v-for="columnNode in tableNode.columns"
                                  :key="columnNode.asset.id"
                                >
                                  <ExplorerLeaf
                                    :is-selected="props.selectedAssetId === columnNode.asset.id"
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
import type { ExplorerDatabaseNode } from './types'

interface Props {
  tree: ExplorerDatabaseNode[]
  selectedAssetId: string | null
  collapsed: boolean
  showCollapseButton?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
  'select-asset': [assetId: string]
  'select-database': [databaseKey: string]
}>()

const expandedNodes = reactive<Record<string, boolean>>({})

function isExpanded(key: string) {
  return expandedNodes[key] ?? false
}

function toggleNode(key: string) {
  expandedNodes[key] = !expandedNodes[key]
}

function handleDatabaseClick(databaseKey: string) {
  // Toggle the clicked database
  expandedNodes[databaseKey] = !expandedNodes[databaseKey]

  // If expanding, collapse all other databases
  if (expandedNodes[databaseKey]) {
    Object.keys(expandedNodes).forEach((key) => {
      if (key.startsWith('database:') && key !== databaseKey) {
        expandedNodes[key] = false
      }
    })
  }

  emit('select-database', databaseKey)
}

function handleSchemaClick(schemaKey: string) {
  // Toggle the clicked schema
  expandedNodes[schemaKey] = !expandedNodes[schemaKey]
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
