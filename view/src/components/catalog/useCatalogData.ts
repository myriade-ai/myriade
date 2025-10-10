import { useCatalogStore, type CatalogAsset } from '@/stores/catalog'
import { useDatabasesStore } from '@/stores/databases'
import { computed } from 'vue'
import type { ExplorerSchemaNode, ExplorerTableNode } from './types'

export function useCatalogData() {
  const catalogStore = useCatalogStore()
  const databasesStore = useDatabasesStore()

  const databaseNameById = computed(() => {
    const map = new Map<string, string>()
    databasesStore.databases.forEach((db) => {
      map.set(db.id, db.name)
    })
    return map
  })

  const tableById = computed(() => {
    const map = new Map<string, CatalogAsset>()
    catalogStore.tableAssets.forEach((asset) => {
      map.set(asset.id, asset)
    })
    return map
  })

  const columnsByTableId = computed(() => {
    const map = new Map<string, CatalogAsset[]>()
    catalogStore.columnAssets.forEach((asset) => {
      const tableId = asset.column_facet?.parent_table_asset_id
      if (!tableId) return
      if (!map.has(tableId)) {
        map.set(tableId, [])
      }
      map.get(tableId)!.push(asset)
    })
    // Sort by ordinal when present
    for (const cols of map.values()) {
      cols.sort((a, b) => {
        const ordinalA = a.column_facet?.ordinal ?? Number.MAX_SAFE_INTEGER
        const ordinalB = b.column_facet?.ordinal ?? Number.MAX_SAFE_INTEGER
        if (ordinalA === ordinalB) {
          return (a.column_facet?.column_name || '').localeCompare(
            b.column_facet?.column_name || ''
          )
        }
        return ordinalA - ordinalB
      })
    }
    return map
  })

  const schemaOptions = computed(() => {
    const schemas = new Set<string>()
    catalogStore.tableAssets.forEach((asset) => {
      const schema = asset.table_facet?.schema || ''
      schemas.add(schema)
    })
    return Array.from(schemas).sort((a, b) => a.localeCompare(b))
  })

  const tagOptions = computed(() => catalogStore.tagsArray)

  function computeDocumentationScore(asset: CatalogAsset): number {
    const hasDescription = Boolean(asset.description?.trim().length)
    const hasTags = Boolean(asset.tags?.length)
    const isReviewed = Boolean(asset.reviewed)
    const score = (hasDescription ? 40 : 0) + (hasTags ? 30 : 0) + (isReviewed ? 30 : 0)
    return Math.min(100, score)
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
      searchQuery: string
      selectedSchema: string
      selectedTag: string
    }
  ): boolean {
    const { searchQuery, selectedSchema, selectedTag } = options

    if (selectedSchema && selectedSchema !== '__all__' && assetSchema(asset) !== selectedSchema) {
      return false
    }

    if (selectedTag && selectedTag !== '__all__') {
      const hasTag = asset.tags?.some((tag) => tag.id === selectedTag)
      if (!hasTag) return false
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
  }): ExplorerSchemaNode[] {
    const { searchQuery, selectedSchema, selectedTag } = options
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

    const searchActive = Boolean(searchQuery.trim())

    catalogStore.tableAssets
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
        const columnAssets = columnsByTableId.value.get(tableAsset.id) || []

        const matchedColumns = columnAssets.filter((column) =>
          assetMatchesFilters(column, { searchQuery, selectedSchema, selectedTag })
        )
        const tableMatches = assetMatchesFilters(tableAsset, {
          searchQuery,
          selectedSchema,
          selectedTag
        })

        if (!tableMatches && !matchedColumns.length) {
          return
        }

        const tableNode: ExplorerTableNode = {
          key: `table:${tableAsset.id}`,
          asset: tableAsset,
          badges: tableAsset.tags || [],
          columns: matchedColumns.map((column) => ({
            asset: column,
            label: column.column_facet?.column_name || column.name || 'Unnamed column',
            meta: column.column_facet?.data_type || '',
            score: computeDocumentationScore(column)
          }))
        }

        if (!matchedColumns.length && searchActive && tableMatches && columnAssets.length) {
          // When search matches table but not specific columns, show first few columns for context
          tableNode.columns = columnAssets.slice(0, 5).map((column) => ({
            asset: column,
            label: column.column_facet?.column_name || column.name || 'Unnamed column',
            meta: column.column_facet?.data_type || '',
            score: computeDocumentationScore(column)
          }))
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
    computeDocumentationScore,
    assetSchema,
    assetMatchesFilters,
    buildFilteredTree
  }
}
