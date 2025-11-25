<template>
  <aside
    v-if="!props.collapsed"
    class="flex flex-col h-full border-r border-border bg-gradient-to-b from-muted/50 to-muted/30 dark:from-muted/20 dark:to-muted/10 transition-all duration-300"
  >
    <div
      class="flex items-center justify-between border-b border-border bg-muted/50 dark:bg-muted/20 px-6 py-4 flex-shrink-0"
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
            :selection-mode="props.selectionMode"
            :checked="isAssetSelected(databaseNode.asset.id)"
            :disabled="props.disabled"
            :status="getAssetStatus(databaseNode.asset)"
            :child-count="getChildCount(databaseNode)"
            :child-type="getChildType(databaseNode)"
            @toggle="handleDatabaseClick(databaseNode.key)"
            @select="$emit('select-asset', databaseNode.asset.id)"
            @toggle-check="$emit('toggle-asset-selection', databaseNode.asset.id)"
          >
            <template #default>
              <ul class="space-y-1 pl-3">
                <!-- Select all children button -->
                <li
                  v-if="
                    props.selectionMode &&
                    hasDirectChildren(databaseNode) &&
                    getChildCount(databaseNode) > 2
                  "
                >
                  <button
                    type="button"
                    class="text-xs text-muted-foreground hover:text-foreground hover:underline transition-colors"
                    @click="$emit('select-all-children', databaseNode.asset.id)"
                  >
                    {{
                      areAllChildrenSelected(databaseNode)
                        ? 'unselect all children'
                        : 'select all children'
                    }}
                  </button>
                </li>
                <li v-for="schemaNode in databaseNode.schemas" :key="schemaNode.key">
                  <ExplorerNode
                    :label="schemaNode.name || 'default'"
                    icon="schema"
                    :expanded="isExpanded(schemaNode.key)"
                    :is-selected="schemaNode.asset && props.selectedAssetId === schemaNode.asset.id"
                    :selection-mode="props.selectionMode"
                    :checked="isAssetSelected(schemaNode.asset?.id)"
                    :disabled="props.disabled"
                    :status="getAssetStatus(schemaNode.asset)"
                    :child-count="getChildCount(schemaNode)"
                    :child-type="getChildType(schemaNode)"
                    @toggle="handleSchemaClick(schemaNode.key)"
                    @select="
                      schemaNode.asset
                        ? $emit('select-asset', schemaNode.asset.id)
                        : handleSchemaClick(schemaNode.key)
                    "
                    @toggle-check="
                      schemaNode.asset && $emit('toggle-asset-selection', schemaNode.asset.id)
                    "
                  >
                    <template #default>
                      <ul class="space-y-2 pl-3">
                        <!-- Select all children button -->
                        <li
                          v-if="
                            props.selectionMode &&
                            hasDirectChildren(schemaNode) &&
                            getChildCount(schemaNode) > 2
                          "
                        >
                          <button
                            type="button"
                            class="text-xs text-muted-foreground hover:text-foreground hover:underline transition-colors"
                            @click="
                              schemaNode.asset && $emit('select-all-children', schemaNode.asset.id)
                            "
                          >
                            {{
                              areAllChildrenSelected(schemaNode)
                                ? 'unselect all children'
                                : 'select all children'
                            }}
                          </button>
                        </li>
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
                            :selection-mode="props.selectionMode"
                            :checked="isAssetSelected(tableNode.asset.id)"
                            :disabled="props.disabled"
                            :status="getAssetStatus(tableNode.asset)"
                            :child-count="getChildCount(tableNode)"
                            :child-type="getChildType(tableNode)"
                            @toggle="toggleNode(tableNode.key)"
                            @select="$emit('select-asset', tableNode.asset.id)"
                            @toggle-check="$emit('toggle-asset-selection', tableNode.asset.id)"
                          >
                            <template #default>
                              <transition-group name="fade" tag="ul" class="space-y-0.5 pl-8 mt-1">
                                <!-- Select all children button -->
                                <li
                                  v-if="
                                    props.selectionMode &&
                                    hasDirectChildren(tableNode) &&
                                    getChildCount(tableNode) > 2
                                  "
                                  :key="`select-all-${tableNode.asset.id}`"
                                >
                                  <button
                                    type="button"
                                    class="text-xs text-muted-foreground hover:text-foreground hover:underline transition-colors"
                                    @click="$emit('select-all-children', tableNode.asset.id)"
                                  >
                                    {{
                                      areAllChildrenSelected(tableNode)
                                        ? 'unselect all children'
                                        : 'select all children'
                                    }}
                                  </button>
                                </li>
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
                                    :selection-mode="props.selectionMode"
                                    :checked="isAssetSelected(columnNode.asset.id)"
                                    :disabled="props.disabled"
                                    :status="getAssetStatus(columnNode.asset)"
                                    @select="$emit('select-asset', columnNode.asset.id)"
                                    @toggle-check="
                                      $emit('toggle-asset-selection', columnNode.asset.id)
                                    "
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
import type { CatalogAsset } from '@/stores/catalog'
import { ChevronsLeft } from 'lucide-vue-next'
import { reactive } from 'vue'
import type { ExplorerDatabaseNode, ExplorerSchemaNode, ExplorerTableNode } from './types'

