<template>
  <div>
    <div class="flex-1 text-sm">
      <!-- Asset Display -->
      <div v-if="formattedAssetData" class="space-y-3">
        <AssetBase
          :asset="formattedAssetData"
          :is-processing="isProcessing"
          @save="handleAssetSave"
          @publish="handleAssetPublish"
          @navigate-to-catalog="handleNavigateToCatalog"
          @approve-description="handleApproveDescription"
          @approve-tags="handleApproveTags"
          @reject-description="handleRejectDescription"
          @reject-tags="handleRejectTags"
        />
      </div>

      <!-- Term Display -->
      <div v-else-if="termData" class="space-y-3">
        <TermBase
          v-model="editableTermData"
          :is-editable="true"
          :is-processing="isProcessing"
          @approve="handleTermApprove"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useCatalogStore, type AssetStatus, type CatalogAsset } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import type { CatalogTermState } from '@/types/catalog'
import { useQueryClient } from '@tanstack/vue-query'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AssetBase from './AssetBase.vue'
import TermBase from './TermBase.vue'

const props = defineProps<{
  functionCall?: {
    name: string
    arguments: Record<string, unknown>
  }
  asset?: {
    id: string
    name: string
    description?: string | null
    tags?: Array<{
      id: string
      name: string
      description: string | null
    }>
    type: 'TABLE' | 'COLUMN'
    status?: AssetStatus
    ai_suggestion?: string | null
    note?: string | null
    ai_suggested_tags?: string[] | null
    published_by?: string | null
    published_at?: string | null
  }
  term?: {
    id: string
    name: string
    definition: string
    synonyms?: string[] | null
    business_domains?: string[] | null
  }
}>()

const router = useRouter()
const catalogStore = useCatalogStore()
const contextsStore = useContextsStore()
const queryClient = useQueryClient()
const isProcessing = ref(false)

const assetData = computed(() => props.asset)
const termData = computed(() => props.term)

const formattedAssetData = computed(() => {
  if (!assetData.value) return undefined

  // Extract schema and tableName from facets
  let schema: string | null = null
  let tableName: string | null = null

  // First try to get from the asset prop itself (from backend message)
  const asset = assetData.value as {
    table_facet?: { schema?: string; table_name?: string }
    column_facet?: {
      parent_table_facet?: { schema?: string; table_name?: string }
    }
  }

  if (assetData.value.type === 'TABLE' && asset.table_facet) {
    schema = asset.table_facet.schema ?? null
    tableName = asset.table_facet.table_name ?? null
  } else if (assetData.value.type === 'COLUMN' && asset.column_facet) {
    schema = asset.column_facet.parent_table_facet?.schema ?? null
    tableName = asset.column_facet.parent_table_facet?.table_name ?? null
  }

  return {
    ...assetData.value,
    tags: assetData.value.tags || [],
    schema,
    tableName
  }
})

const editableTermData = computed<CatalogTermState>({
  get: () => {
    if (!termData.value) {
      return {
        id: '',
        name: '',
        definition: '',
        synonyms: [],
        business_domains: []
      }
    }
    return {
      id: termData.value.id,
      name: termData.value.name,
      definition: termData.value.definition,
      synonyms: termData.value.synonyms || [],
      business_domains: termData.value.business_domains || []
    }
  },
  set: (value: CatalogTermState) => {
    if (termData.value) {
      termData.value.definition = value.definition
      termData.value.synonyms = value.synonyms
      termData.value.business_domains = value.business_domains
    }
  }
})

const handleAssetSave = async (payload: { id: string; description: string; tag_ids: string[] }) => {
  const contextId = contextsStore.contextSelected?.id
  if (!contextId || !assetData.value) {
    console.warn('Cannot save asset without context or asset data')
    return
  }

  try {
    isProcessing.value = true

    const updated = await catalogStore.updateAsset(payload.id, {
      description: payload.description,
      tag_ids: payload.tag_ids
    })

    // Update the query cache directly instead of refetching
    const queryKey = ['catalog', 'assets', contextsStore.contextSelected?.id]
    queryClient.setQueryData(queryKey, (oldData: CatalogAsset[] | undefined) => {
      if (!oldData) return oldData
      return oldData.map((a) => {
        if (a.id === updated.id) {
          return { ...a, ...updated }
        }
        return a
      })
    })

    // Update local asset data
    if (assetData.value) {
      assetData.value.description = updated.description
      assetData.value.status = updated.status
    }
  } catch (error) {
    console.error('Failed to save asset:', error)
  } finally {
    isProcessing.value = false
  }
}

const handleTermApprove = async () => {
  const contextId = contextsStore.contextSelected?.id
  if (!contextId || !termData.value) {
    console.warn('Cannot approve term without context or term data')
    return
  }

  try {
    isProcessing.value = true
    const currentTermData = editableTermData.value
    await catalogStore.updateTerm(termData.value.id, {
      definition: currentTermData.definition,
      synonyms: currentTermData.synonyms,
      business_domains: currentTermData.business_domains
    })

    if (termData.value) {
      termData.value.definition = currentTermData.definition
      termData.value.synonyms = currentTermData.synonyms
      termData.value.business_domains = currentTermData.business_domains
    }
  } catch (error) {
    console.error('Failed to approve term:', error)
  } finally {
    isProcessing.value = false
  }
}

