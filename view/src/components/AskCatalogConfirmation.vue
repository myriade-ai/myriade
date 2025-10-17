<template>
  <div>
    <div class="flex-1 text-sm">
      <!-- Asset Display -->
      <div v-if="formattedAssetData" class="space-y-3">
        <AssetBase
          :asset="formattedAssetData"
          :is-processing="isProcessing"
          @approve="handleAssetApprove"
          @navigate-to-catalog="handleNavigateToCatalog"
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
import { useCatalogStore, type AssetStatus } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import type { CatalogTermState } from '@/types/catalog'
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
    ai_flag_reason?: string | null
    ai_suggested_tags?: string[] | null
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

  // Fallback to catalog store if not found in prop
  if (!schema && !tableName) {
    const fullAsset = catalogStore.assets[assetData.value.id]
    if (fullAsset) {
      if (assetData.value.type === 'TABLE' && fullAsset.table_facet) {
        schema = fullAsset.table_facet.schema
        tableName = fullAsset.table_facet.table_name
      } else if (assetData.value.type === 'COLUMN' && fullAsset.column_facet) {
        schema = fullAsset.column_facet.parent_table_facet?.schema ?? null
        tableName = fullAsset.column_facet.parent_table_facet?.table_name ?? null
      }
    }
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

const handleAssetApprove = async (payload: {
  id: string
  description: string
  tag_ids: string[]
  approve_suggestion?: boolean
  ai_suggestion?: null
  ai_flag_reason?: null
  ai_suggested_tags?: null
}) => {
  const contextId = contextsStore.contextSelected?.id
  if (!contextId || !assetData.value) {
    console.warn('Cannot approve asset without context or asset data')
    return
  }

  try {
    isProcessing.value = true

    // Forward the payload to the catalog store
    // If the payload includes ai_suggestion/ai_flag_reason/ai_suggested_tags as null, they will be cleared
    await catalogStore.updateAsset(payload.id, {
      description: payload.description,
      tag_ids: payload.tag_ids,
      ...(payload.approve_suggestion !== undefined && {
        approve_suggestion: payload.approve_suggestion
      }),
      ...(payload.ai_suggestion !== undefined && { ai_suggestion: payload.ai_suggestion }),
      ...(payload.ai_flag_reason !== undefined && { ai_flag_reason: payload.ai_flag_reason }),
      ...(payload.ai_suggested_tags !== undefined && {
        ai_suggested_tags: payload.ai_suggested_tags
      })
    })

    // Update local asset data
    if (assetData.value) {
      assetData.value.description = payload.description
      // Fetch the updated asset to get the full tag objects and status
      const updatedAsset = catalogStore.assets[payload.id]
      if (updatedAsset) {
        assetData.value.tags = updatedAsset.tags
        assetData.value.status = updatedAsset.status
        assetData.value.ai_suggestion = updatedAsset.ai_suggestion
        assetData.value.ai_flag_reason = updatedAsset.ai_flag_reason
        assetData.value.ai_suggested_tags = updatedAsset.ai_suggested_tags
      }
    }
  } catch (error) {
    console.error('Failed to approve asset:', error)
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

const handleNavigateToCatalog = (payload: { id: string }) => {
  const assetId = payload?.id
  if (!assetId) return

  void router.push({
    name: 'AssetPage',
    query: { assetId }
  })
}
</script>
