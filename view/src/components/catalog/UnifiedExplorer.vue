<template>
  <aside
    v-if="!props.collapsed"
    class="flex flex-col h-full border-r border-border bg-gradient-to-b from-muted/50 to-muted/30 dark:from-muted/20 dark:to-muted/10 transition-all duration-300"
  >
    <!-- Header -->
    <div
      v-if="showHeader"
      class="flex items-center justify-between border-b border-border bg-muted/50 dark:bg-muted/20 px-4 py-3 flex-shrink-0"
    >
      <div>
        <p class="text-sm font-medium">{{ headerTitle }}</p>
        <p class="text-xs text-muted-foreground">{{ headerSubtitle }}</p>
      </div>
      <Button
        v-if="props.showCollapseButton"
        variant="ghost"
        size="icon"
        @click="$emit('update:collapsed', true)"
        title="Collapse explorer"
        class="-m-2"
      >
        <ChevronsLeft class="h-4 w-4" />
      </Button>
    </div>

    <!-- Search Bar -->
    <div v-if="showSearch" class="px-3 py-2 border-b border-border flex-shrink-0 space-y-2">
      <div class="relative">
        <SearchIcon
          class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
        />
        <Input
          :model-value="searchQuery"
          class="pl-9 h-9"
          :placeholder="searchPlaceholder"
          @update:model-value="handleSearchInput"
        />
      </div>
      <label
        v-if="props.showUndocumentedFilter"
        class="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer"
      >
        <Checkbox
          :model-value="showOnlyUndocumented"
          class="cursor-pointer h-3.5 w-3.5"
          @click.stop.prevent="$emit('update:showOnlyUndocumented', !showOnlyUndocumented)"
        />
        <span class="select-none">Show only undocumented</span>
      </label>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto min-h-0">
      <!-- Tree View -->
      <ul v-if="props.tree.length" class="space-y-1 p-2">
        <li v-for="databaseNode in props.tree" :key="databaseNode.key">
          <ExplorerTreeItem
            v-if="databaseNode.asset"
            :label="databaseNode.name"
            icon="database"
            :expanded="isExpanded(databaseNode.key)"
            :is-selected="props.selectedAssetId === databaseNode.asset.id"
            :mode="props.mode"
            :checked="isAssetSelected(databaseNode.asset.id)"
            :disabled="props.disabled"
            :status-info="getAssetStatusInfo(databaseNode.asset)"
            :child-count="getChildCount(databaseNode)"
            :child-type="getChildType(databaseNode)"
            :is-used="isAssetUsed(databaseNode.asset)"
            @toggle="handleDatabaseClick(databaseNode.key)"
            @select="$emit('select-asset', databaseNode.asset.id)"
            @toggle-check="$emit('toggle-asset-selection', databaseNode.asset.id)"
            @quick-action="(action) => $emit('quick-action', action, databaseNode.asset)"
          >
            <template #default>
              <ul class="space-y-1 pl-3">
                <li v-for="schemaNode in databaseNode.schemas" :key="schemaNode.key">
                  <ExplorerTreeItem
                    :label="schemaNode.name || 'default'"
                    icon="schema"
                    :expanded="isExpanded(schemaNode.key)"
                    :is-selected="schemaNode.asset && props.selectedAssetId === schemaNode.asset.id"
                    :mode="props.mode"
                    :checked="isAssetSelected(schemaNode.asset?.id)"
                    :disabled="props.disabled"
                    :status-info="getAssetStatusInfo(schemaNode.asset)"
                    :child-count="getChildCount(schemaNode)"
                    :child-type="getChildType(schemaNode)"
                    :is-used="schemaNode.asset ? isAssetUsed(schemaNode.asset) : false"
                    @toggle="handleSchemaClick(schemaNode.key)"
                    @select="
                      schemaNode.asset
                        ? $emit('select-asset', schemaNode.asset.id)
                        : handleSchemaClick(schemaNode.key)
                    "
                    @toggle-check="
                      schemaNode.asset && $emit('toggle-asset-selection', schemaNode.asset.id)
                    "
                    @quick-action="
                      (action) =>
                        schemaNode.asset && $emit('quick-action', action, schemaNode.asset)
                    "
                  >
                    <template #default>
                      <ul class="space-y-1 pl-3">
                        <li v-for="tableNode in schemaNode.tables" :key="tableNode.asset.id">
                          <ExplorerTreeItem
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
                            :mode="props.mode"
                            :checked="isAssetSelected(tableNode.asset.id)"
                            :disabled="props.disabled"
                            :status-info="getAssetStatusInfo(tableNode.asset)"
                            :child-count="getChildCount(tableNode)"
                            :child-type="getChildType(tableNode)"
                            :is-used="isAssetUsed(tableNode.asset)"
                            :show-quick-actions="props.mode === 'editor'"
                            @toggle="toggleNode(tableNode.key)"
                            @select="$emit('select-asset', tableNode.asset.id)"
                            @toggle-check="$emit('toggle-asset-selection', tableNode.asset.id)"
                            @quick-action="
                              (action) => $emit('quick-action', action, tableNode.asset)
                            "
                          >
                            <template #default>
                              <transition-group name="fade" tag="ul" class="space-y-0.5 pl-6 mt-1">
                                <li
                                  v-for="columnNode in getVisibleColumns(tableNode)"
                                  :key="columnNode.asset.id"
                                >
                                  <ExplorerTreeLeaf
                                    :is-selected="props.selectedAssetId === columnNode.asset.id"
                                    :label="
                                      columnNode.asset.column_facet?.column_name ||
                                      columnNode.asset.name ||
                                      'Unnamed column'
                                    "
                                    :mode="props.mode"
                                    :checked="isAssetSelected(columnNode.asset.id)"
                                    :disabled="props.disabled"
                                    :status-info="getAssetStatusInfo(columnNode.asset)"
                                    @select="$emit('select-asset', columnNode.asset.id)"
                                    @toggle-check="
                                      $emit('toggle-asset-selection', columnNode.asset.id)
                                    "
                                  />
                                </li>
                                <li
                                  v-if="hasMoreColumns(tableNode)"
                                  :key="`more-${tableNode.asset.id}`"
                                  class="text-xs text-muted-foreground italic pl-2"
                                >
                                  + {{ tableNode.columns.length - maxVisibleColumns }} more
                                  columns...
                                </li>
                              </transition-group>
                            </template>
                          </ExplorerTreeItem>
                        </li>
                      </ul>
                    </template>
                  </ExplorerTreeItem>
                </li>
              </ul>
            </template>
          </ExplorerTreeItem>
        </li>
      </ul>

      <!-- Empty State -->
      <div v-else class="flex h-full items-center justify-center p-6 text-sm text-muted-foreground">
        <div class="text-center space-y-2">
          <FolderOpen class="h-8 w-8 mx-auto text-muted-foreground/50" />
          <p>{{ emptyMessage }}</p>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import ExplorerTreeItem from '@/components/catalog/ExplorerTreeItem.vue'
