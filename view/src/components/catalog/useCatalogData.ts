import { useCatalogStore, type CatalogAsset } from '@/stores/catalog'
import { useDatabasesStore } from '@/stores/databases'
import { computed, type ComputedRef } from 'vue'
import type { ExplorerColumnNode, ExplorerSchemaNode, ExplorerTableNode } from './types'
import { useCatalogIndexed } from './useCatalogIndexed'

/**
 * High-level composable for catalog data access
 * Provides indexes, filters, and business logic for catalog assets
 *
 * @param assetsSource - Reactive source of assets from TanStack Query (useCatalogAssetsQuery)
 */
export function useCatalogData(assetsSource: ComputedRef<CatalogAsset[] | undefined>) {
  const catalogStore = useCatalogStore()
  const databasesStore = useDatabasesStore()

  // Build optimized indexes from assets
  const indexes = useCatalogIndexed(assetsSource)

  const databaseNameById = computed(() => {
    const map = new Map<string, string>()
    databasesStore.databases.forEach((db) => {
      map.set(db.id, db.name)
    })
    return map
  })

  // Re-export indexes with existing names for backward compatibility
  const tableById = indexes.tablesByIdMap
  const columnsByTableId = indexes.columnsByTableIdMap
  const schemaOptions = indexes.schemaOptions
  const tagOptions = computed(() => catalogStore.tagsArray)

  function assetSchema(asset: CatalogAsset): string {
    if (asset.type === 'TABLE') {
      return asset.table_facet?.schema || ''
    }
    if (asset.type === 'COLUMN') {
      return asset.column_facet?.parent_table_facet?.schema || ''
    }
    return ''
  }

  function assetMatchesFilters(
    asset: CatalogAsset,
    options: {
      searchQuery: string
      selectedSchema: string
      selectedTag: string
      selectedStatus?: string
    }
  ): boolean {
    const { searchQuery, selectedSchema, selectedTag, selectedStatus } = options

    if (selectedSchema && selectedSchema !== '__all__' && assetSchema(asset) !== selectedSchema) {
      return false
    }

    if (selectedTag && selectedTag !== '__all__') {
      const hasTag = asset.tags?.some((tag) => tag.id === selectedTag)
      if (!hasTag) return false
    }

    if (selectedStatus && selectedStatus !== '__all__') {
      if (selectedStatus === 'unverified') {
        if (asset.status !== null) return false
      } else if (asset.status !== selectedStatus) {
        return false
      }
    }

    if (!searchQuery) {
      return true
    }

    const normalizedSearch = searchQuery.trim().toLowerCase()
    const targetParts: string[] = []
    if (asset.name) targetParts.push(asset.name)
    if (asset.description) targetParts.push(asset.description)
    if (asset.table_facet?.table_name) targetParts.push(asset.table_facet.table_name)
    if (asset.column_facet?.column_name) targetParts.push(asset.column_facet.column_name)
    if (asset.column_facet?.data_type) targetParts.push(asset.column_facet.data_type)
    if (asset.tags?.length) {
      targetParts.push(...asset.tags.map((tag) => tag.name))
    }

    return targetParts.some((value) => value.toLowerCase().includes(normalizedSearch))
  }

  function buildFilteredTree(options: {
    searchQuery: string
    selectedSchema: string
    selectedTag: string
    selectedStatus?: string
  }): ExplorerSchemaNode[] {
    const { searchQuery, selectedSchema, selectedTag, selectedStatus } = options
    const schemaMap = new Map<string, ExplorerSchemaNode>()

    const ensureSchemaNode = (schemaName: string | null) => {
      const schemaKey = `schema:${schemaName || ''}`
      if (!schemaMap.has(schemaKey)) {
        schemaMap.set(schemaKey, {
          key: schemaKey,
          name: schemaName,
          tables: []
        })
      }
      return schemaMap.get(schemaKey)!
    }

    // Use indexed tables list instead of catalogStore.tableAssets
    indexes.tablesList.value
      .slice()
      .sort((a, b) => {
        const schemaA = a.table_facet?.schema || ''
        const schemaB = b.table_facet?.schema || ''
        if (schemaA !== schemaB) return schemaA.localeCompare(schemaB)
        return (a.name || a.table_facet?.table_name || '').localeCompare(
          b.name || b.table_facet?.table_name || ''
        )
      })
      .forEach((tableAsset) => {
        const schemaNode = ensureSchemaNode(tableAsset.table_facet?.schema || '')

        // For search filtering, check both table and its columns
        const columnAssets = columnsByTableId.value.get(tableAsset.id) || []
        const matchedColumns = columnAssets.filter((column) =>
          assetMatchesFilters(column, { searchQuery, selectedSchema, selectedTag, selectedStatus })
        )
        const tableMatches = assetMatchesFilters(tableAsset, {
          searchQuery,
          selectedSchema,
          selectedTag,
          selectedStatus
        })

        // Only include table if it matches or has matching columns
        if (!tableMatches && !matchedColumns.length) {
          return
        }

        // Build column nodes with metadata
        const columnNodes: ExplorerColumnNode[] = matchedColumns.map((columnAsset) => ({
          asset: columnAsset,
          label: columnAsset.column_facet?.column_name || columnAsset.name || 'Unnamed column',
          meta: columnAsset.column_facet?.data_type || ''
        }))

        const tableNode: ExplorerTableNode = {
          key: `table:${tableAsset.id}`,
          asset: tableAsset,
          columns: columnNodes
        }

        schemaNode.tables.push(tableNode)
      })

    const sorted = Array.from(schemaMap.values()).sort((a, b) =>
      (a.name || '').localeCompare(b.name || '')
    )

    return sorted
  }

  return {
    databaseNameById,
    tableById,
    columnsByTableId,
    schemaOptions,
    tagOptions,
    assetSchema,
    assetMatchesFilters,
    buildFilteredTree,
    // Expose indexes for advanced usage
    indexes
  }
}
