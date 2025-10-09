<template>
  <div class="flex h-full">
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
          v-if="!explorerCollapsed"
          :default-size="25"
          :min-size="15"
          :max-size="40"
          :collapsible="false"
        >
          <CatalogExplorer
            ref="explorerRef"
            v-model:collapsed="explorerCollapsed"
            :tree="filteredTree"
            :selected-asset-id="selectedAssetId"
            @select-asset="handleSelectAsset"
            @select-schema="handleSelectSchema"
          />
        </ResizablePanel>

        <!-- Resizable Handle -->
        <ResizableHandle v-if="!explorerCollapsed" />

        <!-- Right side - Content and Filters Panel -->
        <ResizablePanel :default-size="explorerCollapsed ? 100 : 75">
          <div class="flex flex-1 flex-col min-h-0 h-full">
            <!-- Filters Bar -->
            <CatalogFilters
              v-model:search-query="searchQuery"
              v-model:selected-schema="selectedSchema"
              v-model:selected-tag="selectedTag"
              :schema-options="schemaOptions"
              :tag-options="tagOptions"
              :has-active-filters="hasActiveFilters"
              :explorer-collapsed="explorerCollapsed"
              @clear-filters="clearFilters"
              @toggle-explorer="explorerCollapsed = false"
            />

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
import { useCatalogStore } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import type { CatalogAssetUpdatePayload } from '@/types/catalog'
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { EditableDraft } from './catalog/types'
import { useCatalogData } from './catalog/useCatalogData'

const catalogStore = useCatalogStore()
const contextsStore = useContextsStore()

const loading = computed(() => catalogStore.loading)
const error = computed(() => catalogStore.error)

// State
const searchQuery = ref('')
const selectedSchema = ref('__all__')
const selectedTag = ref('__all__')
const activeTab = ref<'overview' | 'columns'>('overview')
const selectedAssetId = ref<string | null>(null)
const explorerCollapsed = ref(false)
const explorerRef = ref<InstanceType<typeof CatalogExplorer> | null>(null)

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

// Use catalog data composable
const catalogData = useCatalogData()
const {
  tableById,
  columnsByTableId,
  schemaOptions,
  tagOptions,
  computeDocumentationScore,
  buildFilteredTree,
  assetMatchesFilters
} = catalogData

// Computed
const hasActiveFilters = computed(() =>
  Boolean(
    searchQuery.value.trim() ||
      (selectedSchema.value && selectedSchema.value !== '__all__') ||
      (selectedTag.value && selectedTag.value !== '__all__')
  )
)

const filteredTree = computed(() =>
  buildFilteredTree({
    searchQuery: searchQuery.value,
    selectedSchema: selectedSchema.value,
    selectedTag: selectedTag.value
  })
)

const selectedAsset = computed(() => {
  if (!selectedAssetId.value) return null
  return catalogStore.assets[selectedAssetId.value] ?? null
})

const selectedTable = computed(() => {
  const asset = selectedAsset.value
  if (!asset) return null
  if (asset.type === 'TABLE') return asset
  if (asset.type === 'COLUMN') {
    const tableId = asset.column_facet?.parent_table_asset_id
    if (!tableId) return null
    return catalogStore.assets[tableId] ?? null
  }
  return null
})

const columnsForSelectedTable = computed(() => {
  if (!selectedTable.value) return []
  const tableColumns = columnsByTableId.value.get(selectedTable.value.id) || []
  return tableColumns.map((column) => ({
    asset: column,
    label: column.column_facet?.column_name || column.name || 'Unnamed column',
    meta: column.column_facet?.data_type || '',
    score: computeDocumentationScore(column)
  }))
})

const assetHasChanges = computed(() => {
  const asset = selectedAsset.value
  if (!asset) return false

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

const tablesForOverview = computed(() => {
  let tables = catalogStore.tableAssets

  // Filter by schema if selected
  if (selectedSchema.value && selectedSchema.value !== '__all__') {
    tables = tables.filter((table) => {
      const schema = table.table_facet?.schema || ''
      return schema === selectedSchema.value
    })
  }

  // Filter by tag if selected
  if (selectedTag.value && selectedTag.value !== '__all__') {
    tables = tables.filter((table) => {
      return table.tags?.some((tag) => tag.id === selectedTag.value)
    })
  }

  // Filter by search query
  if (searchQuery.value.trim()) {
    tables = tables.filter((table) =>
      assetMatchesFilters(table, {
        searchQuery: searchQuery.value,
        selectedSchema: selectedSchema.value,
        selectedTag: selectedTag.value
      })
    )
  }

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
      searchQuery.value = ''
      selectedSchema.value = '__all__'
      selectedTag.value = '__all__'
      selectedAssetId.value = null
    }
  }
)

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

    assetDraft.description = asset.description ?? ''
    assetDraft.tags = [...(asset.tags || [])]
    assetEditing.value = false
  },
  { immediate: true }
)

// No need for complex column drafts management anymore

// Functions
function expandForAsset(assetId: string) {
  const asset = catalogStore.assets[assetId]
  if (!asset || !explorerRef.value) return
  const table =
    asset.type === 'TABLE'
      ? asset
      : tableById.value.get(asset.column_facet?.parent_table_asset_id || '')
  if (!table) return
  const schemaKey = `schema:${table.table_facet?.schema || ''}`
  const tableKey = `table:${table.id}`
  explorerRef.value.expandNode(schemaKey)
  // Only expand table if we're selecting a column
  if (asset.type === 'COLUMN') {
    explorerRef.value.expandNode(tableKey)
  }
}

function handleSelectAsset(assetId: string) {
  selectedAssetId.value = assetId
}

function handleSelectSchema(schemaKey: string) {
  selectedAssetId.value = null
  const parts = schemaKey.split(':')
  const schemaName = parts.length >= 2 ? parts.slice(1).join(':') : ''
  selectedSchema.value = schemaName || '__all__'
}

function clearFilters() {
  searchQuery.value = ''
  selectedSchema.value = '__all__'
  selectedTag.value = '__all__'
}

async function refresh() {
  if (!contextsStore.contextSelected) return
  await catalogStore.fetchAssets(contextsStore.contextSelected.id)
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
  assetDraft.description = asset.description ?? ''
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

    const updated = await catalogStore.updateAsset(asset.id, updatePayload)

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
</script>
