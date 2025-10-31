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
            @select-schema="handleSelectSchema"
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
              v-model:selected-schema="selectedSchema"
              v-model:selected-tag="selectedTag"
              v-model:selected-status="selectedStatus"
              :schema-options="schemaOptions"
              :tag-options="tagOptions"
              :has-active-filters="hasActiveFilters"
              :explorer-collapsed="explorerCollapsed"
              :show-explorer-shortcut="isMobile"
              @clear-filters="clearFilters"
              @toggle-explorer="openExplorer"
              @open-explorer="openExplorer"
            />

            <!-- Stats Bar (shows stats for filtered view) -->
            <div
              v-if="filteredStats && hasActiveFilters"
              class="flex flex-wrap gap-4 px-4 py-2 border-b bg-blue-50/50 flex-shrink-0 text-sm"
            >
              <div class="flex items-center gap-2">
                <span class="font-medium text-gray-700">Filtered:</span>
                <span class="font-semibold text-gray-900">{{ filteredStats.total_assets }}</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="font-medium text-gray-700">Completion:</span>
                <span
                  class="font-semibold"
                  :class="
                    filteredStats.completion_score >= 70
                      ? 'text-green-600'
                      : filteredStats.completion_score >= 40
                        ? 'text-yellow-600'
                        : 'text-red-600'
                  "
                  >{{ filteredStats.completion_score }}%</span
                >
              </div>
              <div class="flex items-center gap-2">
                <span class="font-medium text-gray-700">To Review:</span>
                <span
                  class="font-semibold"
                  :class="filteredStats.assets_to_review > 0 ? 'text-orange-600' : 'text-gray-900'"
                  >{{ filteredStats.assets_to_review }}</span
                >
              </div>
              <div class="flex items-center gap-2">
                <span class="font-medium text-gray-700">Validated:</span>
                <span class="font-semibold text-gray-900">{{
                  filteredStats.assets_validated
                }}</span>
              </div>
            </div>

            <!-- Details View (when asset selected) -->
            <CatalogDetailsView
              v-if="selectedAsset"
              v-model:active-tab="activeTab"
              :asset="selectedAsset"
              :columns="columnsForSelectedTable"
              :draft="assetDraft"
              :is-editing="assetEditing"
              :is-saving="assetSaving"
              :has-changes="assetHasChanges"
              :error="assetEditError"
              @select-column="handleSelectAsset"
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
              :tables="tablesForOverview"
              :get-column-count="getTableColumnCount"
              @select-table="handleSelectAsset"
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
          @select-schema="handleSelectSchema"
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
import { computeCatalogStats } from '@/utils/catalog-stats'
import { useQueryClient } from '@tanstack/vue-query'
import { useMediaQuery } from '@vueuse/core'
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { EditableDraft } from './catalog/types'
import { useCatalogData } from './catalog/useCatalogData'
import { useCatalogAssetsQuery } from './catalog/useCatalogQuery'
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
const selectedSchema = ref('__all__')
const selectedTag = ref('__all__')
const selectedStatus = ref('__all__')
const activeTab = ref<'overview' | 'columns' | 'preview' | 'sources'>('overview')
const isMobile = useMediaQuery('(max-width: 1023px)')
const selectedAssetId = ref<string | null>(null)
const explorerCollapsed = ref(false)
type ExplorerInstance = InstanceType<typeof CatalogExplorer>
const desktopExplorerRef = ref<ExplorerInstance | null>(null)
const mobileExplorerRef = ref<ExplorerInstance | null>(null)
const showExplorerSheet = ref(false)

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
  schemaOptions,
  tagOptions,
  buildFilteredTree,
  assetMatchesFilters,
  indexes
} = catalogData

// Computed
const hasActiveFilters = computed(() =>
  Boolean(
    searchQuery.value.trim() ||
      (selectedSchema.value && selectedSchema.value !== '__all__') ||
      (selectedTag.value && selectedTag.value !== '__all__') ||
      (selectedStatus.value && selectedStatus.value !== '__all__')
  )
)

const filteredTree = computed(() =>
  buildFilteredTree({
    searchQuery: searchQuery.value,
    selectedSchema: selectedSchema.value,
    selectedTag: selectedTag.value,
    selectedStatus: selectedStatus.value
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

  return assetsData.value.filter((asset) =>
    assetMatchesFilters(asset, {
      searchQuery: searchQuery.value,
      selectedSchema: selectedSchema.value,
      selectedTag: selectedTag.value,
      selectedStatus: selectedStatus.value
    })
  )
})

// Compute stats for filtered assets
const filteredStats = computed(() => {
  if (!filteredAssets.value || filteredAssets.value.length === 0) {
    return null
  }
  return computeCatalogStats(filteredAssets.value)
})

const tablesForOverview = computed(() => {
  // Use indexed tables list and filter using assetMatchesFilters
  const tables = indexes.tablesList.value.filter((table) =>
    assetMatchesFilters(table, {
      searchQuery: searchQuery.value,
      selectedSchema: selectedSchema.value,
      selectedTag: selectedTag.value,
      selectedStatus: selectedStatus.value
    })
  )

  // Sort by schema and name
  return tables.slice().sort((a, b) => {
    const schemaA = a.table_facet?.schema || ''
    const schemaB = b.table_facet?.schema || ''
    if (schemaA !== schemaB) return schemaA.localeCompare(schemaB)
    return (a.name || a.table_facet?.table_name || '').localeCompare(
      b.name || b.table_facet?.table_name || ''
    )
  })
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
  }
})

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
  const table =
    asset.type === 'TABLE'
      ? asset
      : tableById.value.get(asset.column_facet?.parent_table_asset_id || '')
  if (!table) return
  const schemaKey = `schema:${table.table_facet?.schema || ''}`
  const tableKey = `table:${table.id}`
  const explorers = [desktopExplorerRef.value, mobileExplorerRef.value].filter(
    (instance): instance is ExplorerInstance => Boolean(instance)
  )
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

function handleSelectSchema(schemaKey: string) {
  selectedAssetId.value = null
  const parts = schemaKey.split(':')
  const schemaName = parts.length >= 2 ? parts.slice(1).join(':') : ''
  selectedSchema.value = schemaName || '__all__'
  // Don't close the sheet when selecting a schema on mobile - let user browse tables
}

function clearFilters() {
  searchQueryInput.value = ''
  searchQuery.value = ''
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
