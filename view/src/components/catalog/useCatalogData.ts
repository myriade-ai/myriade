import { useCatalogStore, type CatalogAsset } from '@/stores/catalog'
import { useDatabasesStore } from '@/stores/databases'
import { computed, type ComputedRef } from 'vue'
import type {
  ExplorerColumnNode,
  ExplorerDatabaseNode,
  ExplorerSchemaNode,
  ExplorerTableNode
} from './types'
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
  const databaseOptions = indexes.databaseOptions
  const schemaOptions = indexes.schemaOptions
  const tagOptions = computed(() => catalogStore.tagsArray)

  function assetDatabase(asset: CatalogAsset): string {
    if (asset.type === 'TABLE') {
      return asset.table_facet?.database_name || ''
    }
    if (asset.type === 'COLUMN') {
      return asset.column_facet?.parent_table_facet?.database_name || ''
    }
    return ''
  }

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
      selectedDatabase: string
      selectedSchema: string
      matchingIds?: Set<string> | null
    }
  ): boolean {
    const { selectedDatabase, selectedSchema, matchingIds } = options

    if (matchingIds && !matchingIds.has(asset.id)) {
      return false
    }

    if (
      selectedDatabase &&
      selectedDatabase !== '__all__' &&
      assetDatabase(asset) !== selectedDatabase
    ) {
      return false
    }

    if (selectedSchema && selectedSchema !== '__all__' && assetSchema(asset) !== selectedSchema) {
      return false
    }

    return true
  }

  function buildFilteredTree(options: {
    selectedDatabase: string
    selectedSchema: string
    matchingIds?: Set<string> | null
  }): ExplorerDatabaseNode[] {
    const { selectedDatabase, selectedSchema, matchingIds } = options
    const databaseMap = new Map<string, ExplorerDatabaseNode>()
    const schemaNodeByAssetId = new Map<
      string,
      { node: ExplorerSchemaNode; database: ExplorerDatabaseNode }
    >()

    // First, collect all database and schema assets
    const assets = assetsSource.value || []
    const databaseAssets = assets.filter((a) => a.type === 'DATABASE')
    const schemaAssets = assets.filter((a) => a.type === 'SCHEMA')

    const ensureDatabaseNode = (databaseName: string, databaseAsset?: CatalogAsset) => {
      const databaseKey = `database:${databaseName}`
      if (!databaseMap.has(databaseKey)) {
        databaseMap.set(databaseKey, {
          key: databaseKey,
          name: databaseName,
          asset: databaseAsset!,
          schemas: []
        })
      }
      return databaseMap.get(databaseKey)!
    }

    const ensureSchemaNode = (
      databaseNode: ExplorerDatabaseNode,
      schemaName: string | null,
      databaseName: string,
      schemaAsset?: CatalogAsset
    ) => {
      const schemaKey = `schema:${databaseName}:${schemaName || ''}`
      let schemaNode = databaseNode.schemas.find((s) => s.key === schemaKey)
      if (!schemaNode) {
        schemaNode = {
          key: schemaKey,
          name: schemaName,
          asset: schemaAsset,
          tables: []
        }
        databaseNode.schemas.push(schemaNode)
      }
      return schemaNode
    }

    // Create database nodes from database assets
    databaseAssets.forEach((dbAsset) => {
      const dbName = dbAsset.database_facet?.database_name || 'unknown'
      ensureDatabaseNode(dbName, dbAsset)
    })

    // Create schema nodes from schema assets and index them by asset ID
    schemaAssets.forEach((schemaAsset) => {
      const dbName = schemaAsset.schema_facet?.database_name || 'unknown'
      const schemaName = schemaAsset.schema_facet?.schema_name || ''
      const databaseAsset = databaseAssets.find((a) => a.database_facet?.database_name === dbName)
      const databaseNode = ensureDatabaseNode(dbName, databaseAsset)
      const schemaNode = ensureSchemaNode(databaseNode, schemaName, dbName, schemaAsset)

      // Index schema nodes by their asset ID for quick lookup
      schemaNodeByAssetId.set(schemaAsset.id, { node: schemaNode, database: databaseNode })
    })

    // Use indexed tables list to build table/column hierarchy
    indexes.tablesList.value
      .slice()
      .sort((a, b) => {
        const dbA = a.table_facet?.database_name || ''
        const dbB = b.table_facet?.database_name || ''
        if (dbA !== dbB) return dbA.localeCompare(dbB)
        const schemaA = a.table_facet?.schema || ''
        const schemaB = b.table_facet?.schema || ''
        if (schemaA !== schemaB) return schemaA.localeCompare(schemaB)
        return (a.name || a.table_facet?.table_name || '').localeCompare(
          b.name || b.table_facet?.table_name || ''
        )
      })
      .forEach((tableAsset) => {
        // Try to find schema using parent_schema_asset_id first (most reliable)
        const parentSchemaAssetId = tableAsset.table_facet?.parent_schema_asset_id
        let schemaLookup = parentSchemaAssetId ? schemaNodeByAssetId.get(parentSchemaAssetId) : null

        // Fallback to schema name matching if parent_schema_asset_id is not available
        if (!schemaLookup) {
          const dbName = tableAsset.table_facet?.database_name || 'unknown'
          const schemaName = tableAsset.table_facet?.schema || ''
          const databaseAsset = databaseAssets.find(
            (a) => a.database_facet?.database_name === dbName
          )
          const databaseNode = ensureDatabaseNode(dbName, databaseAsset)
          const schemaNode = ensureSchemaNode(databaseNode, schemaName, dbName)
          schemaLookup = { node: schemaNode, database: databaseNode }
        }

        const schemaNode = schemaLookup.node

        // For search filtering, check both table and its columns
        const columnAssets = columnsByTableId.value.get(tableAsset.id) || []
        const matchedColumns = columnAssets.filter((column) =>
          assetMatchesFilters(column, {
            selectedDatabase,
            selectedSchema,
            matchingIds
          })
        )
        const tableMatches = assetMatchesFilters(tableAsset, {
          selectedDatabase,
          selectedSchema,
          matchingIds
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

    const sorted = Array.from(databaseMap.values()).sort((a, b) => a.name.localeCompare(b.name))

    return sorted
  }

  return {
    databaseNameById,
    tableById,
    columnsByTableId,
    databaseOptions,
    schemaOptions,
    tagOptions,
    assetSchema,
    assetMatchesFilters,
    buildFilteredTree,
    // Expose indexes for advanced usage
    indexes
  }
}
