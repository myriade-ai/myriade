import type { AssetTag, CatalogAsset } from '@/stores/catalog'

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
  badges: AssetTag[]
  columns: ExplorerColumnNode[]
}

export interface ExplorerSchemaNode {
  key: string
  name: string | null
  tables: ExplorerTableNode[]
}
