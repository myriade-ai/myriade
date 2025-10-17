import axios from '@/plugins/axios'
import { useContextsStore } from '@/stores/contexts'
import type { CatalogAssetUpdatePayload, CatalogTermUpdatePayload } from '@/types/catalog'
import type { AxiosResponse } from 'axios'
import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

export type AssetType = 'TABLE' | 'COLUMN'

export type AssetStatus =
  | 'validated'
  | 'human_authored'
  | 'published_by_ai'
  | 'needs_review'
  | 'requires_validation'
  | null

export type Privacy = {
  llm: 'Encrypted' | 'Default'
}

export interface AssetTag {
  id: string
  name: string
  description: string | null
  createdAt?: string
  updatedAt?: string
}

export interface CatalogAsset {
  id: string
  urn: string
  name: string | null
  description: string | null
  type: AssetType
  tags: AssetTag[]
  database_id: string
  created_by: string | null
  createdAt: string
  updatedAt: string
  table_facet?: TableFacet
  column_facet?: ColumnFacet
  status: AssetStatus
  ai_suggestion?: string | null
  ai_flag_reason?: string | null
  ai_suggested_tags?: string[] | null
}

export interface TableFacet {
  asset_id: string
  schema: string | null
  table_name: string | null
}

export interface ColumnFacet {
  asset_id: string
  parent_table_asset_id: string
  column_name: string
  ordinal: number | null
  data_type: string | null
  privacy?: Privacy
  parent_table_facet?: TableFacet
}

export interface CatalogTerm {
  id: string
  name: string
  definition: string
  database_id: string
  synonyms: string[] | null
  business_domains: string[] | null
  createdAt: string
  updatedAt: string
}

export interface CatalogStats {
  total_assets: number
  completion_score: number
  assets_to_review: number
  assets_validated: number
  assets_with_ai_suggestions: number
  assets_with_description: number
}

