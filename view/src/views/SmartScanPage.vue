<template>
  <div class="flex min-h-full flex-col bg-background">
    <header
      class="relative flex flex-col gap-4 border-b border-border bg-card px-4 py-4 sm:px-6 sm:py-5 sm:flex-row sm:items-start sm:justify-between"
    >
      <div class="flex items-start gap-3 pr-10 sm:pr-0">
        <div
          class="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 text-primary-600"
        >
          <RocketIcon class="h-5 w-5" />
        </div>
        <div class="space-y-1">
          <p class="text-xs font-semibold uppercase tracking-wide text-primary-600">Smart Scan</p>
          <h2 class="text-lg sm:text-xl font-semibold text-foreground">
            AI-assisted documentation run
          </h2>
          <p class="text-xs sm:text-sm text-muted-foreground">
            Select assets to document with AI assistance
          </p>
        </div>
      </div>

      <!-- Close button - top right on mobile, right side on desktop -->
      <Button
        variant="ghost"
        class="absolute right-2 top-2 sm:relative sm:right-auto sm:top-auto sm:gap-2 sm:w-auto"
        @click="goBack"
      >
        <XIcon class="h-4 w-4" />
        <span class="hidden sm:inline">Close</span>
      </Button>
    </header>

    <!-- Step Indicator (Mobile Only) -->
    <div class="border-b border-border bg-card px-4 py-3 lg:hidden">
      <div class="flex items-center justify-center gap-2">
        <div v-for="step in 2" :key="step" class="flex items-center">
          <div
            class="flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold transition-colors"
            :class="
              currentStep === step
                ? 'bg-primary-600 text-white'
                : currentStep > step
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-muted text-muted-foreground'
            "
          >
            {{ step }}
          </div>
          <div
            v-if="step < 2"
            class="mx-2 h-0.5 w-8 transition-colors"
            :class="currentStep > step ? 'bg-primary-200' : 'bg-border'"
          />
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto pb-safe">
      <!-- Mobile: 2-step workflow -->
      <div class="mx-auto max-w-4xl p-4 pb-6 sm:p-6 lg:hidden">
        <!-- Step 1: Select Assets -->
        <section v-if="currentStep === 1" class="space-y-6">
          <div>
            <h3 class="text-lg font-semibold text-foreground mb-2">Select assets to document</h3>
            <p class="text-sm text-muted-foreground mb-6">
              Choose up to {{ MAX_SELECTION_LIMIT }} assets ({{
                catalogStore.selectedAssetIds.length
              }}
              selected)
            </p>
          </div>

          <div
            v-if="isAtSelectionLimit"
            class="rounded-md border border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-900/20 p-3 text-sm text-orange-700 dark:text-orange-300"
          >
            <div class="flex items-start gap-2">
              <AlertCircleIcon class="mt-0.5 h-4 w-4 flex-shrink-0" />
              <p>Selection limit reached ({{ MAX_SELECTION_LIMIT }} assets maximum).</p>
            </div>
          </div>

          <div class="space-y-3 rounded-lg border border-border bg-card p-3 sm:p-4">
            <div class="relative">
              <SearchIcon
                class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
              />
              <Input
                :model-value="filterText"
                class="pl-9"
                placeholder="Filter databases, schemas, tables..."
                @update:model-value="
                  (value) => {
                    filterText = String(value)
                    handleSearchInput(String(value))
                  }
                "
              />
            </div>
            <div class="flex flex-wrap items-center justify-between gap-3">
              <label class="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
                <Checkbox
                  id="undocumented-filter-mobile"
                  :model-value="showOnlyUndocumented"
                  class="cursor-pointer"
                  @click.stop.prevent="showOnlyUndocumented = !showOnlyUndocumented"
                />
                <span class="select-none">Show only undocumented</span>
              </label>
            </div>

            <div class="rounded-md border border-border bg-muted/70">
              <div
                v-if="explorerTree.length === 0"
                class="flex flex-col items-center gap-3 py-12 text-center"
              >
                <SparklesIcon class="h-6 w-6 text-muted-foreground" />
                <p class="text-sm font-medium text-foreground">No assets to display</p>
                <p class="text-xs text-muted-foreground">
                  Adjust your filters or select a different catalog to get started.
                </p>
              </div>

              <div v-else class="max-h-[60vh] overflow-y-auto">
                <UnifiedExplorer
                  :tree="explorerTree"
                  :selected-asset-id="null"
                  mode="select"
                  :selected-asset-ids="selectedIdsComputed"
                  :disabled="false"
                  :collapsed="false"
                  :show-collapse-button="false"
                  :show-header="false"
                  :show-search="false"
                  :show-status-badge="true"
                  :expand-databases-by-default="true"
                  @toggle-asset-selection="handleToggleAssetSelection"
                  @select-all-children="handleSelectAllChildren"
                />
              </div>
            </div>
          </div>

          <!-- Navigation -->
          <div class="flex flex-col gap-3 pt-6 sm:flex-row sm:justify-between">
            <Button variant="ghost" @click="goBack" class="w-full sm:w-auto">Cancel</Button>
            <Button :disabled="!canProceedToStep2" @click="nextStep" class="w-full sm:w-auto">
              Next
              <ChevronRight class="h-4 w-4" />
            </Button>
          </div>
        </section>

        <!-- Step 2: Review & Run -->
        <section v-if="currentStep === 2" class="space-y-6">
          <div>
            <h3 class="text-lg font-semibold text-foreground mb-2">Review your selection</h3>
            <p class="text-sm text-muted-foreground mb-6">
              Verify your Smart Scan settings before starting
            </p>
          </div>

          <div class="space-y-4 rounded-lg border border-border bg-card p-4 sm:p-6">
            <div class="border-t border-border pt-4">
              <h4 class="text-sm font-semibold text-foreground mb-3">Selected Assets</h4>
              <ul class="space-y-2 text-sm text-foreground">
                <li class="flex items-center gap-2">
                  <Database class="h-4 w-4 text-primary-500" />
                  <span
                    >{{ selectedDatabasesCount }} database{{
                      selectedDatabasesCount === 1 ? '' : 's'
                    }}</span
                  >
                </li>
                <li class="flex items-center gap-2">
                  <FolderIcon class="h-4 w-4 text-primary-500" />
                  <span
                    >{{ selectedSchemasCount }} schema{{
                      selectedSchemasCount === 1 ? '' : 's'
                    }}</span
                  >
                </li>
                <li class="flex items-center gap-2">
                  <TableIcon class="h-4 w-4 text-primary-500" />
                  <span
                    >{{ selectedTables.length }} table{{
                      selectedTables.length === 1 ? '' : 's'
                    }}</span
                  >
                </li>
                <li class="flex items-center gap-2">
                  <Columns3Icon class="h-4 w-4 text-muted-foreground" />
                  <span
                    >{{ selectedColumns.length }} column{{
                      selectedColumns.length === 1 ? '' : 's'
                    }}</span
                  >
                </li>
              </ul>
            </div>

            <div class="border-t border-border pt-4">
              <div class="rounded-md bg-muted p-4 text-sm text-muted-foreground">
                <div class="flex items-center gap-2 font-medium text-foreground">
                  <ClockIcon class="h-4 w-4 text-primary-500" />
                  Estimated time: {{ estimatedTimeLabel }}
                </div>
                <p class="mt-2 text-xs text-muted-foreground">
                  Smart Scan runs in the background — you can continue working while documentation
                  is generated.
                </p>
              </div>
            </div>

            <div class="border-t border-border pt-4">
              <div class="rounded-md bg-primary-50/70 p-4 text-sm text-primary-700">
                <div class="flex items-start gap-2">
                  <SparklesIcon class="mt-0.5 h-4 w-4" />
                  <p>
                    The AI will prioritize clarity, business context, and data quality insights for
                    every selected asset.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Navigation -->
          <div class="flex flex-col gap-3 pt-6 sm:flex-row sm:justify-between">
            <Button
              variant="ghost"
              @click="previousStep"
              class="w-full sm:w-auto order-2 sm:order-1"
            >
              <ChevronLeft class="h-4 w-4" />
              Back
            </Button>
            <Button
              :disabled="!canProceed"
              @click="analyzeSelected"
              class="w-full sm:w-auto order-1 sm:order-2"
            >
              Start Smart Scan
              <SparklesIcon class="h-4 w-4" />
            </Button>
          </div>
        </section>
      </div>

      <!-- Desktop: 2-column layout with full height -->
      <div class="hidden lg:flex h-full gap-6 p-4 sm:p-6 mx-auto w-full">
        <section class="flex-[2] flex flex-col min-h-0">
          <div
            class="flex-1 space-y-3 rounded-lg border border-border bg-card p-3 sm:p-4 flex flex-col overflow-hidden"
          >
            <div class="relative">
              <SearchIcon
                class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
              />
              <Input
                :model-value="filterText"
                class="pl-9"
                placeholder="Filter databases, schemas, tables..."
                @update:model-value="
                  (value) => {
                    filterText = String(value)
                    handleSearchInput(String(value))
                  }
                "
              />
            </div>
            <div class="flex flex-wrap items-center justify-between gap-3">
              <label class="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
                <Checkbox
                  id="undocumented-filter-desktop"
                  :model-value="showOnlyUndocumented"
                  class="cursor-pointer"
                  @click.stop.prevent="showOnlyUndocumented = !showOnlyUndocumented"
                />
                <span class="select-none">Show only undocumented</span>
              </label>
            </div>

            <div
              class="flex-1 rounded-md border border-border bg-muted/70 overflow-hidden flex flex-col"
            >
              <div
                v-if="explorerTree.length === 0"
                class="flex flex-col items-center gap-3 py-12 text-center h-full justify-center"
              >
                <SparklesIcon class="h-6 w-6 text-muted-foreground" />
                <p class="text-sm font-medium text-foreground">No assets to display</p>
                <p class="text-xs text-muted-foreground">
                  Adjust your filters or select a different catalog to get started.
                </p>
              </div>

              <div v-else class="flex-1 overflow-y-auto">
                <UnifiedExplorer
                  :tree="explorerTree"
                  :selected-asset-id="null"
                  mode="select"
                  :selected-asset-ids="selectedIdsComputed"
                  :disabled="false"
                  :collapsed="false"
                  :show-collapse-button="false"
                  :show-header="false"
                  :show-search="false"
                  :show-status-badge="true"
                  :expand-databases-by-default="true"
                  @toggle-asset-selection="handleToggleAssetSelection"
                  @select-all-children="handleSelectAllChildren"
                />
              </div>
            </div>
          </div>
        </section>

        <aside class="flex-1 flex flex-col rounded-lg border border-border bg-card overflow-hidden">
          <!-- Scrollable content area -->
          <div class="flex-1 overflow-y-auto space-y-4 p-4 sm:p-5 min-h-0">
            <div class="space-y-2">
              <h3 class="text-sm font-semibold text-foreground">Summary</h3>
              <p class="text-xs text-muted-foreground">
                Review your Smart Scan selection before starting.
              </p>
            </div>

            <div
              v-if="isAtSelectionLimit"
              class="rounded-md border border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-900/20 p-3 text-sm text-orange-700 dark:text-orange-300"
            >
              <div class="flex items-start gap-2">
                <AlertCircleIcon class="mt-0.5 h-4 w-4 flex-shrink-0" />
                <p>Selection limit reached ({{ MAX_SELECTION_LIMIT }} assets maximum).</p>
              </div>
            </div>

            <ul class="space-y-2 text-sm text-foreground">
              <li class="flex items-center gap-2">
                <Database class="h-4 w-4 text-primary-500" />
                <span
                  >{{ selectedDatabasesCount }} database{{
                    selectedDatabasesCount === 1 ? '' : 's'
                  }}</span
                >
              </li>
              <li class="flex items-center gap-2">
                <FolderIcon class="h-4 w-4 text-primary-500" />
                <span
                  >{{ selectedSchemasCount }} schema{{
                    selectedSchemasCount === 1 ? '' : 's'
                  }}</span
                >
              </li>
              <li class="flex items-center gap-2">
                <TableIcon class="h-4 w-4 text-primary-500" />
                <span
                  >{{ selectedTables.length }} table{{
                    selectedTables.length === 1 ? '' : 's'
                  }}</span
                >
              </li>
              <li class="flex items-center gap-2">
                <Columns3Icon class="h-4 w-4 text-muted-foreground" />
                <span
                  >{{ selectedColumns.length }} column{{
                    selectedColumns.length === 1 ? '' : 's'
                  }}</span
                >
              </li>
            </ul>

            <div class="rounded-md border border-border bg-muted p-4 text-sm text-muted-foreground">
              <div class="flex items-center gap-2 font-medium text-foreground">
                <ClockIcon class="h-4 w-4 text-primary-500" />
                Estimated time: {{ estimatedTimeLabel }}
              </div>
              <p class="mt-2 text-xs text-muted-foreground">
                Smart Scan runs in the background — you can continue working while documentation is
                generated.
              </p>
            </div>

            <div
              class="rounded-md border border-dashed border-primary-300 bg-primary-50/70 p-4 text-sm text-primary-700"
            >
              <div class="flex items-start gap-2">
                <SparklesIcon class="mt-0.5 h-4 w-4" />
                <p>
                  The AI will prioritize clarity, business context, and data quality insights for
                  every selected asset.
                </p>
              </div>
            </div>

            <div class="flex flex-col gap-2 text-xs text-muted-foreground">
              <p v-if="!canProceed" class="font-medium text-red-600">
                Select at least one asset to continue.
              </p>
            </div>
          </div>

          <!-- Fixed footer with buttons -->
          <div class="flex flex-col gap-2 p-4 sm:p-5 border-t border-border flex-shrink-0">
            <Button variant="ghost" class="justify-center" @click="goBack">Cancel</Button>
            <Button :disabled="!canProceed" @click="analyzeSelected">
              Start Smart Scan
              <SparklesIcon class="h-4 w-4" />
            </Button>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ExplorerDatabaseNode } from '@/components/catalog/types'