const handleAssetPublish = async (payload: { id: string }) => {
  const contextId = contextsStore.contextSelected?.id
  if (!contextId || !assetData.value) {
    console.warn('Cannot publish asset without context or asset data')
    return
  }

  try {
    isProcessing.value = true
    const updated = await catalogStore.publishAsset(payload.id)

    // Update the query cache directly for optimistic update
    const queryKey = ['catalog', 'assets', contextsStore.contextSelected?.id]
    queryClient.setQueryData(queryKey, (oldData: CatalogAsset[] | undefined) => {
      if (!oldData) return oldData
      return oldData.map((a) => {
        if (a.id === updated.id) {
          return { ...a, ...updated }
        }
        return a
      })
    })

    // Update local asset data for immediate UI update
    if (assetData.value) {
      assetData.value.status = updated.status
      assetData.value.published_by = updated.published_by
      assetData.value.published_at = updated.published_at
    }
  } catch (error) {
    console.error('Failed to publish asset:', error)
  } finally {
    isProcessing.value = false
  }
}

const handleNavigateToCatalog = (payload: { id: string }) => {
  const assetId = payload?.id
  if (!assetId) return

  void router.push({
    name: 'AssetPage',
    query: { assetId }
  })
}

const handleApproveDescription = async (payload: { id: string; description: string }) => {
  const contextId = contextsStore.contextSelected?.id
  if (!contextId || !assetData.value) {
    console.warn('Cannot approve description without context or asset data')
    return
  }

  try {
    isProcessing.value = true

    const updated = await catalogStore.updateAsset(payload.id, {
      description: payload.description,
      ai_suggestion: null
      // Keep ai_suggested_tags if they exist
    })

    // Update the query cache directly
    const queryKey = ['catalog', 'assets', contextsStore.contextSelected?.id]
    queryClient.setQueryData(queryKey, (oldData: CatalogAsset[] | undefined) => {
      if (!oldData) return oldData
      return oldData.map((a) => (a.id === updated.id ? updated : a))
    })

    // Update local asset data
    if (assetData.value) {
      assetData.value.description = updated.description
      assetData.value.ai_suggestion = null
    }
  } catch (error) {
    console.error('Failed to approve description:', error)
  } finally {
    isProcessing.value = false
  }
}

const handleApproveTags = async (payload: { id: string; tag_ids: string[] }) => {
  const contextId = contextsStore.contextSelected?.id
  if (!contextId || !assetData.value) {
    console.warn('Cannot approve tags without context or asset data')
    return
  }

  try {
    isProcessing.value = true

    const updated = await catalogStore.updateAsset(payload.id, {
      tag_ids: payload.tag_ids,
      ai_suggested_tags: null
      // Keep ai_suggestion if it exists
    })

    // Update the query cache directly
    const queryKey = ['catalog', 'assets', contextsStore.contextSelected?.id]
    queryClient.setQueryData(queryKey, (oldData: CatalogAsset[] | undefined) => {
      if (!oldData) return oldData
      return oldData.map((a) => (a.id === updated.id ? updated : a))
    })

    // Update local asset data
    if (assetData.value) {
      assetData.value.tags = updated.tags
      assetData.value.ai_suggested_tags = null
    }
  } catch (error) {
    console.error('Failed to approve tags:', error)
  } finally {
    isProcessing.value = false
  }
}

const handleRejectDescription = async (payload: { id: string }) => {
  const contextId = contextsStore.contextSelected?.id
  if (!contextId || !assetData.value) {
    console.warn('Cannot reject description without context or asset data')
    return
  }

  try {
    isProcessing.value = true

    const updated = await catalogStore.updateAsset(payload.id, {
      ai_suggestion: null
      // Keep description and ai_suggested_tags unchanged
    })

    // Update the query cache directly
    const queryKey = ['catalog', 'assets', contextsStore.contextSelected?.id]
    queryClient.setQueryData(queryKey, (oldData: CatalogAsset[] | undefined) => {
      if (!oldData) return oldData
      return oldData.map((a) => (a.id === updated.id ? updated : a))
    })

    // Update local asset data
    if (assetData.value) {
      assetData.value.ai_suggestion = null
    }
  } catch (error) {
    console.error('Failed to reject description:', error)
  } finally {
    isProcessing.value = false
  }
}

const handleRejectTags = async (payload: { id: string }) => {
  const contextId = contextsStore.contextSelected?.id
  if (!contextId || !assetData.value) {
    console.warn('Cannot reject tags without context or asset data')
    return
  }

  try {
    isProcessing.value = true

    const updated = await catalogStore.updateAsset(payload.id, {
      ai_suggested_tags: null
      // Keep tags and ai_suggestion unchanged
    })

    // Update the query cache directly
    const queryKey = ['catalog', 'assets', contextsStore.contextSelected?.id]
    queryClient.setQueryData(queryKey, (oldData: CatalogAsset[] | undefined) => {
      if (!oldData) return oldData
      return oldData.map((a) => (a.id === updated.id ? updated : a))
    })

    // Update local asset data
    if (assetData.value) {
      assetData.value.ai_suggested_tags = null
    }
  } catch (error) {
    console.error('Failed to reject tags:', error)
  } finally {
    isProcessing.value = false
  }
}
</script>