export const useCatalogStore = defineStore('catalog', () => {
  // ——————————————————————————————————————————————————
  // STATE
  // ——————————————————————————————————————————————————
  const assets = ref<Record<string, CatalogAsset>>({})
  const terms = ref<Record<string, CatalogTerm>>({})
  const tags = ref<Record<string, AssetTag>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)
  const stats = ref<CatalogStats | null>(null)

  // Watch for context changes and fetch catalog data
  const contextsStore = useContextsStore()

  watch(
    () => contextsStore.contextSelected,
    (newContext, oldContext) => {
      if (newContext && newContext.id && newContext.id !== oldContext?.id) {
        // Clear the catalog store
        assets.value = {}
        terms.value = {}
        tags.value = {}
        error.value = null

        fetchTags(newContext.id)
      }
    },
    { immediate: true, deep: true }
  )

  // ——————————————————————————————————————————————————
  // GETTERS
  // ——————————————————————————————————————————————————

  const assetsArray = computed(() => Object.values(assets.value))
  const termsArray = computed(() => Object.values(terms.value))
  const tagsArray = computed(() => Object.values(tags.value))

  const assetsByType = computed(() => {
    const grouped: Record<string, CatalogAsset[]> = {}
    assetsArray.value.forEach((asset) => {
      if (!grouped[asset.type]) {
        grouped[asset.type] = []
      }
      grouped[asset.type].push(asset)
    })
    return grouped
  })

  const tableAssets = computed(() => assetsByType.value.TABLE || [])
  const columnAssets = computed(() => assetsByType.value.COLUMN || [])

  // ——————————————————————————————————————————————————
  // ACTIONS
  // ——————————————————————————————————————————————————

  async function fetchAssets(contextId: string, type?: 'TABLE' | 'COLUMN') {
    try {
      loading.value = true
      error.value = null

      const params: Record<string, unknown> = {}
      if (type) params.type = type

      const response: AxiosResponse<CatalogAsset[]> = await axios.get(
        `/api/catalogs/${contextId}/assets`,
        {
          params
        }
      )

      if (contextsStore.contextSelected?.id !== contextId) {
        return []
      }

      // Update assets in store
      response.data.forEach((asset) => {
        assets.value[asset.id] = asset
      })

      return response.data
    } catch (err: unknown) {
      const errorResponse = err as any
      error.value = errorResponse?.response?.data?.message || 'Failed to fetch assets'
      console.error('Error fetching assets:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchTerms(contextId: string, limit: number = 50) {
    try {
      loading.value = true
      error.value = null

      const response: AxiosResponse<CatalogTerm[]> = await axios.get(
        `/api/catalogs/${contextId}/terms`,
        {
          params: { limit }
        }
      )

      if (contextsStore.contextSelected?.id !== contextId) {
        return []
      }

      // Update terms in store
      response.data.forEach((term) => {
        terms.value[term.id] = term
      })

      return response.data
    } catch (err: unknown) {
      const errorResponse = err as any
      error.value = errorResponse?.response?.data?.message || 'Failed to fetch terms'
      console.error('Error fetching terms:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  async function createTerm(
    contextId: string,
    termData: {
      name: string
      definition: string
      synonyms?: string[]
      business_domains?: string[]
    }
  ) {
    try {
      loading.value = true
      error.value = null

      const response: AxiosResponse<CatalogTerm> = await axios.post(
        `/api/catalogs/${contextId}/terms`,
        termData
      )

      terms.value[response.data.id] = response.data
      return response.data
    } catch (err: unknown) {
      const errorResponse = err as any
      error.value = errorResponse?.response?.data?.message || 'Failed to create term'
      console.error('Error creating term:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateAsset(assetId: string, updates: CatalogAssetUpdatePayload) {
    try {
      error.value = null

      const response: AxiosResponse<CatalogAsset> = await axios.patch(
        `/api/catalogs/assets/${assetId}`,
        updates
      )

      assets.value[response.data.id] = response.data
      return response.data
    } catch (err: unknown) {
      const errorResponse = err as any
      const message =
        errorResponse?.response?.data?.error ||
        errorResponse?.response?.data?.message ||
        'Failed to update asset'
      error.value = message
      console.error('Error updating asset:', err)
      throw err
    }
  }

  async function updateTerm(termId: string, updates: CatalogTermUpdatePayload) {
    try {
      error.value = null

      const response: AxiosResponse<CatalogTerm> = await axios.patch(
        `/api/catalogs/terms/${termId}`,
        updates
      )

      terms.value[response.data.id] = response.data
      return response.data
    } catch (err: unknown) {
      const errorResponse = err as any
      const message =
        errorResponse?.response?.data?.error ||
        errorResponse?.response?.data?.message ||
        'Failed to update term'
      error.value = message
      console.error('Error updating term:', err)
      throw err
    }
  }

  async function deleteTerm(termId: string) {
    try {
      error.value = null

      await axios.delete(`/api/catalogs/terms/${termId}`)

      delete terms.value[termId]
    } catch (err: unknown) {
      const errorResponse = err as any
      const message =
        errorResponse?.response?.data?.error ||
        errorResponse?.response?.data?.message ||
        'Failed to delete term'
      error.value = message
      console.error('Error deleting term:', err)
      throw err
    }
  }

  async function fetchTags(contextId: string) {
    try {
      loading.value = true
      error.value = null

      const response: AxiosResponse<AssetTag[]> = await axios.get(`/api/catalogs/${contextId}/tags`)

      if (contextsStore.contextSelected?.id !== contextId) {
        return []
      }

      // Update tags in store
      response.data.forEach((tag) => {
        tags.value[tag.id] = tag
      })

      return response.data
    } catch (err: unknown) {
      const errorResponse = err as any
      error.value = errorResponse?.response?.data?.message || 'Failed to fetch tags'
      console.error('Error fetching tags:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  async function createTag(
    contextId: string,
    tagData: {
      name: string
      description?: string
    }
  ) {
    try {
      error.value = null

      const response: AxiosResponse<AssetTag> = await axios.post(
        `/api/catalogs/${contextId}/tags`,
        tagData
      )

      tags.value[response.data.id] = response.data
      return response.data
    } catch (err: unknown) {
      const errorResponse = err as any
      error.value = errorResponse?.response?.data?.message || 'Failed to create tag'
      console.error('Error creating tag:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateTag(
    tagId: string,
    updates: {
      name?: string
      description?: string
    }
  ) {
    try {
      error.value = null

      const response: AxiosResponse<AssetTag> = await axios.patch(
        `/api/catalogs/tags/${tagId}`,
        updates
      )

      tags.value[response.data.id] = response.data
      return response.data
    } catch (err: unknown) {
      const errorResponse = err as any
      const message =
        errorResponse?.response?.data?.error ||
        errorResponse?.response?.data?.message ||
        'Failed to update tag'
      error.value = message
      console.error('Error updating tag:', err)
      throw err
    }
  }

  async function deleteTag(tagId: string) {
    try {
      error.value = null

      await axios.delete(`/api/catalogs/tags/${tagId}`)

      delete tags.value[tagId]
      return true
    } catch (err: unknown) {
      const errorResponse = err as any
      error.value = errorResponse?.response?.data?.message || 'Failed to delete tag'
      console.error('Error deleting tag:', err)
      throw err
    }
  }

  async function dismissFlag(assetId: string) {
    try {
      error.value = null

      const response: AxiosResponse<CatalogAsset> = await axios.patch(
        `/api/catalogs/assets/${assetId}`,
        {
          dismiss_flag: true
        }
      )

      assets.value[response.data.id] = response.data
      return response.data
    } catch (err: unknown) {
      const errorResponse = err as any
      error.value = errorResponse?.response?.data?.message || 'Failed to dismiss flag'
      console.error('Error dismissing flag:', err)
      throw err
    }
  }

  async function fetchStats(contextId: string) {
    try {
      loading.value = true
      error.value = null

      const response: AxiosResponse<CatalogStats> = await axios.get(
        `/api/catalogs/${contextId}/stats`
      )

      if (contextsStore.contextSelected?.id !== contextId) {
        return null
      }

      stats.value = response.data
      return response.data
    } catch (err: unknown) {
      const errorResponse = err as any
      error.value = errorResponse?.response?.data?.message || 'Failed to fetch stats'
      console.error('Error fetching stats:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  // ——————————————————————————————————————————————————
  // RETURN
  // ——————————————————————————————————————————————————
  return {
    // state
    assets,
    terms,
    loading,
    error,
    stats,

    // getters
    assetsArray,
    termsArray,
    tagsArray,
    assetsByType,
    tableAssets,
    columnAssets,

    // actions
    fetchAssets,
    fetchTerms,
    fetchTags,
    fetchStats,
    createTag,
    createTerm,
    updateAsset,
    updateTerm,
    deleteTerm,
    updateTag,
    deleteTag,
    dismissFlag
  }
})
