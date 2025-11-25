import type { CatalogAsset } from '@/stores/catalog'
import { computed, type ComputedRef } from 'vue'

export interface OverallStats {
  total_assets: number // Total catalogable assets (tables, views, etc.) - excludes columns
  completion_percentage: number
  assets_validated: number
  assets_ai_generated: number
  assets_to_review: number
}

export interface SchemaStats {
  schema_name: string
  schema_asset_id: string
  table_count: number
  completion_percentage: number
}

export interface DatabaseStats {
  database_id: string
  database_name: string
  total_schemas: number
  total_tables: number
  total_columns: number
  completion_percentage: number
  last_updated: string | null
  schemas: SchemaStats[]
}

export interface DashboardStatsResponse {
  overall: OverallStats
  databases: DatabaseStats[]
}

/**
 * Compute dashboard statistics from catalog assets
 * Aggregates stats by database, schema, and overall completion
 *
 * @param assets - Array of catalog assets to compute stats from
 * @returns Computed dashboard statistics
 */
export function computeDashboardStats(
  assets: ComputedRef<CatalogAsset[] | undefined>
): ComputedRef<DashboardStatsResponse | undefined> {
  return computed(() => {
    const catalogAssets = assets.value
    if (!catalogAssets) {
      return undefined
    }

    // Filter out columns - they are NOT counted as "assets to catalog"
    const nonColumnAssets = catalogAssets.filter((asset) => asset.type !== 'COLUMN')

    // Overall stats
    let total_assets = 0
    let assets_validated = 0
    let assets_ai_generated = 0
    let assets_to_review = 0
    let assets_with_description = 0

    for (const asset of nonColumnAssets) {
      total_assets++

      if (asset.description) {
        assets_with_description++
      }

      if (asset.status === 'published') {
        assets_validated++
        assets_ai_generated++ // Count all published assets
      } else if (asset.status === 'draft') {
        assets_to_review++
      }
    }

    const completion_percentage =
      total_assets > 0 ? Math.round((assets_with_description / total_assets) * 1000) / 10 : 0

    // Group assets by database
    const databaseAssetsMap = new Map<string, CatalogAsset>()
    const schemaAssetsMap = new Map<string, CatalogAsset>()
    const tableAssetsMap = new Map<string, CatalogAsset[]>()
    const columnAssetsMap = new Map<string, number>()

    for (const asset of catalogAssets) {
      if (asset.type === 'DATABASE' && asset.database_facet) {
        databaseAssetsMap.set(asset.id, asset)
      } else if (asset.type === 'SCHEMA' && asset.schema_facet) {
        schemaAssetsMap.set(asset.id, asset)
      } else if (asset.type === 'TABLE' && asset.table_facet) {
        const parentSchemaId = asset.table_facet.parent_schema_asset_id
        if (parentSchemaId) {
          if (!tableAssetsMap.has(parentSchemaId)) {
            tableAssetsMap.set(parentSchemaId, [])
          }
          tableAssetsMap.get(parentSchemaId)!.push(asset)
        }
      } else if (asset.type === 'COLUMN' && asset.column_facet) {
        const parentTableId = asset.column_facet.parent_table_asset_id
        columnAssetsMap.set(parentTableId, (columnAssetsMap.get(parentTableId) || 0) + 1)
      }
    }

    // Build database stats
    const databases: DatabaseStats[] = []

    for (const [dbAssetId, dbAsset] of databaseAssetsMap.entries()) {
      const dbFacet = dbAsset.database_facet
      if (!dbFacet) continue

      // Find schemas for this database
      const schemasForDb = Array.from(schemaAssetsMap.values()).filter(
        (schema) => schema.schema_facet?.parent_database_asset_id === dbAssetId
      )

      const schemas: SchemaStats[] = []
      let total_tables = 0
      let total_tables_with_desc = 0
      let total_columns = 0

      for (const schemaAsset of schemasForDb) {
        const schemaFacet = schemaAsset.schema_facet
        if (!schemaFacet) continue

        const tablesForSchema = tableAssetsMap.get(schemaAsset.id) || []
        const table_count = tablesForSchema.length
        const tables_with_desc = tablesForSchema.filter((t) => t.description).length

        total_tables += table_count
        total_tables_with_desc += tables_with_desc

        // Count columns for this schema's tables
        const schema_columns = tablesForSchema.reduce(
          (sum, table) => sum + (columnAssetsMap.get(table.id) || 0),
          0
        )
        total_columns += schema_columns

        const schema_completion =
          table_count > 0 ? Math.round((tables_with_desc / table_count) * 1000) / 10 : 0

        schemas.push({
          schema_name: schemaFacet.schema_name,
          schema_asset_id: schemaAsset.id,
          table_count,
          completion_percentage: schema_completion
        })
      }

      // Sort schemas by name
      schemas.sort((a, b) => a.schema_name.localeCompare(b.schema_name))

      const db_completion =
        total_tables > 0 ? Math.round((total_tables_with_desc / total_tables) * 1000) / 10 : 0

      databases.push({
        database_id: dbAssetId,
        database_name: dbFacet.database_name,
        total_schemas: schemasForDb.length,
        total_tables,
        total_columns,
        completion_percentage: db_completion,
        last_updated: null,
        schemas
      })
    }

    return {
      overall: {
        total_assets,
        completion_percentage,
        assets_validated,
        assets_ai_generated,
        assets_to_review
      },
      databases
    }
  })
}
