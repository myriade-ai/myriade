<template>
  <Card class="bg-card rounded-lg gap-0 py-2 flex flex-col h-full">
    <CardHeader class="border-b-1 py-3">
      <CardTitle class="text-lg"> Database </CardTitle>
    </CardHeader>
    <CardContent class="px-0 flex-1 overflow-hidden flex flex-col">
      <div
        v-if="isLoading && explorerTree.length === 0"
        class="flex-1 overflow-y-auto p-4 space-y-3"
      >
        <div v-for="i in 5" :key="i" class="space-y-2">
          <div class="h-4 bg-muted/50 rounded animate-pulse w-full"></div>
          <div class="h-3 bg-muted/30 rounded animate-pulse w-3/4"></div>
        </div>
      </div>

      <UnifiedExplorer
        v-else
        ref="explorerRef"
        :tree="explorerTree"
        mode="editor"
        :selected-asset-id="null"
        :used-asset-ids="usedAssetIds"
        :show-search="true"
        :search-query="searchQuery"
        search-placeholder="Search tables..."
        :show-status-badge="false"
        :collapsed="false"
        :show-collapse-button="false"
        :show-header="false"
        empty-message="No tables available."
        :max-visible-columns="10"
        :expand-databases-by-default="true"
        @update:search-query="handleSearchUpdate"
        @quick-action="handleQuickAction"
      />
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import UnifiedExplorer from '@/components/catalog/UnifiedExplorer.vue'
import { useCatalogData } from '@/components/catalog/useCatalogData'
import { useCatalogAssetsQuery } from '@/components/catalog/useCatalogQuery'
import { Card, CardHeader, CardTitle } from '@/components/ui/card'
import CardContent from '@/components/ui/card/CardContent.vue'
import { useQueryEditor } from '@/composables/useQueryEditor'
import type { CatalogAsset } from '@/stores/catalog'
import { computed, ref } from 'vue'

const editor = useQueryEditor()
const searchQuery = ref('')

// Use the catalog query hook to fetch assets
const { data: catalogAssets, isLoading } = useCatalogAssetsQuery()

// Use catalog data composable to build tree
const { buildFilteredTree } = useCatalogData(computed(() => catalogAssets.value))

// Build the explorer tree, filtered by search query
const explorerTree = computed(() => {
  const tree = buildFilteredTree({
    selectedDatabase: '__all__',
    selectedSchema: '__all__',
    matchingIds: null
  })

  // If no search query, return tree as-is but sort by usage
  if (!searchQuery.value.trim()) {
    return sortTreeByUsage(tree)
  }

  // Filter tree by search query
  const query = searchQuery.value.toLowerCase().trim()
  return filterTreeBySearch(tree, query)
})

// Extract tables from SQL query to determine "used" tables
function extractTablesFromQuery(sqlQuery: string): Set<string> {
  const regex = /\b(FROM|JOIN|UPDATE|INTO)\s+("?\w+"?\."?\w+"?|"\w+"|\w+)/gi
  const tables = new Set<string>()

  let match
  while ((match = regex.exec(sqlQuery)) !== null) {
    if (match[2]) {
      tables.add(match[2].split('"').join('').toLowerCase())
    }
  }

  return tables
}

const extractedTableNames = computed(() => extractTablesFromQuery(editor.query.sql))

// Build set of used asset IDs based on table names in the query
const usedAssetIds = computed(() => {
  const ids = new Set<string>()
  const assets = catalogAssets.value || []

  for (const asset of assets) {
    if (asset.type !== 'TABLE') continue

    const tableName = asset.table_facet?.table_name || asset.name || ''
    const schemaName = asset.table_facet?.schema || ''
    const fullName = `${schemaName}.${tableName}`.toLowerCase()

    if (
      extractedTableNames.value.has(tableName.toLowerCase()) ||
      extractedTableNames.value.has(fullName)
    ) {
      ids.add(asset.id)
    }
  }

  return ids
})

// Sort tree to show used databases/schemas/tables first
function sortTreeByUsage(
  tree: ReturnType<typeof buildFilteredTree>
): ReturnType<typeof buildFilteredTree> {
  // Check if a database has any used tables
  const hasUsedTables = (db: (typeof tree)[0]) =>
    db.schemas.some((schema) =>
      schema.tables.some((table) => usedAssetIds.value.has(table.asset.id))
    )

  return tree
    .map((db) => ({
      ...db,
      schemas: db.schemas
        .map((schema) => ({
          ...schema,
          tables: [...schema.tables].sort((a, b) => {
            const aUsed = usedAssetIds.value.has(a.asset.id)
            const bUsed = usedAssetIds.value.has(b.asset.id)
            if (aUsed && !bUsed) return -1
            if (!aUsed && bUsed) return 1
            return 0
          })
        }))
        .sort((a, b) => {
          const aHasUsed = a.tables.some((t) => usedAssetIds.value.has(t.asset.id))
          const bHasUsed = b.tables.some((t) => usedAssetIds.value.has(t.asset.id))
          if (aHasUsed && !bHasUsed) return -1
          if (!aHasUsed && bHasUsed) return 1
          return 0
        })
    }))
    .sort((a, b) => {
      const aHasUsed = hasUsedTables(a)
      const bHasUsed = hasUsedTables(b)
      if (aHasUsed && !bHasUsed) return -1
      if (!aHasUsed && bHasUsed) return 1
      return 0
    })
}

// Filter tree by search query
function filterTreeBySearch(
  tree: ReturnType<typeof buildFilteredTree>,
  query: string
): ReturnType<typeof buildFilteredTree> {
  return tree
    .map((db) => {
      const dbMatches = db.name.toLowerCase().includes(query)

      const filteredSchemas = db.schemas
        .map((schema) => {
          const schemaMatches = (schema.name || '').toLowerCase().includes(query)

          const filteredTables = schema.tables.filter((table) => {
            const tableName = table.asset.table_facet?.table_name || table.asset.name || ''
            return tableName.toLowerCase().includes(query)
          })

          // Include schema if it matches, or if it has matching tables
          if (schemaMatches || filteredTables.length > 0) {
            return {
              ...schema,
              tables: schemaMatches ? schema.tables : filteredTables
            }
          }
          return null
        })
        .filter((s): s is NonNullable<typeof s> => s !== null)

      // Include database if it matches, or if it has matching schemas
      if (dbMatches || filteredSchemas.length > 0) {
        return {
          ...db,
          schemas: dbMatches ? db.schemas : filteredSchemas
        }
      }
      return null
    })
    .filter((db): db is NonNullable<typeof db> => db !== null)
}

function handleSearchUpdate(value: string) {
  searchQuery.value = value
}

function handleQuickAction(action: string, asset: CatalogAsset) {
  if (action === 'select-all' && asset.type === 'TABLE') {
    const tableFacet = asset.table_facet
    const databaseName = tableFacet?.database_name
    const schemaName = tableFacet?.schema
    const tableName = tableFacet?.table_name || asset.name

    let tableRef: string
    if (databaseName) {
      tableRef = `"${databaseName}"."${schemaName}"."${tableName}"`
    } else {
      tableRef = `"${schemaName}"."${tableName}"`
    }

    editor.query.sql = `SELECT * FROM ${tableRef};`
    searchQuery.value = ''
    editor.runQuery()
  }
}
</script>
