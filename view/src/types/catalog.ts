export type AssetStatus = 'draft' | 'published' | null

export interface CatalogAssetUpdatePayload {
  description?: string | null
  tag_ids?: string[]
  name?: string | null
  status?: AssetStatus
  approve_suggestion?: boolean
  ai_suggestion?: string | null
  note?: string | null
  ai_suggested_tags?: string[] | null
  published_by?: string | null
  published_at?: string | null
}

export interface CatalogTermUpdatePayload {
  name?: string
  definition?: string
  synonyms?: string[]
  business_domains?: string[]
}

export interface CatalogTermState {
  name: string
  definition: string
  synonyms: string[]
  business_domains: string[]
}