import UnifiedExplorer from '@/components/catalog/UnifiedExplorer.vue'
import { useCatalogData } from '@/components/catalog/useCatalogData'
import { useCatalogAssetsQuery } from '@/components/catalog/useCatalogQuery'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { useCatalogStore, type CatalogAsset } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { useConversationsStore } from '@/stores/conversations'
import { debounce } from '@/utils/debounce'
import {
  AlertCircleIcon,
  ChevronLeft,
  ChevronRight,
  ClockIcon,
  Columns3Icon,
  Database,
  FolderIcon,
  RocketIcon,
  SearchIcon,
  SparklesIcon,
  Table as TableIcon,
  XIcon
} from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const MAX_SELECTION_LIMIT = 30

const catalogStore = useCatalogStore()
const contextsStore = useContextsStore()
const conversationsStore = useConversationsStore()
const router = useRouter()

const { data: assets } = useCatalogAssetsQuery()

const catalogData = useCatalogData(computed(() => assets.value))
const { buildFilteredTree } = catalogData

const filterText = ref('')
const showOnlyUndocumented = ref(false)
const currentStep = ref(1)
const debouncedFilterText = ref('')

// Debounced search handler (300ms delay)
const handleSearchInput = debounce((value: string) => {
  debouncedFilterText.value = value
}, 300)

