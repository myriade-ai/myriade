import axios from '@/plugins/axios'
import { socket } from '@/plugins/socket'
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

export const useCatalogStore = defineStore('catalog', () => {
  // ——————————————————————————————————————————————————
  // STATE
  // ——————————————————————————————————————————————————
  const assets = ref<Record<string, CatalogAsset>>({})
  const terms = ref<Record<string, CatalogTerm>>({})
  const tags = ref<Record<string, AssetTag>>({})
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

  // ——————————————————————————————————————————————————
  // REAL-TIME UPDATES VIA SOCKET.IO
  // ——————————————————————————————————————————————————

  // Setup Socket.IO listeners for real-time catalog updates
  const setupSocketListeners = () => {
    // Asset updated
    socket.on('catalog:asset:updated', (data: { asset: CatalogAsset; database_id: string }) => {
      const currentContext = contextsStore.contextSelected
      if (!currentContext) return

      // Extract database_id from context
      const contextDatabaseId = currentContext.id.startsWith('database-')
        ? currentContext.id.replace('database-', '')
        : currentContext.id.startsWith('project-')
          ? currentContext.database?.id
          : null

      // Only update if the event is for the current context's database
      if (contextDatabaseId === data.database_id) {
        assets.value[data.asset.id] = data.asset
      }
    })

    // Term created
    socket.on('catalog:term:created', (data: { term: CatalogTerm; database_id: string }) => {
      const currentContext = contextsStore.contextSelected
      if (!currentContext) return

      const contextDatabaseId = currentContext.id.startsWith('database-')
        ? currentContext.id.replace('database-', '')
        : currentContext.id.startsWith('project-')
          ? currentContext.database?.id
          : null

      if (contextDatabaseId === data.database_id) {
        terms.value[data.term.id] = data.term
      }
    })

    // Term updated
    socket.on('catalog:term:updated', (data: { term: CatalogTerm; database_id: string }) => {
      const currentContext = contextsStore.contextSelected
      if (!currentContext) return

      const contextDatabaseId = currentContext.id.startsWith('database-')
        ? currentContext.id.replace('database-', '')
        : currentContext.id.startsWith('project-')
          ? currentContext.database?.id
          : null

      if (contextDatabaseId === data.database_id) {
        terms.value[data.term.id] = data.term
      }
    })

    // Term deleted
    socket.on('catalog:term:deleted', (data: { term_id: string; database_id: string }) => {
      const currentContext = contextsStore.contextSelected
      if (!currentContext) return

      const contextDatabaseId = currentContext.id.startsWith('database-')
        ? currentContext.id.replace('database-', '')
        : currentContext.id.startsWith('project-')
          ? currentContext.database?.id
          : null

      if (contextDatabaseId === data.database_id) {
        delete terms.value[data.term_id]
      }
    })

    // Tag created
    socket.on('catalog:tag:created', (data: { tag: AssetTag; database_id: string }) => {
      const currentContext = contextsStore.contextSelected
      if (!currentContext) return

      const contextDatabaseId = currentContext.id.startsWith('database-')
        ? currentContext.id.replace('database-', '')
        : currentContext.id.startsWith('project-')
          ? currentContext.database?.id
          : null

      if (contextDatabaseId === data.database_id) {
        tags.value[data.tag.id] = data.tag
      }
    })

    // Tag updated
    socket.on('catalog:tag:updated', (data: { tag: AssetTag; database_id: string }) => {
      const currentContext = contextsStore.contextSelected
      if (!currentContext) return

      const contextDatabaseId = currentContext.id.startsWith('database-')
        ? currentContext.id.replace('database-', '')
        : currentContext.id.startsWith('project-')
          ? currentContext.database?.id
          : null

      if (contextDatabaseId === data.database_id) {
        tags.value[data.tag.id] = data.tag
      }
    })

    // Tag deleted
    socket.on('catalog:tag:deleted', (data: { tag_id: string; database_id: string }) => {
      const currentContext = contextsStore.contextSelected
      if (!currentContext) return

      const contextDatabaseId = currentContext.id.startsWith('database-')
        ? currentContext.id.replace('database-', '')
        : currentContext.id.startsWith('project-')
          ? currentContext.database?.id
          : null

      if (contextDatabaseId === data.database_id) {
        delete tags.value[data.tag_id]

        // Also remove this tag from all assets
        Object.values(assets.value).forEach((asset) => {
          if (asset.tags) {
            asset.tags = asset.tags.filter((tag) => tag.id !== data.tag_id)
          }
        })
      }
    })

    // Metadata synced - full catalog refresh needed
    socket.on(
      'catalog:metadata:synced',
      (data: { database_id: string; synced_count: number }) => {
        const currentContext = contextsStore.contextSelected
        if (!currentContext) return

        const contextDatabaseId = currentContext.id.startsWith('database-')
          ? currentContext.id.replace('database-', '')
          : currentContext.id.startsWith('project-')
            ? currentContext.database?.id
            : null

        if (contextDatabaseId === data.database_id) {
          // Clear and reload all catalog data
          assets.value = {}
          terms.value = {}

          // Refetch all data
          fetchAssets(currentContext.id)
          fetchTerms(currentContext.id)
          fetchTags(currentContext.id)
        }
      }
    )
  }

  // Initialize socket listeners
  setupSocketListeners()

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
    tagsArray,
    assetsByType,
    tableAssets,
    columnAssets,

    // actions
    fetchAssets,
    fetchTerms,
    fetchTags,
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