import ExplorerTreeLeaf from '@/components/catalog/ExplorerTreeLeaf.vue'
import { useExplorerState } from '@/components/catalog/useExplorerState'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import type { CatalogAsset } from '@/stores/catalog'
import { ChevronsLeft, FolderOpen, SearchIcon } from 'lucide-vue-next'
import { computed, watch } from 'vue'
import type {
  AssetStatusInfo,
  ExplorerDatabaseNode,
  ExplorerMode,
  ExplorerSchemaNode,
  ExplorerTableNode
} from './types'

interface Props {
  // Data
  tree: ExplorerDatabaseNode[]

  // Mode
  mode?: ExplorerMode

  // Browse mode
  selectedAssetId?: string | null

  // Select mode
  selectedAssetIds?: string[]
  disabled?: boolean

  // Editor mode
  usedAssetIds?: Set<string>

  // Search
  showSearch?: boolean
  searchQuery?: string
  searchPlaceholder?: string
  showUndocumentedFilter?: boolean
  showOnlyUndocumented?: boolean

  // Status display
  showStatusBadge?: boolean

  // Layout
  collapsed?: boolean
  showCollapseButton?: boolean
  showHeader?: boolean
  headerTitle?: string
  headerSubtitle?: string
  emptyMessage?: string

  // Column display limit (for editor mode)
  maxVisibleColumns?: number

