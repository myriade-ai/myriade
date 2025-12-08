import type { AssetTag, CatalogAsset } from '@/stores/catalog'

export interface DatabaseFacet {
  asset_id: string
  database_id: string
  database_name: string
}

export interface SchemaFacet {
  asset_id: string
  database_id: string
  database_name: string
  schema_name: string
  parent_database_asset_id: string
}

export interface ExplorerColumnNode {
  asset: CatalogAsset
  label: string
  meta: string
}

export interface EditableDraft {
  description: string
  tags: AssetTag[]
}

export interface ExplorerTableNode {
  key: string
  asset: CatalogAsset
  columns: ExplorerColumnNode[]
}

export interface ExplorerSchemaNode {
  key: string
  name: string | null
  asset?: CatalogAsset
  tables: ExplorerTableNode[]
}

export interface ExplorerDatabaseNode {
  key: string
  name: string
  asset: CatalogAsset
  schemas: ExplorerSchemaNode[]
}

// ============================================
// Unified Explorer Types
// ============================================

/**
 * Explorer mode determines the primary interaction pattern
 * - browse: View hierarchy, select single asset to view details
 * - select: Multi-select with checkboxes for batch operations
 * - editor: Interact with SQL editor, quick actions available
 */
export type ExplorerMode = 'browse' | 'select' | 'editor'

/**
 * Asset status display configuration
 */
export interface AssetStatusInfo {
  label: string
  variant: 'default' | 'draft' | 'published' | 'ai-suggestion' | 'used'
  icon?: string
}

/**
 * Quick action configuration for editor mode
 */
export interface ExplorerQuickAction {
  id: string
  label: string
  icon: string
}

/**
 * Flat item for list view (used in editor mode or search results)
 */
export interface ExplorerFlatItem {
  id: string
  asset: CatalogAsset
  label: string
  sublabel?: string
  meta?: string
  columns?: ExplorerColumnNode[]
}
