import axios from '@/plugins/axios'
import { useContextsStore } from '@/stores/contexts'
import type { CatalogAssetUpdatePayload, CatalogTermUpdatePayload } from '@/types/catalog'
import type { AxiosResponse } from 'axios'
import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

export type AssetType = 'TABLE' | 'COLUMN'

export type Privacy = {
  llm: 'Encrypted' | 'Default'
}

export interface CatalogAsset {
  id: string
  urn: string
  name: string | null
  description: string | null
  type: AssetType
  tags: string[] | null
  database_id: string
  created_by: string | null
  createdAt: string
  updatedAt: string
  table_facet?: TableFacet
  column_facet?: ColumnFacet
  reviewed: boolean
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
  reviewed: boolean
}

export interface CatalogSearchResults {
  assets: CatalogAsset[]
  terms: CatalogTerm[]
}

export const useCatalogStore = defineStore('catalog', () => {
  // ——————————————————————————————————————————————————
  // STATE
  // ——————————————————————————————————————————————————
  const assets = ref<Record<string, CatalogAsset>>({})
  const terms = ref<Record<string, CatalogTerm>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Watch for context changes and fetch catalog data
  const contextsStore = useContextsStore()

  watch(
    () => contextsStore.contextSelected,
    (newContext, oldContext) => {
      if (newContext && newContext.id && newContext.id !== oldContext?.id) {
        // Clear the catalog store
        assets.value = {}
        terms.value = {}
        error.value = null
      }
    },
    { immediate: true, deep: true }
  )

  // ——————————————————————————————————————————————————
  // GETTERS
  // ——————————————————————————————————————————————————

  const assetsArray = computed(() => Object.values(assets.value))
  const termsArray = computed(() => Object.values(terms.value))

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

  async function updateAsset(
    contextId: string,
    assetId: string,
    updates: CatalogAssetUpdatePayload
  ) {
    try {
      error.value = null

      const response: AxiosResponse<CatalogAsset> = await axios.patch(
        `/api/catalogs/${contextId}/assets/${assetId}`,
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

  async function updateTerm(contextId: string, termId: string, updates: CatalogTermUpdatePayload) {
    try {
      error.value = null

      const response: AxiosResponse<CatalogTerm> = await axios.patch(
        `/api/catalogs/${contextId}/terms/${termId}`,
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

  function clearError() {
    error.value = null
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

    // getters
    assetsArray,
    termsArray,
    assetsByType,
    tableAssets,
    columnAssets,

    // actions
    fetchAssets,
    fetchTerms,
    createTerm,
    updateAsset,
    updateTerm,
    clearError
  }
})
