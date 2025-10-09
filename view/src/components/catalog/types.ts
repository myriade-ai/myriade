import type { AssetTag, CatalogAsset } from '@/stores/catalog'

export interface ExplorerColumnNode {
  asset: CatalogAsset
  label: string
  meta: string
  privacyLabel: string
  score: number
}

export interface EditableDraft {
  description: string
  tags: AssetTag[]
  privacy: string
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
