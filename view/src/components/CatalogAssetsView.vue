<template>
  <div class="flex h-full w-full">
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center h-full w-full">
      <LoaderIcon />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8 flex-shrink-0 w-full">
      <p class="text-red-600 mb-4">{{ error }}</p>
      <Button @click="refresh" variant="outline">Retry</Button>
    </div>

    <!-- Main Content -->
    <template v-else>
      <ResizablePanelGroup direction="horizontal" class="h-full w-full">
        <!-- Explorer Panel -->
        <ResizablePanel
          v-if="!isMobile && !explorerCollapsed"
          :default-size="25"
          :min-size="15"
          :max-size="40"
          :collapsible="false"
        >
          <CatalogExplorer
            ref="desktopExplorerRef"
            v-model:collapsed="explorerCollapsed"
            :tree="filteredTree"
            :selected-asset-id="selectedAssetId"
            :show-collapse-button="!isMobile"
            @select-asset="handleSelectAsset"
          />
        </ResizablePanel>

        <!-- Resizable Handle -->
        <ResizableHandle v-if="!isMobile && !explorerCollapsed" />

        <!-- Right side - Content and Filters Panel -->
        <ResizablePanel :default-size="explorerCollapsed ? 100 : 75">
          <div class="flex flex-1 flex-col min-h-0 h-full">
            <!-- Filters Bar -->
            <CatalogFilters
              v-model:search-query="searchQueryInput"
              v-model:selected-database="selectedDatabase"
              v-model:selected-schema="selectedSchema"
              v-model:selected-tag="selectedTag"
              v-model:selected-status="selectedStatus"
              :database-options="databaseOptions"
              :schema-options="schemaOptions"
              :tag-options="tagOptions"
              :has-active-filters="hasActiveFilters"
              :explorer-collapsed="explorerCollapsed"
              :show-explorer-shortcut="isMobile"
              :is-searching="isSearching"
              @clear-filters="clearFilters"
              @toggle-explorer="openExplorer"
              @open-explorer="openExplorer"
            />

            <!-- Details View (when asset selected) -->
            <CatalogDetailsView
              v-if="selectedAsset"
              v-model:active-tab="activeTab"
              :asset="selectedAsset"
              :columns="columnsForSelectedTable"
              :schemas="schemasForSelectedDatabase"
              :tables="tablesForSelectedSchema"
              :draft="assetDraft"
              :is-editing="assetEditing"
              :is-saving="assetSaving"
              :has-changes="assetHasChanges"
              :error="assetEditError"
              @select-column="handleSelectAsset"
              @select-schema="handleSelectAsset"
              @select-table="handleSelectAsset"
              @start-edit="startAssetEdit"
              @cancel-edit="cancelAssetEdit"
              @save="saveAssetDetails"
              @update:draft="updateAssetDraft"
              @dismiss-flag="dismissAssetFlag"
              @approve-suggestion="approveAssetSuggestion"
            />

            <!-- List View (no asset selected) -->
            <CatalogListView
              v-else
              :assets="filteredAssets"
              :get-column-count="getTableColumnCount"
              @select-asset="handleSelectAsset"
            />
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </template>

    <Sheet v-if="isMobile" :open="showExplorerSheet" @update:open="setExplorerSheetOpen">
      <SheetContent side="left" class="flex h-full w-full max-w-sm flex-col p-0 sm:max-w-md">
        <SheetHeader class="sr-only">
          <SheetTitle>Catalog explorer</SheetTitle>
          <SheetDescription>Browse by schema and table.</SheetDescription>
        </SheetHeader>
        <CatalogExplorer
          ref="mobileExplorerRef"
          :tree="filteredTree"
          :selected-asset-id="selectedAssetId"
          :collapsed="false"
          :show-collapse-button="false"
          @select-asset="handleSelectAsset"
        />
      </SheetContent>
    </Sheet>
  </div>
</template>

<script setup lang="ts">
import CatalogDetailsView from '@/components/catalog/CatalogDetailsView.vue'
import CatalogExplorer from '@/components/catalog/CatalogExplorer.vue'
import CatalogFilters from '@/components/catalog/CatalogFilters.vue'
import CatalogListView from '@/components/catalog/CatalogListView.vue'
import LoaderIcon from '@/components/icons/LoaderIcon.vue'
import { Button } from '@/components/ui/button'
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle
} from '@/components/ui/sheet'
import type { CatalogAsset } from '@/stores/catalog'
import { useCatalogStore } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import type { CatalogAssetUpdatePayload } from '@/types/catalog'
import { useQueryClient } from '@tanstack/vue-query'
import { useMediaQuery } from '@vueuse/core'
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { EditableDraft } from './catalog/types'
import { useCatalogData } from './catalog/useCatalogData'
import { useCatalogAssetsQuery, useCatalogSearchQuery } from './catalog/useCatalogQuery'
import { debounce } from '@/utils/debounce'