onMounted(() => {
  filterText.value = ''
  debouncedFilterText.value = ''
  showOnlyUndocumented.value = false
  currentStep.value = 1
})

function nextStep() {
  if (currentStep.value < 2) {
    currentStep.value++
  }
}

function previousStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

const canProceedToStep2 = computed(() => {
  return catalogStore.selectedAssetIds.length > 0
})

// Helper to check if an asset is documented
function isAssetDocumented(asset: CatalogAsset): boolean {
  const hasMeaningfulDescription = Boolean(asset.description?.trim())
  const statusDocumented = asset.status === 'published' || asset.status === 'draft'
  return hasMeaningfulDescription || statusDocumented
}

const explorerTree = computed<ExplorerDatabaseNode[]>(() => {
  const query = debouncedFilterText.value.trim().toLowerCase()
  const onlyUndocumented = showOnlyUndocumented.value

  // Get the base tree from the optimized buildFilteredTree
  const baseTree = buildFilteredTree({
    selectedDatabase: '__all__',
    selectedSchema: '__all__',
    matchingIds: null
  })

  if (!query && !onlyUndocumented) {
    return baseTree
  }

  // Apply local filters (search and undocumented)
  const filteredTree: ExplorerDatabaseNode[] = []

  for (const dbNode of baseTree) {
    const filteredSchemas = []

    for (const schemaNode of dbNode.schemas) {
      const filteredTables = []

      for (const tableNode of schemaNode.tables) {
        const tableDocumented = isAssetDocumented(tableNode.asset)

        // Filter by documented status at table level
        if (onlyUndocumented && tableDocumented) continue

        // Filter by search query
        const tableName = tableNode.asset.table_facet?.table_name || tableNode.asset.name || ''
        const matchesFilter =
          !query ||
          tableName.toLowerCase().includes(query) ||
          (schemaNode.name || '').toLowerCase().includes(query) ||
          dbNode.name.toLowerCase().includes(query)

        if (!matchesFilter) continue

        // Filter columns by documented status if needed
        const filteredColumns = onlyUndocumented
          ? tableNode.columns.filter((col) => !isAssetDocumented(col.asset))
          : tableNode.columns

        filteredTables.push({
          ...tableNode,
          columns: filteredColumns
        })
      }

      if (filteredTables.length) {
        filteredSchemas.push({
          ...schemaNode,
          tables: filteredTables
        })
      }
    }

    if (filteredSchemas.length) {
      filteredTree.push({
        ...dbNode,
        schemas: filteredSchemas
      })
    }
  }

  return filteredTree
})

