<template>
  <transition name="slide-up">
    <div
      v-if="catalogStore.selectionMode"
      class="fixed bottom-4 right-4 z-50 bg-white rounded-lg shadow-xl border border-slate-200 max-w-md w-full"
    >
      <div class="px-4 py-3 border-b border-slate-200 bg-slate-50">
        <div class="flex items-center justify-between">
          <div class="flex flex-col gap-1">
            <h3 class="font-semibold text-sm">Selected Assets</h3>
            <div class="flex items-center gap-2 text-xs text-muted-foreground">
              <template v-if="selectedAssets.length > 0">
                <span v-if="selectedAssetsGrouped.databases.length > 0">
                  {{ selectedAssetsGrouped.databases.length }} database{{
                    selectedAssetsGrouped.databases.length !== 1 ? 's' : ''
                  }}
                </span>
                <span
                  v-if="
                    selectedAssetsGrouped.databases.length > 0 &&
                    (selectedAssetsGrouped.schemas.length > 0 ||
                      selectedAssetsGrouped.tables.length > 0 ||
                      selectedAssetsGrouped.columns.length > 0)
                  "
                  class="text-slate-300"
                >
                  •
                </span>
                <span v-if="selectedAssetsGrouped.schemas.length > 0">
                  {{ selectedAssetsGrouped.schemas.length }} schema{{
                    selectedAssetsGrouped.schemas.length !== 1 ? 's' : ''
                  }}
                </span>
                <span
                  v-if="
                    selectedAssetsGrouped.schemas.length > 0 &&
                    (selectedAssetsGrouped.tables.length > 0 ||
                      selectedAssetsGrouped.columns.length > 0)
                  "
                  class="text-slate-300"
                >
                  •
                </span>
                <span v-if="selectedAssetsGrouped.tables.length > 0">
                  {{ selectedAssetsGrouped.tables.length }} table{{
                    selectedAssetsGrouped.tables.length !== 1 ? 's' : ''
                  }}
                </span>
                <span
                  v-if="
                    selectedAssetsGrouped.tables.length > 0 &&
                    selectedAssetsGrouped.columns.length > 0
                  "
                  class="text-slate-300"
                >
                  •
                </span>
                <span v-if="selectedAssetsGrouped.columns.length > 0">
                  {{ selectedAssetsGrouped.columns.length }} column{{
                    selectedAssetsGrouped.columns.length !== 1 ? 's' : ''
                  }}
                </span>
              </template>
              <span v-else>No assets selected yet</span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            class="h-6 w-6"
            @click="closeSelectionPanel"
            title="Clear selection"
          >
            <XIcon class="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div class="max-h-64 overflow-y-auto p-2 space-y-1">
        <!-- Empty State -->
        <div
          v-if="selectedAssets.length === 0"
          class="flex flex-col items-center justify-center py-8 px-4 text-center"
        >
          <div class="rounded-full bg-slate-100 p-3 mb-3">
            <SparklesIcon class="h-6 w-6 text-slate-400" />
          </div>
          <p class="text-sm text-muted-foreground mb-1">Click on assets to select them</p>
          <p class="text-xs text-muted-foreground">
            Use the "Add to Analysis" button on databases, schemas, tables, or columns
          </p>
        </div>

        <!-- Databases -->
        <div v-if="selectedAssetsGrouped.databases.length > 0">
          <p class="text-xs font-medium text-muted-foreground px-2 py-1">Databases</p>
          <div
            v-for="database in selectedAssetsGrouped.databases"
            :key="database.id"
            class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-50 group"
          >
            <Database class="h-4 w-4 text-primary-600 flex-shrink-0" />
            <span class="text-sm truncate flex-1">
              {{ database.database_facet?.database_name || database.name }}
            </span>
            <Button
              variant="ghost"
              size="icon"
              class="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
              @click="catalogStore.toggleAssetSelection(database.id)"
              title="Remove from selection"
            >
              <XIcon class="h-3 w-3" />
            </Button>
          </div>
        </div>

        <!-- Schemas -->
        <div v-if="selectedAssetsGrouped.schemas.length > 0">
          <p class="text-xs font-medium text-muted-foreground px-2 py-1 mt-2">Schemas</p>
          <div
            v-for="schema in selectedAssetsGrouped.schemas"
            :key="schema.id"
            class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-50 group"
          >
            <FolderTree class="h-4 w-4 text-primary-600 flex-shrink-0" />
            <span class="text-sm truncate flex-1">
              {{ schema.schema_facet?.schema_name || schema.name }}
            </span>
            <Button
              variant="ghost"
              size="icon"
              class="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
              @click="catalogStore.toggleAssetSelection(schema.id)"
              title="Remove from selection"
            >
              <XIcon class="h-3 w-3" />
            </Button>
          </div>
        </div>

        <!-- Tables -->
        <div v-if="selectedAssetsGrouped.tables.length > 0">
          <p class="text-xs font-medium text-muted-foreground px-2 py-1 mt-2">Tables</p>
          <div
            v-for="table in selectedAssetsGrouped.tables"
            :key="table.id"
            class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-50 group"
          >
            <Table class="h-4 w-4 text-primary-600 flex-shrink-0" />
            <span class="text-sm truncate flex-1">
              {{ table.name || table.table_facet?.table_name }}
            </span>
            <Button
              variant="ghost"
              size="icon"
              class="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
              @click="catalogStore.toggleAssetSelection(table.id)"
              title="Remove from selection"
            >
              <XIcon class="h-3 w-3" />
            </Button>
          </div>
        </div>

        <!-- Columns -->
        <div v-if="selectedAssetsGrouped.columns.length > 0">
          <p class="text-xs font-medium text-muted-foreground px-2 py-1 mt-2">Columns</p>
          <div
            v-for="column in selectedAssetsGrouped.columns"
            :key="column.id"
            class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-50 group"
          >
            <Columns3 class="h-4 w-4 text-primary-600 flex-shrink-0" />
            <span class="text-sm truncate flex-1">
              {{ column.column_facet?.parent_table_facet?.table_name }}.{{
                column.column_facet?.column_name
              }}
            </span>
            <Button
              variant="ghost"
              size="icon"
              class="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
              @click="catalogStore.toggleAssetSelection(column.id)"
              title="Remove from selection"
            >
              <XIcon class="h-3 w-3" />
            </Button>
          </div>
        </div>
      </div>

      <div
        class="px-4 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between gap-3"
      >
        <p class="text-xs text-muted-foreground">
          {{
            selectedAssets.length > 0
              ? 'Ready to review these assets with AI'
              : 'Select assets to start analysis'
          }}
        </p>
        <Button @click="analyzeSelected" size="sm" :disabled="selectedAssets.length === 0">
          <SparklesIcon class="h-4 w-4" />
          Analyze Selected
        </Button>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { useCatalogAssetsQuery } from '@/components/catalog/useCatalogQuery'