interface Props {
  isLoading?: boolean
  isFetching?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  isFetching: false
})

const catalogStore = useCatalogStore()
const contextsStore = useContextsStore()
const queryClient = useQueryClient()

// Use TanStack Query as the data source
const { data: assetsData, isLoading: queryLoading, error: queryError } = useCatalogAssetsQuery()

const loading = computed(() => {
  if (props.isLoading !== undefined) {
    // Show loading only if we're loading AND we have no data yet
    return props.isLoading && (!assetsData.value || assetsData.value.length === 0)
  }
  return queryLoading.value && (!assetsData.value || assetsData.value.length === 0)
})

const error = computed(() => queryError.value?.message || catalogStore.error)

// State
const searchQueryInput = ref('')
const searchQuery = ref('')
const selectedDatabase = ref('__all__')
const selectedSchema = ref('__all__')
const selectedTag = ref('__all__')
const selectedStatus = ref('__all__')
const activeTab = ref<'overview' | 'columns' | 'schemas' | 'tables' | 'preview' | 'sources'>(
  'overview'
)
const isMobile = useMediaQuery('(max-width: 1023px)')
const selectedAssetId = ref<string | null>(null)
const explorerCollapsed = ref(false)
type ExplorerInstance = InstanceType<typeof CatalogExplorer>
const desktopExplorerRef = ref<ExplorerInstance | null>(null)
const mobileExplorerRef = ref<ExplorerInstance | null>(null)
const showExplorerSheet = ref(false)
const hasAutoSelected = ref(false)

// Debounced search handler
const debouncedUpdateSearch = debounce((query: string) => {
  searchQuery.value = query
}, 500)

// Watch for input changes and debounce
watch(searchQueryInput, (newValue) => {
  debouncedUpdateSearch(newValue)
})

// Asset editing state (used for both tables and columns)
const assetEditing = ref(false)
const assetSaving = ref(false)
const assetEditError = ref<string | null>(null)
const assetDraft = reactive<EditableDraft>({
  description: '',
  tags: []
})

const route = useRoute()
const router = useRouter()

// Use catalog data composable with TanStack Query as the source
const catalogData = useCatalogData(computed(() => assetsData.value))
const {
  tableById,
  columnsByTableId,
  databaseOptions,
  schemaOptions,
  tagOptions,
  buildFilteredTree,
  assetMatchesFilters,
  indexes
} = catalogData

const selectedDatabaseId = computed<string>(() => {
  return contextsStore.getSelectedContextDatabaseId()
})

// Server-side search (always enabled when filters are active)
const searchEnabled = computed(() => {
  return (
    !!selectedDatabaseId.value &&
    (searchQuery.value.length > 0 ||
      selectedTag.value !== '__all__' ||
      selectedStatus.value !== '__all__')
  )
})

const { data: searchResultIds, isFetching: isSearching } = useCatalogSearchQuery(
  selectedDatabaseId,
  searchQuery,
  searchEnabled,
  selectedTag,
  selectedStatus
)

const matchingIds = computed(() => {
  if (searchResultIds.value && searchEnabled.value) {
    return new Set(searchResultIds.value)
  }
  return null
})

// Create order map for search results to preserve backend sorting
const searchResultOrderMap = computed(() => {
  if (!searchResultIds.value || !searchEnabled.value) return null

  const orderMap = new Map<string, number>()
  searchResultIds.value.forEach((id, index) => {
    orderMap.set(id, index)
  })
  return orderMap
})

// Computed
const hasActiveFilters = computed(() =>
  Boolean(
    searchQuery.value.trim() ||
      (selectedDatabase.value && selectedDatabase.value !== '__all__') ||
      (selectedSchema.value && selectedSchema.value !== '__all__') ||
      (selectedTag.value && selectedTag.value !== '__all__') ||
      (selectedStatus.value && selectedStatus.value !== '__all__')
  )
)

const filteredTree = computed(() =>
  buildFilteredTree({
    selectedDatabase: selectedDatabase.value,
    selectedSchema: selectedSchema.value,
    matchingIds: matchingIds.value
  })
)

