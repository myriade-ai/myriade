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
            :tree="explorerTree"
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
            <!-- Filters Bar (only when viewing list) -->
            <CatalogFilters
              v-if="!selectedAsset"
              v-model:search-query="searchQueryInput"
              v-model:selected-database="selectedDatabase"
              v-model:selected-schema="selectedSchema"
              v-model:selected-tag="selectedTag"
              v-model:selected-status="selectedStatus"
              v-model:has-ai-suggestion="hasAiSuggestion"
              :database-options="databaseOptions"
              :schema-options="schemaOptions"
              :tag-options="tagOptions"
              :has-active-filters="hasActiveFilters"
              :explorer-collapsed="explorerCollapsed"
              :show-explorer-shortcut="isMobile"
              :is-searching="isSearching"
              :ai-suggestion-count="filterCounts.aiSuggestionCount"
              :draft-count="filterCounts.draftCount"
              :published-count="filterCounts.publishedCount"
              :unverified-count="filterCounts.unverifiedCount"
              @clear-filters="clearFilters"
              @toggle-explorer="openExplorer"
              @open-explorer="openExplorer"
            />

            <!-- Details Navigation Bar (when viewing asset details) -->
            <div
              v-else
              class="flex items-center gap-3 flex-shrink-0 px-4 py-3 border-b border-border bg-gradient-to-r from-muted/50 via-muted/30 to-muted/50 dark:from-muted/20 dark:via-muted/10 dark:to-muted/20"
            >
              <!-- Explorer toggle (when collapsed) -->
              <Button
                v-if="explorerCollapsed && !isMobile"
                variant="ghost"
                size="icon"
                @click="openExplorer"
                title="Expand explorer"
                class="-ml-2"
              >
                <ChevronsRight class="h-4 w-4" />
              </Button>
              <!-- Mobile explorer button -->
              <Button
                v-if="isMobile"
                variant="ghost"
                size="icon"
                @click="openExplorer"
                class="-ml-2"
              >
                <PanelLeft class="size-4" />
              </Button>
              <!-- Breadcrumb navigation -->
              <Breadcrumb>
                <BreadcrumbList>
                  <!-- List (root) -->
                  <BreadcrumbItem>
                    <BreadcrumbLink
                      class="flex items-center gap-1.5 cursor-pointer"
                      @click="clearAssetSelection"
                    >
                      <List class="h-4 w-4" />
                      <span>Back to list</span>
                    </BreadcrumbLink>
                  </BreadcrumbItem>

                  <!-- Database -->
                  <template v-if="breadcrumbItems.database">
                    <BreadcrumbSeparator />
                    <BreadcrumbItem>
                      <BreadcrumbLink
                        v-if="breadcrumbItems.database.id !== selectedAssetId"
                        class="cursor-pointer"
                        @click="handleBreadcrumbNavigation(breadcrumbItems.database.id)"
                      >
                        {{ breadcrumbItems.database.name }}
                      </BreadcrumbLink>
                      <BreadcrumbPage v-else>
                        {{ breadcrumbItems.database.name }}
                      </BreadcrumbPage>
                    </BreadcrumbItem>
                  </template>

                  <!-- Schema -->
                  <template v-if="breadcrumbItems.schema">
                    <BreadcrumbSeparator />
                    <BreadcrumbItem>
                      <BreadcrumbLink
                        v-if="breadcrumbItems.schema.id !== selectedAssetId"
                        class="cursor-pointer"
                        @click="handleBreadcrumbNavigation(breadcrumbItems.schema.id)"
                      >
                        {{ breadcrumbItems.schema.name }}
                      </BreadcrumbLink>
                      <BreadcrumbPage v-else>
                        {{ breadcrumbItems.schema.name }}
                      </BreadcrumbPage>
                    </BreadcrumbItem>
                  </template>

                  <!-- Table -->
                  <template v-if="breadcrumbItems.table">
                    <BreadcrumbSeparator />
                    <BreadcrumbItem>
                      <BreadcrumbLink
                        v-if="breadcrumbItems.table.id !== selectedAssetId"
                        class="cursor-pointer"
                        @click="handleBreadcrumbNavigation(breadcrumbItems.table.id)"
                      >
                        {{ breadcrumbItems.table.name }}
                      </BreadcrumbLink>
                      <BreadcrumbPage v-else>
                        {{ breadcrumbItems.table.name }}
                      </BreadcrumbPage>
                    </BreadcrumbItem>
                  </template>

                  <!-- Column -->
                  <template v-if="breadcrumbItems.column">
                    <BreadcrumbSeparator />
                    <BreadcrumbItem>
                      <BreadcrumbPage>
                        {{ breadcrumbItems.column.name }}
                      </BreadcrumbPage>
                    </BreadcrumbItem>
                  </template>
                </BreadcrumbList>
              </Breadcrumb>
            </div>

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
              @publish="publishAssetFromDetails"
              @update:draft="updateAssetDraft"
              @approve-description="approveDescriptionSuggestion"
              @approve-tags="approveTagsSuggestion"
              @reject-description="rejectDescriptionSuggestion"
              @reject-tags="rejectTagsSuggestion"
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
          :tree="explorerTree"
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
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator
} from '@/components/ui/breadcrumb'
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
import { ChevronsRight, List, PanelLeft } from 'lucide-vue-next'
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

