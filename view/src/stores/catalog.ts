import axios from '@/plugins/axios'
import { socket } from '@/plugins/socket'
import { useContextsStore } from '@/stores/contexts'
import type { CatalogAssetUpdatePayload, CatalogTermUpdatePayload } from '@/types/catalog'
import type { AxiosResponse } from 'axios'
import { useQueryClient } from '@tanstack/vue-query'
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
  table_type: string | null
  columns_total_count?: number | null
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
  // This store only manages terms, tags, and non-asset metadata
  const terms = ref<Record<string, CatalogTerm>>({})
  const tags = ref<Record<string, AssetTag>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Selection mode state
  const selectionMode = ref(false)
  const selectedAssetIds = ref<string[]>([])

  // Real-time synchronization state
  const currentRoom = ref<string | null>(null)
  const queryClient = useQueryClient()

  // Watch for context changes
  const contextsStore = useContextsStore()

  watch(
    () => contextsStore.contextSelected,
    (newContext, oldContext) => {
      if (newContext && newContext.id && newContext.id !== oldContext?.id) {
        // Leave old room if we were in one
        if (currentRoom.value && oldContext?.id) {
          socket.emit('catalog:leave', oldContext.id)
        }

        // Clear the catalog store
        terms.value = {}
        tags.value = {}
        error.value = null
        selectedAssetIds.value = []

        // Join new room for real-time updates
        if (newContext.id) {
          socket.emit('catalog:join', newContext.id)
          currentRoom.value = newContext.id
        }

        fetchTags(newContext.id)
      }
    },
    { immediate: true, deep: true }
  )

  // ——————————————————————————————————————————————————
  // GETTERS
  // ——————————————————————————————————————————————————

  const termsArray = computed(() => Object.values(terms.value))
  const tagsArray = computed(() => Object.values(tags.value))
  // ——————————————————————————————————————————————————
  // ACTIONS
  // ——————————————————————————————————————————————————

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

      // NOTE: No longer updating local store state
      // Caller should invalidate TanStack Query cache to refetch
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

      // NOTE: No longer updating local store state
      // Caller should invalidate TanStack Query cache to refetch
      return response.data
    } catch (err: unknown) {
      const errorResponse = err as any
      error.value = errorResponse?.response?.data?.message || 'Failed to dismiss flag'
      console.error('Error dismissing flag:', err)
      throw err
    }
  }

  // Selection mode actions
  function toggleSelectionMode() {
    selectionMode.value = !selectionMode.value
    if (!selectionMode.value) {
      // Clear selection when exiting selection mode
      selectedAssetIds.value = []
    }
  }

  function toggleAssetSelection(assetId: string) {
    const isSelected = selectedAssetIds.value.includes(assetId)

    if (isSelected) {
      // Deselect the asset
      selectedAssetIds.value = selectedAssetIds.value.filter((id) => id !== assetId)
    } else {
      // Select the asset
      selectedAssetIds.value = [...selectedAssetIds.value, assetId]
    }
  }

  function addAssetSelection(assetIds: string[]) {
    const newIds = assetIds.filter((id) => !selectedAssetIds.value.includes(id))
    selectedAssetIds.value = [...selectedAssetIds.value, ...newIds]
  }

  function removeAssetSelection(assetIds: string[]) {
    selectedAssetIds.value = selectedAssetIds.value.filter((id) => !assetIds.includes(id))
  }

  function clearSelection() {
    selectedAssetIds.value = []
  }

  function isAssetSelected(assetId: string): boolean {
    return selectedAssetIds.value.includes(assetId)
  }

  // ——————————————————————————————————————————————————
  // REAL-TIME EVENT HANDLERS
  // ——————————————————————————————————————————————————

  function setupRealtimeListeners() {
    socket.on(
      'catalog:asset:updated',
      (data: { asset: CatalogAsset; updated_by: string; timestamp: string }) => {
        const currentContextId = contextsStore.contextSelected?.id
        if (!currentContextId) return

        queryClient.setQueryData<CatalogAsset[]>(
          ['catalog', 'assets', currentContextId],
          (oldData) => {
            if (!oldData) return oldData

            return oldData.map((asset) => (asset.id === data.asset.id ? data.asset : asset))
          }
        )
      }
    )

    socket.on('catalog:tag:updated', (data: { tag: AssetTag; updated_by: string }) => {
      tags.value[data.tag.id] = data.tag

      const currentContextId = contextsStore.contextSelected?.id
      if (!currentContextId) return

      queryClient.setQueryData<CatalogAsset[]>(
        ['catalog', 'assets', currentContextId],
        (oldData) => {
          if (!oldData) return oldData

          return oldData.map((asset) => ({
            ...asset,
            tags: asset.tags.map((tag) => (tag.id === data.tag.id ? data.tag : tag))
          }))
        }
      )
    })

    // Tag deleted - remove from local state and assets
    socket.on('catalog:tag:deleted', (data: { tag_id: string; updated_by: string }) => {
      // Remove from local state
      delete tags.value[data.tag_id]

      // Update assets cache: remove this tag from all assets
      const currentContextId = contextsStore.contextSelected?.id
      if (!currentContextId) return

      queryClient.setQueryData<CatalogAsset[]>(
        ['catalog', 'assets', currentContextId],
        (oldData) => {
          if (!oldData) return oldData

          // Remove deleted tag from all assets
          return oldData.map((asset) => {
            const hasTag = asset.tags.some((tag) => tag.id === data.tag_id)
            if (!hasTag) return asset

            // Remove the deleted tag
            const newTags = asset.tags.filter((tag) => tag.id !== data.tag_id)
            return { ...asset, tags: newTags }
          })
        }
      )
    })

    // Sync completed - refetch all assets to get latest state
    socket.on('catalog:sync:completed', () => {
      const currentContextId = contextsStore.contextSelected?.id
      if (!currentContextId) return

      queryClient.invalidateQueries({
        queryKey: ['catalog', 'assets', currentContextId]
      })
    })

    // Room joined confirmation
    socket.on('catalog:joined', (data: { context_id: string; room: string }) => {
      currentRoom.value = data.context_id
    })

    // Room left confirmation
    socket.on('catalog:left', () => {
      currentRoom.value = null
    })

    // Error handling
    socket.on('catalog:error', (data: { message: string }) => {
      console.error('[Catalog] Socket error:', data.message)
      error.value = data.message
    })
  }

  setupRealtimeListeners()

  // ——————————————————————————————————————————————————
  // RETURN
  // ——————————————————————————————————————————————————
  return {
    // state
    terms,
    loading,
    error,
    selectionMode,
    selectedAssetIds,

    // getters
    termsArray,
    tagsArray,

    // actions
    fetchTerms,
    fetchTags,
    createTag,
    createTerm,
    updateAsset, // NOTE: Caller must invalidate TanStack Query cache
    updateTerm,
    deleteTerm,
    updateTag,
    deleteTag,
    dismissFlag, // NOTE: Caller must invalidate TanStack Query cache

    // selection actions
    toggleSelectionMode,
    toggleAssetSelection,
    addAssetSelection,
    removeAssetSelection,
    clearSelection,
    isAssetSelected
  }
})