// Create a computed that explicitly tracks the store selection
const selectedIdsComputed = computed(() => [...catalogStore.selectedAssetIds])

function handleToggleAssetSelection(assetId: string) {
  const selectedSet = new Set(catalogStore.selectedAssetIds)
  const isSelected = selectedSet.has(assetId)

  if (isSelected) {
    catalogStore.removeAssetSelection([assetId])
  } else {
    const remainingSlots = MAX_SELECTION_LIMIT - catalogStore.selectedAssetIds.length
    if (remainingSlots > 0) {
      catalogStore.addAssetSelection([assetId])
    }
  }
}

function collectDirectChildren(parentAssetId: string): string[] {
  const ids: string[] = []

  for (const database of explorerTree.value) {
    if (database.asset.id === parentAssetId) {
      // Database: select all schemas
      for (const schema of database.schemas) {
        if (schema.asset) ids.push(schema.asset.id)
      }
      return ids
    }

    for (const schema of database.schemas) {
      if (schema.asset?.id === parentAssetId) {
        // Schema: select all tables
        for (const table of schema.tables) {
          ids.push(table.asset.id)
        }
        return ids
      }

      for (const table of schema.tables) {
        if (table.asset.id === parentAssetId) {
          // Table: select all columns
          for (const column of table.columns) {
            ids.push(column.asset.id)
          }
          return ids
        }
      }
    }
  }

  return ids
}