const route = useRoute()
const getStateParam = (key: string, defaultValue: string = '__all__') => {
  const state = window.history.state as Record<string, unknown> | null
  if (!state) return defaultValue
  const value = state[key]
  return typeof value === 'string' && value.trim().length > 0 ? value : defaultValue
}

const searchQueryInput = ref('')
const searchQuery = ref('')
const selectedDatabase = ref('__all__')
const selectedSchema = ref('__all__')
const selectedTag = ref('__all__')
const selectedStatus = ref(getStateParam('status'))
const hasAiSuggestion = ref(getStateParam('ai'))
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
      selectedStatus.value !== '__all__' ||
      hasAiSuggestion.value !== '__all__')
  )
})

const { data: searchResultIds, isFetching: isSearching } = useCatalogSearchQuery(
  selectedDatabaseId,
  searchQuery,
  searchEnabled,
  selectedTag,
  selectedStatus,
  hasAiSuggestion
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
      (selectedStatus.value && selectedStatus.value !== '__all__') ||
      (hasAiSuggestion.value && hasAiSuggestion.value !== '__all__')
  )
)

// Filter counts for the filter chips
const filterCounts = computed(() => {
  const assets = assetsData.value || []
  return {
    aiSuggestionCount: assets.filter(
      (a) => a.ai_suggestion || (a.ai_suggested_tags && a.ai_suggested_tags.length > 0)
    ).length,
    draftCount: assets.filter((a) => a.status === 'draft').length,
    publishedCount: assets.filter((a) => a.status === 'published').length,
    unverifiedCount: assets.filter((a) => !a.status).length
  }
})

const filteredTree = computed(() =>
  buildFilteredTree({
    selectedDatabase: selectedDatabase.value,
    selectedSchema: selectedSchema.value,
    matchingIds: matchingIds.value
  })
)