import { Button } from '@/components/ui/button'
import { useCatalogStore, type CatalogAsset } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { useConversationsStore } from '@/stores/conversations'
import { Columns3, Database, FolderTree, SparklesIcon, Table, XIcon } from 'lucide-vue-next'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const catalogStore = useCatalogStore()
const conversationsStore = useConversationsStore()
const contextsStore = useContextsStore()
const router = useRouter()

// Get assets from TanStack Query
const { data: assets } = useCatalogAssetsQuery()

function closeSelectionPanel() {
  catalogStore.clearSelection()
  catalogStore.selectionMode = false
}

// Compute selected assets based on selectedAssetIds
const selectedAssets = computed(() => {
  if (!assets.value) return []
  return assets.value.filter((asset) => catalogStore.selectedAssetIds.includes(asset.id))
})

// Group selected assets by type
const selectedAssetsGrouped = computed(() => {
  const databases: CatalogAsset[] = []
  const schemas: CatalogAsset[] = []
  const tables: CatalogAsset[] = []
  const columns: CatalogAsset[] = []
  selectedAssets.value.forEach((asset) => {
    if (asset.type === 'DATABASE') {
      databases.push(asset)
    } else if (asset.type === 'SCHEMA') {
      schemas.push(asset)
    } else if (asset.type === 'TABLE') {
      tables.push(asset)
    } else if (asset.type === 'COLUMN') {
      columns.push(asset)
    }
  })
  return { databases, schemas, tables, columns }
})

async function analyzeSelected() {
  const { databases, schemas, tables, columns } = selectedAssetsGrouped.value

  const databasesList = databases
    .map((d) => `- ${d.database_facet?.database_name || d.name} (id: ${d.id})`)
    .join('\n')
  const schemasList = schemas
    .map((s) => `- ${s.schema_facet?.database_name}.${s.schema_facet?.schema_name} (id: ${s.id})`)
    .join('\n')
  const tablesList = tables
    .map((t) => `- ${t.name || t.table_facet?.table_name} (id: ${t.id})`)
    .join('\n')
  const columnsList = columns
    .map(
      (c) =>
        `- ${c.column_facet?.parent_table_facet?.table_name}.${c.column_facet?.column_name} (id: ${c.id})`
    )
    .join('\n')

  const prompt = `Please review and help fill in descriptions for the following selected assets in our data catalog:

${databases.length > 0 ? `**Databases:**\n${databasesList}\n` : ''}
${schemas.length > 0 ? `**Schemas:**\n${schemasList}\n` : ''}
${tables.length > 0 ? `**Tables:**\n${tablesList}\n` : ''}
${columns.length > 0 ? `**Columns:**\n${columnsList}\n` : ''}

Before writing any asset descriptions, please:

1. **Perform a global business understanding check**:
   - Analyze the overall database structure and schema
   - Identify key business domains and data relationships
   - Understand the primary business processes reflected in the data

2. **Prioritize assets for description**:
   - Identify core tables and columns
   - Consider tables with the most relationships or references

3. **Write short and concise asset descriptions that include**:
   - Key relationships with other tables
   - Data freshness and update patterns if observable
   - Important business rules or constraints
   - Relevant tags based on business domain, data sensitivity, usage patterns, and data quality characteristics

Please start by exploring the database structure to understand our business context, then provide descriptions for the most important assets you identify. Focus on clarity and business value rather than technical implementation details.`

  if (!contextsStore.contextSelected) {
    console.error('No context selected')
    return
  }

  try {
    const newConversation = await conversationsStore.createConversation(
      contextsStore.contextSelected.id
    )

    await conversationsStore.sendMessage(newConversation.id, prompt, 'text')

    router.push({ name: 'ChatPage', params: { id: newConversation.id.toString() } })
    // Clear the cart and exit selection mode after analyzing
    catalogStore.clearSelection()
    catalogStore.selectionMode = false
  } catch (error) {
    console.error('Error creating conversation and sending message:', error)
  }
}
</script>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(100%);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(20px);
  opacity: 0;
}
</style>
