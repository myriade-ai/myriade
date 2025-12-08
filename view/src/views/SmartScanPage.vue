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
        size="icon"
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
        <div v-for="step in 3" :key="step" class="flex items-center">
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
            v-if="step < 3"
            class="mx-2 h-0.5 w-8 transition-colors"
            :class="currentStep > step ? 'bg-primary-200' : 'bg-border'"
          />
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto pb-safe">
      <!-- Mobile: 3-step workflow -->
      <div class="mx-auto max-w-4xl p-4 pb-6 sm:p-6 lg:hidden">
        <!-- Step 1: Select Scan Mode -->
        <section v-if="currentStep === 1" class="space-y-6">
          <div>
            <h3 class="text-lg font-semibold text-foreground mb-2">Choose your scan mode</h3>
            <p class="text-sm text-muted-foreground mb-6">
              Select how you want to document your assets
            </p>

            <RadioGroup
              :model-value="scanMode"
              @update:model-value="(value: string) => setScanMode(value as ScanMode)"
              class="grid gap-4 sm:grid-cols-3"
            >
              <label
                class="flex cursor-not-allowed items-start gap-3 rounded-lg border border-dashed border-border bg-muted/60 p-4 text-left opacity-60"
              >
                <RadioGroupItem value="quick" id="scan-quick" disabled class="mt-1" />
                <div class="space-y-1">
                  <div class="font-medium text-sm text-foreground">Quick</div>
                  <p class="text-xs text-muted-foreground">Priority assets only (~100 items)</p>
                  <p class="text-xs text-primary-600">Coming soon</p>
                </div>
              </label>

              <label
                class="flex cursor-pointer items-start gap-3 rounded-lg border p-4 text-left transition-colors"
                :class="
                  scanMode === 'custom'
                    ? 'border-primary-300 bg-primary-50/70'
                    : 'border-border hover:border-primary-200'
                "
              >
                <RadioGroupItem value="custom" id="scan-custom" class="mt-1" />
                <div class="space-y-1">
                  <div class="font-medium text-sm text-foreground">Custom</div>
                  <p class="text-xs text-muted-foreground">
                    Choose the exact tables and columns to document
                  </p>
                </div>
              </label>

              <label
                class="flex cursor-not-allowed items-start gap-3 rounded-lg border border-dashed border-border bg-muted/60 p-4 text-left opacity-60"
              >
                <RadioGroupItem value="full" id="scan-full" disabled class="mt-1" />
                <div class="space-y-1">
                  <div class="font-medium text-sm text-foreground">Full</div>
                  <p class="text-xs text-muted-foreground">Entire catalog (runs in batches)</p>
                  <p class="text-xs text-primary-600">Coming soon</p>
                </div>
              </label>
            </RadioGroup>
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

        <!-- Step 2: Select Assets -->
        <section v-if="currentStep === 2" class="space-y-6">
          <div>
            <h3 class="text-lg font-semibold text-foreground mb-2">Select assets to document</h3>
            <p class="text-sm text-muted-foreground mb-4">
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
                v-model="filterText"
                class="pl-9"
                placeholder="Filter databases, schemas, tables..."
              />
            </div>
            <div class="flex flex-wrap items-center justify-between gap-3">
              <label class="flex items-center gap-2 text-sm text-muted-foreground">
                <Checkbox v-model:checked="showOnlyUndocumented" id="undocumented-filter" />
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
                <CatalogExplorer
                  :tree="explorerTree"
                  :selected-asset-id="null"
                  :collapsed="false"
                  :selection-mode="true"
                  :selected-asset-ids="selectedIdsComputed"
                  :disabled="scanMode !== 'custom'"
                  @toggle-asset-selection="handleToggleAssetSelection"
                  @select-all-children="handleSelectAllChildren"
                />
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
              :disabled="!canProceedToStep3"
              @click="nextStep"
              class="w-full sm:w-auto order-1 sm:order-2"
            >
              Next
              <ChevronRight class="h-4 w-4" />
            </Button>
          </div>
        </section>

        <!-- Step 3: Review & Run -->
        <section v-if="currentStep === 3" class="space-y-6">
          <div>
            <h3 class="text-lg font-semibold text-foreground mb-2">Review your selection</h3>
            <p class="text-sm text-muted-foreground mb-6">
              Verify your Smart Scan settings before starting
            </p>
          </div>

          <div class="space-y-4 rounded-lg border border-border bg-card p-4 sm:p-6">
            <div class="space-y-2">
              <h4 class="text-sm font-semibold text-foreground">Scan Mode</h4>
              <p class="text-sm text-muted-foreground capitalize">{{ scanMode }} scan</p>
            </div>

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

      <!-- Desktop: Original 2-column layout -->
      <div class="mx-auto hidden max-w-[1800px] gap-6 p-4 sm:p-6 lg:grid lg:grid-cols-[2fr_1fr]">
        <section class="space-y-4 sm:space-y-6">
          <div class="space-y-3">
            <h3 class="text-sm font-semibold text-foreground">Scan mode</h3>
            <RadioGroup
              :model-value="scanMode"
              @update:model-value="(value: string) => setScanMode(value as ScanMode)"
              class="grid gap-3 md:grid-cols-3"
            >
              <label
                class="flex cursor-not-allowed items-start gap-3 rounded-lg border border-dashed border-border bg-muted/60 p-3 text-left opacity-60"
              >
                <RadioGroupItem value="quick" id="scan-quick" disabled class="mt-1" />
                <div class="space-y-1">
                  <div class="font-medium text-sm text-foreground">Quick</div>
                  <p class="text-xs text-muted-foreground">Priority assets only (~100 items)</p>
                  <p class="text-xs text-primary-600">Coming soon</p>
                </div>
              </label>

              <label
                class="flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-left transition-colors"
                :class="
                  scanMode === 'custom'
                    ? 'border-primary-300 bg-primary-50/70'
                    : 'border-border hover:border-primary-200'
                "
              >
                <RadioGroupItem value="custom" id="scan-custom" class="mt-1" />
                <div class="space-y-1">
                  <div class="font-medium text-sm text-foreground">Custom</div>
                  <p class="text-xs text-muted-foreground">
                    Choose the exact tables and columns to document
                  </p>
                </div>
              </label>

              <label
                class="flex cursor-not-allowed items-start gap-3 rounded-lg border border-dashed border-border bg-muted/60 p-3 text-left opacity-60"
              >
                <RadioGroupItem value="full" id="scan-full" disabled class="mt-1" />
                <div class="space-y-1">
                  <div class="font-medium text-sm text-foreground">Full</div>
                  <p class="text-xs text-muted-foreground">Entire catalog (runs in batches)</p>
                  <p class="text-xs text-primary-600">Coming soon</p>
                </div>
              </label>
            </RadioGroup>
          </div>

          <div class="space-y-3 rounded-lg border border-border bg-card p-3 sm:p-4">
            <div class="relative">
              <SearchIcon
                class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
              />
              <Input
                v-model="filterText"
                class="pl-9"
                placeholder="Filter databases, schemas, tables..."
              />
            </div>
            <div class="flex flex-wrap items-center justify-between gap-3">
              <label class="flex items-center gap-2 text-sm text-muted-foreground">
                <Checkbox v-model:checked="showOnlyUndocumented" id="undocumented-filter" />
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

              <div v-else class="max-h-[520px] overflow-y-auto">
                <CatalogExplorer
                  :tree="explorerTree"
                  :selected-asset-id="null"
                  :collapsed="false"
                  :selection-mode="true"
                  :selected-asset-ids="selectedIdsComputed"
                  :disabled="scanMode !== 'custom'"
                  @toggle-asset-selection="handleToggleAssetSelection"
                  @select-all-children="handleSelectAllChildren"
                />
              </div>
            </div>
          </div>
        </section>

        <aside
          class="space-y-4 rounded-lg border border-border bg-card p-4 sm:p-5 lg:sticky lg:top-6 lg:self-start"
        >
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
                >{{ selectedSchemasCount }} schema{{ selectedSchemasCount === 1 ? '' : 's' }}</span
              >
            </li>
            <li class="flex items-center gap-2">
              <TableIcon class="h-4 w-4 text-primary-500" />
              <span
                >{{ selectedTables.length }} table{{ selectedTables.length === 1 ? '' : 's' }}</span
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
            <p>Switch scan modes or adjust your selection as needed.</p>
            <p v-if="!canProceed" class="font-medium text-red-600">
              Select at least one asset to continue.
            </p>
          </div>

          <div class="flex flex-col gap-2 pt-2">
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
import CatalogExplorer from '@/components/catalog/CatalogExplorer.vue'
import type {
  ExplorerColumnNode,
  ExplorerDatabaseNode,
  ExplorerSchemaNode,
  ExplorerTableNode
} from '@/components/catalog/types'
import { useCatalogAssetsQuery } from '@/components/catalog/useCatalogQuery'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { useCatalogStore, type AssetStatus, type CatalogAsset } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { useConversationsStore } from '@/stores/conversations'
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

