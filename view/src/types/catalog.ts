// Clean catalog types for REST API usage

export interface CatalogAssetUpdatePayload {
  description?: string | null
  tags?: string[] | null
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

// Simple term state interface for forms and components
export interface CatalogTermState {
  name: string
  definition: string
  synonyms: string[]
  business_domains: string[]
}