  // Auto-expand databases on load
  expandDatabasesByDefault?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'browse',
  selectedAssetId: null,
  selectedAssetIds: () => [],
  disabled: false,
  showSearch: false,
  searchQuery: '',
  searchPlaceholder: 'Search...',
  showUndocumentedFilter: false,
  showOnlyUndocumented: false,
  showStatusBadge: true,
  collapsed: false,
  showCollapseButton: false,
  showHeader: true,
  headerTitle: 'Explorer',
  headerSubtitle: 'Browse by database, schema, and table',
  emptyMessage: 'No assets match the current filters.',
  maxVisibleColumns: 50,
  expandDatabasesByDefault: false
})

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
  'update:searchQuery': [value: string]
  'update:showOnlyUndocumented': [value: boolean]
  'select-asset': [assetId: string]
  'select-database': [databaseKey: string]
  'toggle-asset-selection': [assetId: string]
  'select-all-children': [parentAssetId: string]
  'quick-action': [action: string, asset: CatalogAsset]
}>()

// ============================================
// Expand/Collapse State (shared across all explorer instances)
// ============================================

const {
  isExpanded,
  expandNode,
  collapseNode,
  toggleNode,
  expandNodes,
  hasExplicitState,
  expandedNodes
} = useExplorerState()

// Expand all databases by default when prop is enabled (only if not already set)
function expandAllDatabases() {
  if (!props.expandDatabasesByDefault) return
  const keysToExpand = props.tree.filter((db) => !hasExplicitState(db.key)).map((db) => db.key)
  expandNodes(keysToExpand)
}

// Watch for tree changes to expand new databases
watch(
  () => props.tree,
  () => expandAllDatabases(),
  { immediate: true }
)

function handleDatabaseClick(databaseKey: string) {
  toggleNode(databaseKey)

  // If expanding and not in "expand all" mode, collapse all other databases
  if (isExpanded(databaseKey) && !props.expandDatabasesByDefault) {
    Object.keys(expandedNodes).forEach((key) => {
      if (key.startsWith('database:') && key !== databaseKey) {
        collapseNode(key)
      }
    })
  }

  emit('select-database', databaseKey)
}

function handleSchemaClick(schemaKey: string) {
  toggleNode(schemaKey)
}

// ============================================
// Selection State
// ============================================

function isAssetSelected(assetId: string | undefined): boolean {
  if (!assetId || props.mode !== 'select') return false
  return props.selectedAssetIds.includes(assetId)
}

// ============================================
// Status Display
// ============================================

function getAssetStatusInfo(asset: CatalogAsset | undefined): AssetStatusInfo | undefined {
  if (!asset || !props.showStatusBadge) return undefined

  // AI suggestion takes priority
  if (asset.ai_suggestion || (asset.ai_suggested_tags && asset.ai_suggested_tags.length > 0)) {
    return {
      label: 'AI Suggestion',
      variant: 'ai-suggestion',
      icon: 'sparkles'
    }
  }

  const status = asset.status
  if (status === 'draft') {
    return {
      label: 'Draft',
      variant: 'draft'
    }
  }
  if (status === 'published') {
    return {
      label: 'Published',
      variant: 'published'
    }
  }

  // Only show "Undocumented" in select mode
  if (props.mode === 'select') {
    return {
      label: 'Undocumented',
      variant: 'default'
    }
  }

  return undefined
}

// ============================================
// Editor Mode - Used Assets
// ============================================

function isAssetUsed(asset: CatalogAsset): boolean {
  if (props.mode !== 'editor' || !props.usedAssetIds) return false
  return props.usedAssetIds.has(asset.id)
}

// ============================================
// Tree Helpers
// ============================================

type TreeNode = ExplorerDatabaseNode | ExplorerSchemaNode | ExplorerTableNode

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

// ============================================
// Column Display Limit
// ============================================

const maxVisibleColumns = computed(() => props.maxVisibleColumns)

function getVisibleColumns(tableNode: ExplorerTableNode) {
  return tableNode.columns.slice(0, maxVisibleColumns.value)
}

function hasMoreColumns(tableNode: ExplorerTableNode): boolean {
  return tableNode.columns.length > maxVisibleColumns.value
}

// ============================================
// Search
// ============================================

function handleSearchInput(value: string | number) {
  emit('update:searchQuery', String(value))
}

// ============================================
// Expose methods for parent components
// ============================================

defineExpose({
  expandNode,
  collapseNode,
  isExpanded
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