type ScanMode = 'quick' | 'custom' | 'full'

const MAX_SELECTION_LIMIT = 30

interface ColumnInfo {
  id: string
  name: string
  status: AssetStatus | null
  documented: boolean
}

interface TableInfo {
  id: string
  name: string
  documented: boolean
  status: AssetStatus | null
  columnCount: number
  columns: ColumnInfo[]
}

interface SchemaInfo {
  key: string
  name: string
  totalTables: number
  totalColumns: number
  documentedTables: number
  tables: TableInfo[]
}

interface DatabaseInfo {
  id: string
  name: string
  totalTables: number
  totalColumns: number
  documentedTables: number
  schemas: SchemaInfo[]
}

const catalogStore = useCatalogStore()
const contextsStore = useContextsStore()
const conversationsStore = useConversationsStore()
const router = useRouter()

const { data: assets } = useCatalogAssetsQuery()

const scanMode = ref<ScanMode>('custom')
const filterText = ref('')
const showOnlyUndocumented = ref(false)
const currentStep = ref(1)

onMounted(() => {
  scanMode.value = 'custom'
  filterText.value = ''
  showOnlyUndocumented.value = false
  currentStep.value = 1
})

function nextStep() {
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

function previousStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

const canProceedToStep2 = computed(() => {
  return scanMode.value === 'custom'
})

const canProceedToStep3 = computed(() => {
  return catalogStore.selectedAssetIds.length > 0
})

const columnAssets = computed(() => assets.value?.filter((asset) => asset.type === 'COLUMN') ?? [])
const schemaAssetsByKey = computed(() => {
  const map = new Map<string, CatalogAsset>()
  assets.value?.forEach((asset) => {
    if (asset.type !== 'SCHEMA') return
    const databaseId = asset.schema_facet?.database_id || asset.database_id
    const schemaName = asset.schema_facet?.schema_name || asset.name || 'Schema'
    if (!databaseId) return
    const key = `${databaseId}::${schemaName}`
    map.set(key, asset)
  })
  return map
})
const databaseAssetsById = computed(() => {
  const map = new Map<string, CatalogAsset>()
  assets.value?.forEach((asset) => {
    if (asset.type !== 'DATABASE') return
    const databaseId = asset.database_id || asset.id
    if (!databaseId) return
    map.set(databaseId, asset)
  })
  return map
})

function isAssetDocumented(asset: CatalogAsset): boolean {
  const hasMeaningfulDescription = Boolean(asset.description?.trim())
  const statusDocumented = asset.status === 'published' || asset.status === 'draft'
  return hasMeaningfulDescription || statusDocumented
}

const columnsByTableId = computed(() => {
  const map = new Map<string, ColumnInfo[]>()
  for (const column of columnAssets.value) {
    const tableId = column.column_facet?.parent_table_asset_id
    if (!tableId) continue

    // Skip TIMESTAMP type columns
    const dataType = column.column_facet?.data_type || ''
    if (dataType.toUpperCase() === 'TIMESTAMP') continue

    if (!map.has(tableId)) {
      map.set(tableId, [])
    }
    map.get(tableId)!.push({
      id: column.id,
      name: column.column_facet?.column_name || column.name || 'Unnamed',
      status: column.status ?? null,
      documented: isAssetDocumented(column)
    })
  }
  return map
})

const databaseGroups = computed<DatabaseInfo[]>(() => {
  if (!assets.value) return []

  const groups = new Map<string, DatabaseInfo>()

  for (const asset of assets.value) {
    if (asset.type !== 'TABLE') continue

    const databaseId = asset.database_id || asset.table_facet?.database_name || 'unknown-database'
    const databaseName =
      asset.table_facet?.database_name ||
      asset.database_facet?.database_name ||
      asset.database_id ||
      'Unknown database'
    const schemaName = asset.table_facet?.schema || 'Public'
    const schemaKey = `${databaseId}::${schemaName}`
    const documented = isAssetDocumented(asset)
    const tableColumns = columnsByTableId.value.get(asset.id) || []

    if (!groups.has(databaseId)) {
      groups.set(databaseId, {
        id: databaseId,
        name: databaseName,
        totalTables: 0,
        totalColumns: 0,
        documentedTables: 0,
        schemas: []
      })
    }

    const databaseGroup = groups.get(databaseId)!
    databaseGroup.totalTables += 1
    databaseGroup.totalColumns += tableColumns.length
    if (documented) {
      databaseGroup.documentedTables += 1
    }

    let schemaGroup = databaseGroup.schemas.find((schema) => schema.key === schemaKey)
    if (!schemaGroup) {
      schemaGroup = {
        key: schemaKey,
        name: schemaName,
        totalTables: 0,
        totalColumns: 0,
        documentedTables: 0,
        tables: []
      }
      databaseGroup.schemas.push(schemaGroup)
    }

    schemaGroup.totalTables += 1
    schemaGroup.totalColumns += tableColumns.length
    if (documented) {
      schemaGroup.documentedTables += 1
    }

    schemaGroup.tables.push({
      id: asset.id,
      name: asset.table_facet?.table_name || asset.name || asset.urn,
      documented,
      status: asset.status ?? null,
      columnCount: tableColumns.length,
      columns: tableColumns
    })
  }

  return Array.from(groups.values())
    .map((database) => {
      database.schemas = database.schemas
        .map((schema) => {
          schema.tables = schema.tables.sort((a, b) => a.name.localeCompare(b.name))
          return schema
        })
        .sort((a, b) => a.name.localeCompare(b.name))
      return database
    })
    .sort((a, b) => a.name.localeCompare(b.name))
})

const explorerTree = computed<ExplorerDatabaseNode[]>(() => {
  const query = filterText.value.trim().toLowerCase()
  const onlyUndocumented = showOnlyUndocumented.value

  const nodes: ExplorerDatabaseNode[] = []

  for (const database of databaseGroups.value) {
    const schemaNodes: ExplorerSchemaNode[] = []

    for (const schema of database.schemas) {
      const tableNodes: ExplorerTableNode[] = []

      for (const table of schema.tables) {
        // Filter by documented status
        if (onlyUndocumented && table.documented) continue

        const matchesFilter =
          !query ||
          table.name.toLowerCase().includes(query) ||
          schema.name.toLowerCase().includes(query) ||
          database.name.toLowerCase().includes(query)

        if (!matchesFilter) continue

        // Get the table asset
        const tableAsset = assets.value?.find((a) => a.id === table.id)
        if (!tableAsset) continue

        // Filter columns by documented status if needed
        const filteredColumns = onlyUndocumented
          ? table.columns.filter((col) => !col.documented)
          : table.columns

        const columnNodes: ExplorerColumnNode[] = filteredColumns.map((column) => {
          const columnAsset = assets.value?.find((a) => a.id === column.id)
          return {
            asset: columnAsset!,
            label: column.name,
            meta: columnAsset?.column_facet?.data_type || ''
          }
        })

        tableNodes.push({
          key: table.id,
          asset: tableAsset,
          columns: columnNodes
        })
      }

      if (tableNodes.length) {
        const schemaAsset = schemaAssetsByKey.value.get(schema.key)

        schemaNodes.push({
          key: schema.key,
          name: schema.name,
          asset: schemaAsset,
          tables: tableNodes
        })
      }
    }

    if (schemaNodes.length) {
      const databaseAsset = databaseAssetsById.value.get(database.id)
      if (!databaseAsset) continue

      nodes.push({
        key: database.id,
        name: database.name,
        asset: databaseAsset,
        schemas: schemaNodes
      })
    }
  }

  return nodes
})

// Create a computed that explicitly tracks the store selection
const selectedIdsComputed = computed(() => [...catalogStore.selectedAssetIds])

function handleToggleAssetSelection(assetId: string) {
  if (scanMode.value !== 'custom') return

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
  if (scanMode.value !== 'custom') return

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
  if (scanMode.value === 'custom') {
    return catalogStore.selectedAssetIds.length > 0
  }
  return false
})

function goBack() {
  catalogStore.clearSelection()
  router.push({ name: 'AssetPage' })
}

function setScanMode(mode: ScanMode) {
  scanMode.value = mode
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

  const modeDescription: Record<ScanMode, string> = {
    quick: 'Quick scan focusing on priority undocumented assets',
    custom: 'Custom scan using the assets manually selected by the user',
    full: 'Comprehensive scan of the entire catalog'
  }

  const promptSections = [
    `You are running a Smart Scan in **${modeDescription[scanMode.value]}** mode.`,
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