// Unfiltered tree for the explorer (always shows all assets)
const explorerTree = computed(() =>
  buildFilteredTree({
    selectedDatabase: '__all__',
    selectedSchema: '__all__',
    matchingIds: null
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

// Breadcrumb items for navigation hierarchy
const breadcrumbItems = computed(() => {
  const asset = selectedAsset.value
  if (!asset) return {}

  const items: {
    database?: { id: string; name: string }
    schema?: { id: string; name: string }
    table?: { id: string; name: string }
    column?: { id: string; name: string }
  } = {}

  if (asset.type === 'DATABASE') {
    items.database = {
      id: asset.id,
      name: asset.database_facet?.database_name || asset.name || 'Database'
    }
  } else if (asset.type === 'SCHEMA') {
    // Find parent database
    const dbName = asset.schema_facet?.database_name
    if (dbName) {
      const dbAsset = assetsData.value?.find(
        (a) => a.type === 'DATABASE' && a.database_facet?.database_name === dbName
      )
      if (dbAsset) {
        items.database = { id: dbAsset.id, name: dbName }
      }
    }
    items.schema = {
      id: asset.id,
      name: asset.schema_facet?.schema_name || asset.name || 'Schema'
    }
  } else if (asset.type === 'TABLE') {
    const tableFacet = asset.table_facet
    // Find parent database
    if (tableFacet?.database_name) {
      const dbAsset = assetsData.value?.find(
        (a) => a.type === 'DATABASE' && a.database_facet?.database_name === tableFacet.database_name
      )
      if (dbAsset) {
        items.database = { id: dbAsset.id, name: tableFacet.database_name }
      }
    }
    // Find parent schema
    if (tableFacet?.parent_schema_asset_id) {
      const schemaAsset = indexes.assetsByIdMap.value.get(tableFacet.parent_schema_asset_id)
      if (schemaAsset) {
        items.schema = {
          id: schemaAsset.id,
          name: schemaAsset.schema_facet?.schema_name || tableFacet.schema || 'Schema'
        }
      }
    } else if (tableFacet?.schema) {
      // Fallback: find schema by name
      const schemaAsset = assetsData.value?.find(
        (a) =>
          a.type === 'SCHEMA' &&
          a.schema_facet?.schema_name === tableFacet.schema &&
          a.schema_facet?.database_name === tableFacet.database_name
      )
      if (schemaAsset) {
        items.schema = { id: schemaAsset.id, name: tableFacet.schema }
      }
    }
    items.table = {
      id: asset.id,
      name: tableFacet?.table_name || asset.name || 'Table'
    }
  } else if (asset.type === 'COLUMN') {
    const columnFacet = asset.column_facet

    // First, find the parent table asset - this is the most reliable source
    const tableAsset = columnFacet?.parent_table_asset_id
      ? indexes.tablesByIdMap.value.get(columnFacet.parent_table_asset_id)
      : null
    const tableFacet = tableAsset?.table_facet || columnFacet?.parent_table_facet

    // Find parent database using table's facet data
    if (tableFacet?.database_name) {
      const dbAsset = assetsData.value?.find(
        (a) => a.type === 'DATABASE' && a.database_facet?.database_name === tableFacet.database_name
      )
      if (dbAsset) {
        items.database = { id: dbAsset.id, name: tableFacet.database_name }
      }
    }

    // Find parent schema using table's facet data
    if (tableFacet?.parent_schema_asset_id) {
      const schemaAsset = indexes.assetsByIdMap.value.get(tableFacet.parent_schema_asset_id)
      if (schemaAsset) {
        items.schema = {
          id: schemaAsset.id,
          name: schemaAsset.schema_facet?.schema_name || tableFacet.schema || 'Schema'
        }
      }
    } else if (tableFacet?.schema) {
      // Fallback: find schema by name
      const schemaAsset = assetsData.value?.find(
        (a) =>
          a.type === 'SCHEMA' &&
          a.schema_facet?.schema_name === tableFacet.schema &&
          a.schema_facet?.database_name === tableFacet.database_name
      )
      if (schemaAsset) {
        items.schema = { id: schemaAsset.id, name: tableFacet.schema }
      }
    }

    // Add parent table to breadcrumb
    if (tableAsset) {
      items.table = {
        id: tableAsset.id,
        name: tableAsset.table_facet?.table_name || tableAsset.name || 'Table'
      }
    }

    items.column = {
      id: asset.id,
      name: columnFacet?.column_name || asset.name || 'Column'
    }
  }

  return items
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
      hasAiSuggestion.value = '__all__'
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
watch([searchQuery, selectedSchema, selectedTag, selectedStatus, hasAiSuggestion], () => {
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

  const explorers = [desktopExplorerRef.value, mobileExplorerRef.value].filter(
    (instance): instance is ExplorerInstance => Boolean(instance)
  )

  // Handle DATABASE assets
  if (asset.type === 'DATABASE' && asset.database_facet) {
    const databaseName = asset.database_facet.database_name
    const databaseKey = `database:${databaseName}`
    explorers.forEach((explorer) => {
      explorer.expandNode(databaseKey)
    })
    return
  }

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
  const databaseName = table.table_facet?.database_name || ''
  const schemaName = table.table_facet?.schema || ''
  const databaseKey = `database:${databaseName}`
  const schemaKey = `schema:${databaseName}:${schemaName}`
  const tableKey = `table:${table.id}`
  explorers.forEach((explorer) => {
    explorer.expandNode(databaseKey)
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

function handleBreadcrumbNavigation(assetId: string) {
  // Clear filters when navigating via breadcrumb to ensure the asset is visible
  if (hasActiveFilters.value) {
    clearFilters()
  }
  selectedAssetId.value = assetId
}

function clearAssetSelection() {
  selectedAssetId.value = null
}

function clearFilters() {
  searchQueryInput.value = ''
  searchQuery.value = ''
  selectedDatabase.value = '__all__'
  selectedSchema.value = '__all__'
  selectedTag.value = '__all__'
  selectedStatus.value = '__all__'
  hasAiSuggestion.value = '__all__'
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

    // Clear AI suggestion when saving (it's been applied to description)
    // Keep note for context - don't clear it
    if (asset.ai_suggestion) {
      updatePayload.ai_suggestion = null
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

async function approveDescriptionSuggestion(description: string) {
  const asset = selectedAsset.value
  if (!asset || assetSaving.value) return

  try {
    assetSaving.value = true
    assetEditError.value = null

    const updated = await catalogStore.updateAsset(asset.id, {
      description: description,
      ai_suggestion: null
      // Keep note for context - don't clear it
      // Keep ai_suggested_tags if they exist
    })

    // Update the query cache directly instead of refetching
    const queryKey = ['catalog', 'assets', contextsStore.contextSelected?.id]
    queryClient.setQueryData(queryKey, (oldData: CatalogAsset[] | undefined) => {
      if (!oldData) return oldData
      return oldData.map((a) => (a.id === updated.id ? updated : a))
    })

    // Update draft with the saved description
    assetDraft.description = updated.description ?? description
  } catch (error) {
    console.error('Failed to approve description:', error)
    assetEditError.value = 'Failed to approve description. Please try again.'
  } finally {
    assetSaving.value = false
  }
}

async function approveTagsSuggestion(tagIds: string[]) {
  const asset = selectedAsset.value
  if (!asset || assetSaving.value) return

  try {
    assetSaving.value = true
    assetEditError.value = null

    const updated = await catalogStore.updateAsset(asset.id, {
      tag_ids: tagIds,
      ai_suggested_tags: null
      // Keep ai_suggestion if it exists
    })

    // Update the query cache directly instead of refetching
    const queryKey = ['catalog', 'assets', contextsStore.contextSelected?.id]
    queryClient.setQueryData(queryKey, (oldData: CatalogAsset[] | undefined) => {
      if (!oldData) return oldData
      return oldData.map((a) => (a.id === updated.id ? updated : a))
    })

    // Update draft with the saved tags
    assetDraft.tags = [...(updated.tags || [])]
  } catch (error) {
    console.error('Failed to approve tags:', error)
    assetEditError.value = 'Failed to approve tags. Please try again.'
  } finally {
    assetSaving.value = false
  }
}

async function rejectDescriptionSuggestion() {
  const asset = selectedAsset.value
  if (!asset || assetSaving.value) return

  try {
    assetSaving.value = true
    assetEditError.value = null

    const updated = await catalogStore.updateAsset(asset.id, {
      ai_suggestion: null
      // Keep description and ai_suggested_tags unchanged
    })

    // Update the query cache directly
    const queryKey = ['catalog', 'assets', contextsStore.contextSelected?.id]
    queryClient.setQueryData(queryKey, (oldData: CatalogAsset[] | undefined) => {
      if (!oldData) return oldData
      return oldData.map((a) => (a.id === updated.id ? updated : a))
    })
  } catch (error) {
    console.error('Failed to reject description:', error)
    assetEditError.value = 'Failed to reject suggestion. Please try again.'
  } finally {
    assetSaving.value = false
  }
}

async function rejectTagsSuggestion() {
  const asset = selectedAsset.value
  if (!asset || assetSaving.value) return

  try {
    assetSaving.value = true
    assetEditError.value = null

    const updated = await catalogStore.updateAsset(asset.id, {
      ai_suggested_tags: null
      // Keep tags and ai_suggestion unchanged
    })

    // Update the query cache directly
    const queryKey = ['catalog', 'assets', contextsStore.contextSelected?.id]
    queryClient.setQueryData(queryKey, (oldData: CatalogAsset[] | undefined) => {
      if (!oldData) return oldData
      return oldData.map((a) => (a.id === updated.id ? updated : a))
    })
  } catch (error) {
    console.error('Failed to reject tags:', error)
    assetEditError.value = 'Failed to reject suggestion. Please try again.'
  } finally {
    assetSaving.value = false
  }
}

async function publishAssetFromDetails() {
  const asset = selectedAsset.value
  if (!asset || assetSaving.value) return

  try {
    assetSaving.value = true
    assetEditError.value = null

    const updated = await catalogStore.publishAsset(asset.id)

    // Update the query cache directly instead of refetching
    const queryKey = ['catalog', 'assets', contextsStore.contextSelected?.id]
    queryClient.setQueryData(queryKey, (oldData: CatalogAsset[] | undefined) => {
      if (!oldData) return oldData
      return oldData.map((a) => (a.id === updated.id ? updated : a))
    })

    // End editing mode
    assetEditing.value = false
  } catch (error) {
    console.error('Failed to publish asset', error)
    assetEditError.value = 'Failed to publish asset. Please try again.'
  } finally {
    assetSaving.value = false
  }
}
</script>