const selectedAsset = computed(() => {
  if (!selectedAssetId.value) return null
  return indexes.assetsByIdMap.value.get(selectedAssetId.value) ?? null
})

const selectedTable = computed(() => {
  const asset = selectedAsset.value
  if (!asset) return null
  if (asset.type === 'TABLE') return asset
  if (asset.type === 'COLUMN') {
    const tableId = asset.column_facet?.parent_table_asset_id
    if (!tableId) return null
    return indexes.tablesByIdMap.value.get(tableId) ?? null
  }
  return null
})

const columnsForSelectedTable = computed(() => {
  if (!selectedTable.value) return []
  const tableColumns = columnsByTableId.value.get(selectedTable.value.id) || []
  return tableColumns.map((column) => ({
    asset: column,
    label: column.column_facet?.column_name || column.name || 'Unnamed column',
    meta: column.column_facet?.data_type || ''
  }))
})

const schemasForSelectedDatabase = computed(() => {
  const asset = selectedAsset.value
  if (!asset || asset.type !== 'DATABASE') return []

  // Find the database node in the filtered tree
  const databaseNode = filteredTree.value.find((db) => db.asset?.id === asset.id)
  return databaseNode?.schemas || []
})

const tablesForSelectedSchema = computed(() => {
  const asset = selectedAsset.value
  if (!asset || asset.type !== 'SCHEMA') return []

  // Find the schema node in the filtered tree
  for (const dbNode of filteredTree.value) {
    if (!dbNode.schemas) continue
    const schemaNode = dbNode.schemas.find((s) => s.asset?.id === asset.id)
    if (schemaNode) {
      return schemaNode.tables || []
    }
  }
  return []
})

const assetHasChanges = computed(() => {
  const asset = selectedAsset.value
  if (!asset) return false

  // If there's an AI suggestion, always show changes (needs approval)
  if (asset.ai_suggestion) {
    return true
  }

  const currentDescription = (asset.description ?? '').trim()
  const draftDescription = assetDraft.description.trim()

  if (currentDescription !== draftDescription) {
    return true
  }

  const currentTagIds = [...(asset.tags || [])].map((tag) => tag.id).sort()
  const draftTagIds = [...assetDraft.tags].map((tag) => tag.id).sort()

  if (currentTagIds.length !== draftTagIds.length) {
    return true
  }

  return currentTagIds.some((id, index) => id !== draftTagIds[index])
})

// Compute filtered assets (all types, not just tables) for stats
const filteredAssets = computed(() => {
  if (!assetsData.value) return []

  const filtered = assetsData.value.filter((asset) =>
    assetMatchesFilters(asset, {
      selectedDatabase: selectedDatabase.value,
      selectedSchema: selectedSchema.value,
      matchingIds: matchingIds.value
    })
  )

  // Sort by backend search order if available
  if (searchResultOrderMap.value) {
    return filtered.slice().sort((a, b) => {
      const orderA = searchResultOrderMap.value!.get(a.id) ?? Number.MAX_SAFE_INTEGER
      const orderB = searchResultOrderMap.value!.get(b.id) ?? Number.MAX_SAFE_INTEGER
      return orderA - orderB
    })
  }

  return filtered
})

// Route sync
const routeAssetId = computed(() => {
  const queryParam = route.query.assetId
  if (Array.isArray(queryParam)) {
    return queryParam[0] ?? null
  }
  return typeof queryParam === 'string' && queryParam.trim().length > 0 ? queryParam : null
})

watch(
  routeAssetId,
  (assetId) => {
    if (!assetId) return
    selectedAssetId.value = assetId
    nextTick(() => expandForAsset(assetId))
  },
  { immediate: true }
)

watch(selectedAssetId, (assetId) => {
  activeTab.value = 'overview'
  const current = routeAssetId.value
  if (assetId === current) return
  const query = { ...route.query }
  if (assetId) {
    query.assetId = assetId
  } else {
    delete query.assetId
  }
  router.replace({ query }).catch(() => {})
})

watch(
  () => contextsStore.contextSelected,
  (newContext, oldContext) => {
    if (newContext?.id !== oldContext?.id) {
      searchQueryInput.value = ''
      searchQuery.value = ''
      selectedSchema.value = '__all__'
      selectedTag.value = '__all__'
      selectedStatus.value = '__all__'
      selectedAssetId.value = null
      hasAutoSelected.value = false // Reset flag to allow auto-selection in new context
    }
  }
)