interface Props {
  tree: ExplorerDatabaseNode[]
  selectedAssetId: string | null
  collapsed: boolean
  showCollapseButton?: boolean
  selectionMode?: boolean
  selectedAssetIds?: string[]
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  selectionMode: false,
  selectedAssetIds: () => [],
  disabled: false
})

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
  'select-asset': [assetId: string]
  'select-database': [databaseKey: string]
  'toggle-asset-selection': [assetId: string]
  'select-all-children': [parentAssetId: string]
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

function isAssetSelected(assetId: string | undefined): boolean {
  if (!assetId || !props.selectionMode) return false
  return props.selectedAssetIds.includes(assetId)
}

function getAssetStatus(asset: CatalogAsset | undefined): string | undefined {
  if (!asset) return undefined
  const status = asset.status
  if (status === 'draft') return 'Draft'
  if (status === 'published') return 'Published'
  return undefined // null = unverified
}

type TreeNode = ExplorerDatabaseNode | ExplorerSchemaNode | ExplorerTableNode

function hasDirectChildren(node: TreeNode): boolean {
  if ('schemas' in node && node.schemas?.length) return true
  if ('tables' in node && node.tables?.length) return true
  if ('columns' in node && node.columns?.length) return true
  return false
}

function getChildCount(node: TreeNode): number {
  if ('schemas' in node && node.schemas?.length) return node.schemas.length
  if ('tables' in node && node.tables?.length) return node.tables.length
  if ('columns' in node && node.columns?.length) return node.columns.length
  return 0
}

function getChildType(node: TreeNode): string {
  if ('schemas' in node && node.schemas?.length) {
    return node.schemas.length === 1 ? 'schema' : 'schemas'
  }
  if ('tables' in node && node.tables?.length) {
    return node.tables.length === 1 ? 'table' : 'tables'
  }
  if ('columns' in node && node.columns?.length) {
    return node.columns.length === 1 ? 'column' : 'columns'
  }
  return ''
}

function collectChildIds(node: TreeNode): string[] {
  const ids: string[] = []
  if ('schemas' in node && node.schemas?.length) {
    node.schemas.forEach((s) => {
      if (s.asset?.id) ids.push(s.asset.id)
    })
  } else if ('tables' in node && node.tables?.length) {
    node.tables.forEach((t) => ids.push(t.asset.id))
  } else if ('columns' in node && node.columns?.length) {
    node.columns.forEach((c) => ids.push(c.asset.id))
  }
  return ids
}

function areAllChildrenSelected(node: TreeNode): boolean {
  if (!props.selectionMode) return false
  const childIds = collectChildIds(node)
  if (childIds.length === 0) return false
  return childIds.every((id) => props.selectedAssetIds.includes(id))
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
