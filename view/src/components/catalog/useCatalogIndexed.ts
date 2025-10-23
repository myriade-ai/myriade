import type { CatalogAsset } from '@/stores/catalog'
import { computed, type ComputedRef } from 'vue'

/**
 * Optimized indexes for catalog assets
 * Provides O(1) lookups and pre-computed collections
 * Designed for handling large volumes (50k+ assets)
 */
export interface CatalogIndexes {
  // Primary index: O(1) lookup by asset ID
  assetsByIdMap: ComputedRef<Map<string, CatalogAsset>>

  // Secondary index: O(1) lookup by table ID
  tablesByIdMap: ComputedRef<Map<string, CatalogAsset>>

  // Relational index: O(1) lookup of columns by parent table ID
  columnsByTableIdMap: ComputedRef<Map<string, CatalogAsset[]>>

  // Business indexes
  tablesBySchemaMap: ComputedRef<Map<string, CatalogAsset[]>>
  assetsByStatusMap: ComputedRef<Map<string, CatalogAsset[]>>
  assetsByTagIdMap: ComputedRef<Map<string, CatalogAsset[]>>

  // Flat lists (avoids repeated Object.values() calls)
  tablesList: ComputedRef<CatalogAsset[]>
  columnsList: ComputedRef<CatalogAsset[]>

  // Filter options (deduplicated)
  schemaOptions: ComputedRef<string[]>
}

/**
 * Creates optimized indexes for catalog assets
 *
 * Benefits:
 * - Single pass through data to build all indexes
 * - Map-based lookups are O(1) vs O(n) array searches
 * - Pre-sorted collections reduce UI computation
 * - Computed reactivity only recalculates on source data change
 *
 * @param assets - Reactive source of catalog assets (typically from TanStack Query)
 * @returns Object containing all indexed collections
 */
export function useCatalogIndexed(assets: ComputedRef<CatalogAsset[] | undefined>): CatalogIndexes {
  // ========================================
  // PRIMARY INDEXES
  // ========================================

  /**
   * Index all assets by ID for O(1) lookup
   * Used for: Direct asset access, existence checks
   */
  const assetsByIdMap = computed(() => {
    const map = new Map<string, CatalogAsset>()
    if (!assets.value) return map

    for (const asset of assets.value) {
      map.set(asset.id, asset)
    }
    return map
  })

  // ========================================
  // TYPE SEPARATION
  // ========================================

  /**
   * Pre-filtered list of table assets
   * Avoids repeated type checks in UI components
   */
  const tablesList = computed(() => {
    if (!assets.value) return []
    return assets.value.filter((a) => a.type === 'TABLE')
  })

  /**
   * Pre-filtered list of column assets
   * Avoids repeated type checks in UI components
   */
  const columnsList = computed(() => {
    if (!assets.value) return []
    return assets.value.filter((a) => a.type === 'COLUMN')
  })

  // ========================================
  // SECONDARY INDEXES
  // ========================================

  /**
   * Index tables by ID for O(1) lookup
   * Used for: Finding parent table of a column
   */
  const tablesByIdMap = computed(() => {
    const map = new Map<string, CatalogAsset>()
    for (const table of tablesList.value) {
      map.set(table.id, table)
    }
    return map
  })

  // ========================================
  // RELATIONAL INDEXES
  // ========================================

  /**
   * Index columns by their parent table ID
   * Pre-sorted by ordinal position for correct display order
   * Used for: Displaying table details with columns
   */
  const columnsByTableIdMap = computed(() => {
    const map = new Map<string, CatalogAsset[]>()

    for (const column of columnsList.value) {
      const tableId = column.column_facet?.parent_table_asset_id
      if (!tableId) continue

      if (!map.has(tableId)) {
        map.set(tableId, [])
      }
      map.get(tableId)!.push(column)
    }

    // Sort columns by ordinal (one-time cost, cached in Map)
    for (const columns of map.values()) {
      columns.sort((a, b) => {
        const ordA = a.column_facet?.ordinal ?? Number.MAX_SAFE_INTEGER
        const ordB = b.column_facet?.ordinal ?? Number.MAX_SAFE_INTEGER
        if (ordA !== ordB) return ordA - ordB

        // Fallback to alphabetical if ordinals are equal
        return (a.column_facet?.column_name || '').localeCompare(b.column_facet?.column_name || '')
      })
    }

    return map
  })

  // ========================================
  // BUSINESS INDEXES
  // ========================================

  /**
   * Index tables by schema name
   * Used for: Schema-based filtering and grouping
   */
  const tablesBySchemaMap = computed(() => {
    const map = new Map<string, CatalogAsset[]>()

    for (const table of tablesList.value) {
      const schema = table.table_facet?.schema || ''
      if (!map.has(schema)) {
        map.set(schema, [])
      }
      map.get(schema)!.push(table)
    }

    return map
  })

  /**
   * Index all assets by status
   * Used for: Status-based filtering (needs_review, validated, etc.)
   */
  const assetsByStatusMap = computed(() => {
    const map = new Map<string, CatalogAsset[]>()
    if (!assets.value) return map

    for (const asset of assets.value) {
      const status = asset.status || 'null'
      if (!map.has(status)) {
        map.set(status, [])
      }
      map.get(status)!.push(asset)
    }

    return map
  })

  /**
   * Index all assets by tag ID
   * Used for: Tag-based filtering
   * Note: One asset can appear in multiple tag groups
   */
  const assetsByTagIdMap = computed(() => {
    const map = new Map<string, CatalogAsset[]>()
    if (!assets.value) return map

    for (const asset of assets.value) {
      if (!asset.tags) continue
      for (const tag of asset.tags) {
        if (!map.has(tag.id)) {
          map.set(tag.id, [])
        }
        map.get(tag.id)!.push(asset)
      }
    }

    return map
  })

  // ========================================
  // FILTER OPTIONS
  // ========================================

  /**
   * Deduplicated and sorted list of schema names
   * Used for: Schema filter dropdown
   */
  const schemaOptions = computed(() => {
    const schemas = new Set<string>()
    for (const table of tablesList.value) {
      const schema = table.table_facet?.schema || ''
      schemas.add(schema)
    }
    return Array.from(schemas).sort()
  })

  return {
    assetsByIdMap,
    tablesByIdMap,
    columnsByTableIdMap,
    tablesBySchemaMap,
    assetsByStatusMap,
    assetsByTagIdMap,
    tablesList,
    columnsList,
    schemaOptions
  }
}
