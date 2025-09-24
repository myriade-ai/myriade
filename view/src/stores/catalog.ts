import axios from '@/plugins/axios'
import { useContextsStore } from '@/stores/contexts'
import type { AxiosResponse } from 'axios'
import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

// Define catalog asset types
export interface CatalogAsset {
  id: string
  urn: string
  name: string | null
  description: string | null
  type: 'TABLE' | 'COLUMN'
  tags: string[] | null
  database_id: string
  created_by: string | null
  createdAt: string
  updatedAt: string
  validated: boolean
  table_facet?: TableFacet
  column_facet?: ColumnFacet
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
  privacy: Record<string, any> | null
}

export interface CatalogTerm {
  id: string
  name: string
  definition: string
  database_id: string
  synonyms: string[] | null
  business_domains: string[] | null
  validated: boolean
  createdAt: string
  updatedAt: string
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
  const parsing = ref(false)
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
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to fetch assets'
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
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to fetch terms'
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
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to create term'
      console.error('Error creating term:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function parseCatalog(contextId: string) {
    try {
      parsing.value = true
      error.value = null

      const response = await axios.post(`/api/catalogs/${contextId}/parse`)
      return response.data
    } catch (err: any) {
      const message =
        err.response?.data?.error || err.response?.data?.message || 'Failed to parse catalog'
      error.value = message
      console.error('Error parsing catalog:', err)
      throw err
    } finally {
      parsing.value = false
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
    parsing,
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
    parseCatalog,
    clearError
  }
})