function handleSelectAllChildren(parentAssetId: string) {
  const childIds = collectDirectChildren(parentAssetId)
  if (!childIds.length) return

  const selectedSet = new Set(catalogStore.selectedAssetIds)
  const allSelected = childIds.every((id) => selectedSet.has(id))

  if (allSelected) {
    catalogStore.removeAssetSelection(childIds)
  } else {
    const idsToAdd = childIds.filter((id) => !selectedSet.has(id))
    const remainingSlots = MAX_SELECTION_LIMIT - catalogStore.selectedAssetIds.length
    if (remainingSlots > 0) {
      const limitedIds = idsToAdd.slice(0, remainingSlots)
      catalogStore.addAssetSelection(limitedIds)
    }
  }
}

const selectedAssets = computed(() => {
  if (!assets.value) return []
  const selectedSet = new Set(catalogStore.selectedAssetIds)
  return assets.value.filter((asset) => selectedSet.has(asset.id))
})

const selectedSchemas = computed(() =>
  selectedAssets.value.filter((asset) => asset.type === 'SCHEMA')
)
const selectedDatabases = computed(() =>
  selectedAssets.value.filter((asset) => asset.type === 'DATABASE')
)
const selectedTables = computed(() =>
  selectedAssets.value.filter((asset) => asset.type === 'TABLE')
)
const selectedColumns = computed(() =>
  selectedAssets.value.filter((asset) => asset.type === 'COLUMN')
)

const selectedDatabasesCount = computed(() => selectedDatabases.value.length)
const selectedSchemasCount = computed(() => selectedSchemas.value.length)

const isAtSelectionLimit = computed(() => {
  return catalogStore.selectedAssetIds.length >= MAX_SELECTION_LIMIT
})

const estimatedTimeLabel = computed(() => {
  const totalAssets = catalogStore.selectedAssetIds.length
  if (totalAssets === 0) {
    return 'Less than a minute'
  }
  const minutes = Math.max(1, Math.round((totalAssets * 30) / 60))
  return `~${minutes} minute${minutes === 1 ? '' : 's'}`
})