watch(
  isMobile,
  (mobile) => {
    if (mobile) {
      explorerCollapsed.value = true
    } else {
      explorerCollapsed.value = false
      showExplorerSheet.value = false
      if (selectedAssetId.value) {
        nextTick(() => expandForAsset(selectedAssetId.value!))
      }
    }
  },
  { immediate: true }
)

watch(desktopExplorerRef, (instance) => {
  if (instance && !isMobile.value && selectedAssetId.value) {
    nextTick(() => expandForAsset(selectedAssetId.value!))
  }
})

watch(showExplorerSheet, (open) => {
  if (open && selectedAssetId.value) {
    nextTick(() => expandForAsset(selectedAssetId.value!))
  }
})

watch(
  selectedAsset,
  (asset) => {
    assetEditError.value = null
    assetSaving.value = false

    if (!asset) {
      assetDraft.description = ''
      assetDraft.tags = []
      assetEditing.value = false
      return
    }

    // Initialize with AI suggestion if available, otherwise use current description
    assetDraft.description = asset.ai_suggestion?.trim() || asset.description || ''
    assetDraft.tags = [...(asset.tags || [])]
    assetEditing.value = false
  },
  { immediate: true }
)

// Reset selection when filters change while viewing asset details
watch([searchQuery, selectedSchema, selectedTag, selectedStatus], () => {
  if (selectedAssetId.value) {
    selectedAssetId.value = null
    // Don't reset hasAutoSelected - keep it true to prevent re-selection during filtering
  }
})

// Auto-select first database on initial load or when no asset is selected
watch(
  [filteredTree, selectedAssetId, routeAssetId, loading],
  ([tree, currentSelection, routeId, isLoading]) => {
    // Only auto-select once on initial load
    if (hasAutoSelected.value) return

    // Don't auto-select if loading
    if (isLoading) return

    // Don't auto-select if there's already a selection
    if (currentSelection) return

    // Don't auto-select if there's a route asset ID (user navigation)
    if (routeId) return

    // Don't auto-select if user is actively filtering (they want to see the list)
    const hasActiveFilters =
      searchQuery.value.trim() ||
      selectedSchema.value !== '__all__' ||
      selectedTag.value !== '__all__' ||
      selectedStatus.value !== '__all__'
    if (hasActiveFilters) return

    // Auto-select first database if available
    if (tree.length > 0 && tree[0].asset) {
      const firstDatabaseId = tree[0].asset.id
      selectedAssetId.value = firstDatabaseId
      hasAutoSelected.value = true
    }
  },
  { immediate: true }
)

function setExplorerSheetOpen(value: boolean) {
  showExplorerSheet.value = value
}

function openExplorer() {
  if (isMobile.value) {
    showExplorerSheet.value = true
  } else {
    explorerCollapsed.value = false
  }
}

function expandForAsset(assetId: string) {
  const asset = indexes.assetsByIdMap.value.get(assetId)
  if (!asset) return

  const explorers = [desktopExplorerRef.value, mobileExplorerRef.value].filter(
    (instance): instance is ExplorerInstance => Boolean(instance)
  )

  // Handle SCHEMA assets
  if (asset.type === 'SCHEMA' && asset.schema_facet) {
    const databaseName = asset.schema_facet.database_name
    const schemaName = asset.schema_facet.schema_name
    const databaseKey = `database:${databaseName}`
    const schemaKey = `schema:${databaseName}:${schemaName}`
    explorers.forEach((explorer) => {
      explorer.expandNode(databaseKey)
      explorer.expandNode(schemaKey)
    })
    return
  }

  // Handle TABLE and COLUMN assets
  const table =
    asset.type === 'TABLE'
      ? asset
      : tableById.value.get(asset.column_facet?.parent_table_asset_id || '')
  if (!table) return
  const schemaKey = `schema:${table.table_facet?.schema || ''}`
  const tableKey = `table:${table.id}`
  explorers.forEach((explorer) => {
    explorer.expandNode(schemaKey)
    if (asset.type === 'COLUMN') {
      explorer.expandNode(tableKey)
    }
  })
}

function handleSelectAsset(assetId: string) {
  selectedAssetId.value = assetId
  if (isMobile.value) {
    showExplorerSheet.value = false
  }
}

function clearFilters() {
  searchQueryInput.value = ''
  searchQuery.value = ''
  selectedDatabase.value = '__all__'
  selectedSchema.value = '__all__'
  selectedTag.value = '__all__'
  selectedStatus.value = '__all__'
}

