export type AssetStatus =
  | 'validated'
  | 'human_authored'
  | 'published_by_ai'
  | 'needs_review'
  | 'requires_validation'
  | null

export interface CatalogAssetUpdatePayload {
  description?: string | null
  tag_ids?: string[]
  name?: string | null
  status?: AssetStatus
  approve_suggestion?: boolean
  ai_suggestion?: string | null
  ai_flag_reason?: string | null
  ai_suggested_tags?: string[] | null
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
