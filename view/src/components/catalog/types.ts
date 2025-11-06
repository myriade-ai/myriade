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