async function refresh() {
  if (!contextsStore.contextSelected) return
  // Invalidate TanStack Query cache to trigger refetch
  await queryClient.invalidateQueries({
    queryKey: ['catalog', 'assets', contextsStore.contextSelected.id]
  })
}

function getTableColumnCount(tableId: string): number {
  return columnsByTableId.value.get(tableId)?.length || 0
}

// Asset editing (unified for both tables and columns)
function startAssetEdit() {
  if (!selectedAsset.value) return
  assetEditError.value = null
  assetEditing.value = true
}

function cancelAssetEdit() {
  const asset = selectedAsset.value
  if (!asset) return
  // Restore AI suggestion if available, otherwise use current description
  assetDraft.description = asset.ai_suggestion?.trim() || asset.description || ''
  assetDraft.tags = [...(asset.tags || [])]
  assetEditing.value = false
  assetEditError.value = null
}

function updateAssetDraft(draft: EditableDraft) {
  assetDraft.description = draft.description
  assetDraft.tags = draft.tags
}

async function saveAssetDetails() {
  const asset = selectedAsset.value
  if (!asset || assetSaving.value || !assetHasChanges.value) {
    if (!assetHasChanges.value) {
      assetEditing.value = false
    }
    return
  }

  assetEditError.value = null

  try {
    assetSaving.value = true
    const updatePayload: CatalogAssetUpdatePayload = {
      description: assetDraft.description.trim(),
      tag_ids: assetDraft.tags.map((tag) => tag.id)
    }

    // If there's AI metadata (suggestion or flag reason), clear it when saving (approving)
    const needsReview = ['needs_review', 'requires_validation'].includes(asset.status || '')
    const hasAiMetadata = asset.ai_suggestion || asset.ai_flag_reason
    if (needsReview || hasAiMetadata) {
      updatePayload.ai_suggestion = null
      updatePayload.ai_flag_reason = null
    }

    const updated = await catalogStore.updateAsset(asset.id, updatePayload)

    // Update the query cache directly instead of refetching
    const queryKey = ['catalog', 'assets', contextsStore.contextSelected?.id]
    queryClient.setQueryData(queryKey, (oldData: CatalogAsset[] | undefined) => {
      if (!oldData) return oldData
      return oldData.map((a) => (a.id === updated.id ? updated : a))
    })

    // Update draft with the saved description (not AI suggestion anymore)
    assetDraft.description = updated.description ?? assetDraft.description
    assetDraft.tags = [...(updated.tags || [])]
    assetEditing.value = false
  } catch (error) {
    console.error('Failed to update asset details', error)
    assetEditError.value = 'Failed to save changes. Please try again.'
  } finally {
    assetSaving.value = false
  }
}

async function dismissAssetFlag() {
  const asset = selectedAsset.value
  if (!asset || assetSaving.value) return

  try {
    assetSaving.value = true
    assetEditError.value = null
    const updated = await catalogStore.dismissFlag(asset.id)

    // Update the query cache directly instead of refetching
    const queryKey = ['catalog', 'assets', contextsStore.contextSelected?.id]
    queryClient.setQueryData(queryKey, (oldData: CatalogAsset[] | undefined) => {
      if (!oldData) return oldData
      return oldData.map((a) => (a.id === updated.id ? updated : a))
    })
  } catch (error) {
    console.error('Failed to dismiss flag:', error)
    assetEditError.value = 'Failed to dismiss flag. Please try again.'
  } finally {
    assetSaving.value = false
  }
}

async function approveAssetSuggestion(payload: { description: string; tagIds: string[] }) {
  const asset = selectedAsset.value
  if (!asset || assetSaving.value) return

  try {
    assetSaving.value = true
    assetEditError.value = null

    const updated = await catalogStore.updateAsset(asset.id, {
      description: payload.description,
      tag_ids: payload.tagIds,
      ai_suggestion: null,
      ai_flag_reason: null,
      ai_suggested_tags: null
    })

    // Update the query cache directly instead of refetching
    const queryKey = ['catalog', 'assets', contextsStore.contextSelected?.id]
    queryClient.setQueryData(queryKey, (oldData: CatalogAsset[] | undefined) => {
      if (!oldData) return oldData
      return oldData.map((a) => (a.id === updated.id ? updated : a))
    })

    // Update draft with the saved description
    assetDraft.description = updated.description ?? payload.description
    assetDraft.tags = [...(updated.tags || [])]
  } catch (error) {
    console.error('Failed to approve suggestion:', error)
    assetEditError.value = 'Failed to approve suggestion. Please try again.'
  } finally {
    assetSaving.value = false
  }
}
</script>