const canProceed = computed(() => {
  return catalogStore.selectedAssetIds.length > 0
})

function goBack() {
  catalogStore.clearSelection()
  router.push({ name: 'AssetPage' })
}

async function analyzeSelected() {
  const context = contextsStore.contextSelected
  if (!context) {
    console.error('No context selected')
    return
  }

  const databases = selectedDatabases.value
  const schemas = selectedSchemas.value
  const tables = selectedTables.value
  const columns = selectedColumns.value

  const MAX_DATABASES_IN_PROMPT = 200
  const MAX_SCHEMAS_IN_PROMPT = 200
  const MAX_TABLES_IN_PROMPT = 200
  const MAX_COLUMNS_IN_PROMPT = 200

  const databasesForPrompt = databases.slice(0, MAX_DATABASES_IN_PROMPT)
  const schemasForPrompt = schemas.slice(0, MAX_SCHEMAS_IN_PROMPT)
  const tablesForPrompt = tables.slice(0, MAX_TABLES_IN_PROMPT)
  const columnsForPrompt = columns.slice(0, MAX_COLUMNS_IN_PROMPT)

  const databasesList = databasesForPrompt
    .map(
      (database) =>
        `- ${database.database_facet?.database_name || database.name || database.urn} (id: ${database.id})`
    )
    .join('\n')
  const schemasList = schemasForPrompt
    .map(
      (schema) =>
        `- ${schema.schema_facet?.database_name || 'Unknown'}.${schema.schema_facet?.schema_name || schema.name || schema.urn} (id: ${schema.id})`
    )
    .join('\n')
  const tablesList = tablesForPrompt
    .map(
      (table) => `- ${table.table_facet?.table_name || table.name || table.urn} (id: ${table.id})`
    )
    .join('\n')
  const columnsList = columnsForPrompt
    .map(
      (column) =>
        `- ${column.column_facet?.parent_table_facet?.table_name}.${column.column_facet?.column_name} (id: ${column.id})`
    )
    .join('\n')

  const truncatedDatabases = databases.length > MAX_DATABASES_IN_PROMPT
  const truncatedSchemas = schemas.length > MAX_SCHEMAS_IN_PROMPT
  const truncatedTables = tables.length > MAX_TABLES_IN_PROMPT
  const truncatedColumns = columns.length > MAX_COLUMNS_IN_PROMPT

  const promptSections = [
    'You are running a Smart Scan with the assets manually selected by the user.',
    'Before drafting any documentation, please:',
    '1. Perform a global business understanding pass across the catalog.',
    '2. Prioritize assets that unlock the most analytical value or appear in mission-critical workflows.',
    '3. Produce concise, business-focused descriptions that include relationships, freshness, quality notes, and suggested tags.'
  ]

  if (databasesForPrompt.length > 0) {
    promptSections.push('\n**Databases to document:**', databasesList)
    if (truncatedDatabases) {
      promptSections.push(`\n…and ${databases.length - MAX_DATABASES_IN_PROMPT} more databases.`)
    }
  }

  if (schemasForPrompt.length > 0) {
    promptSections.push('\n**Schemas to document:**', schemasList)
    if (truncatedSchemas) {
      promptSections.push(`\n…and ${schemas.length - MAX_SCHEMAS_IN_PROMPT} more schemas.`)
    }
  }

  if (tablesForPrompt.length > 0) {
    promptSections.push('\n**Tables to document:**', tablesList)
    if (truncatedTables) {
      promptSections.push(`\n…and ${tables.length - MAX_TABLES_IN_PROMPT} more tables.`)
    }
  }

  if (columnsForPrompt.length > 0) {
    promptSections.push('\n**Columns to document:**', columnsList)
    if (truncatedColumns) {
      promptSections.push(`\n…and ${columns.length - MAX_COLUMNS_IN_PROMPT} more columns.`)
    }
  }

  promptSections.push(
    '\nDeliver the output as a structured plan followed by polished descriptions ready to publish in the catalog.'
  )

  const prompt = promptSections.join('\n')

  try {
    const conversation = await conversationsStore.createConversation(context.id)
    await conversationsStore.sendMessage(conversation.id, prompt, 'text')
    router.push({ name: 'ChatPage', params: { id: conversation.id.toString() } })
    catalogStore.clearSelection()
  } catch (error) {
    console.error('Error creating Smart Scan conversation:', error)
  }
}
</script>
