export interface CatalogAssetUpdatePayload {
  description?: string | null
  tag_ids?: string[]
  name?: string | null
  reviewed?: boolean
}

export interface CatalogTermUpdatePayload {
  name?: string
  definition?: string
  synonyms?: string[]
  business_domains?: string[]
  reviewed?: boolean
}

export interface CatalogTermState {
  name: string
  definition: string
  synonyms: string[]
  business_domains: string[]
}
