<template>
  <div>
    <div class="flex-1 text-sm">
      <div class="flex mt-2 space-x-1" v-if="formattedAssetData || termData">
        <component :is="statusIcon" class="w-5 h-5" :class="statusIconClass" />

        <p v-if="!isReviewed" class="text-yellow-700 mb-3">
          This catalog update needs your approval to be marked as reviewed.
        </p>

        <p v-else-if="isReviewed" class="text-green-700 mb-3">
          Catalog update approved and marked as reviewed.
        </p>
      </div>

      <!-- Asset Display -->
      <div v-if="formattedAssetData" class="space-y-3">
        <AssetBase
          :asset="formattedAssetData"
          mode="approval"
          :disable-editing="isReviewed"
          :show-approve="!isReviewed"
          :is-processing="isProcessing"
          @approve="handleAssetApprove"
          @navigate-to-catalog="handleNavigateToCatalog"
        />
      </div>

      <!-- Term Display -->
      <div v-else-if="termData" class="space-y-3">
        <TermBase
          v-model="editableTermData"
          :is-editable="!isReviewed"
          :is-processing="isProcessing"
          @approve="handleTermApprove"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useCatalogStore } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import type { CatalogTermState } from '@/types/catalog'
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AssetBase from './AssetBase.vue'
import TermBase from './TermBase.vue'

const props = defineProps<{
  functionCall?: {
    name: string
    arguments: Record<string, any>
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
    reviewed: boolean
  }
  term?: {
    id: string
    name: string
    definition: string
    synonyms?: string[] | null
    business_domains?: string[] | null
    reviewed: boolean
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

  const fullAsset = catalogStore.assets[assetData.value.id]

  // Extract schema and tableName from facets
  let schema: string | null = null
  let tableName: string | null = null

  if (fullAsset) {
    if (assetData.value.type === 'TABLE' && fullAsset.table_facet) {
      schema = fullAsset.table_facet.schema
      tableName = fullAsset.table_facet.table_name
    } else if (assetData.value.type === 'COLUMN' && fullAsset.column_facet) {
      schema = fullAsset.column_facet.parent_table_facet?.schema ?? null
      tableName = fullAsset.column_facet.parent_table_facet?.table_name ?? null
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
        business_domains: [],
        reviewed: false
      }
    }
    return {
      id: termData.value.id,
      name: termData.value.name,
      definition: termData.value.definition,
      synonyms: termData.value.synonyms || [],
      business_domains: termData.value.business_domains || [],
      reviewed: termData.value.reviewed
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

const isReviewed = computed(() => {
  if (assetData.value) return assetData.value.reviewed
  if (termData.value) return termData.value.reviewed
  return false
})

const statusIcon = computed(() => (isReviewed.value ? CheckCircleIcon : ExclamationTriangleIcon))
const statusIconClass = computed(() => (isReviewed.value ? 'text-green-500' : 'text-yellow-400'))

const handleAssetApprove = async (payload: {
  id: string
  description: string
  tag_ids: string[]
}) => {
  const contextId = contextsStore.contextSelected?.id
  if (!contextId || !assetData.value) {
    console.warn('Cannot approve asset without context or asset data')
    return
  }

  try {
    isProcessing.value = true
    await catalogStore.updateAsset(payload.id, {
      description: payload.description,
      tag_ids: payload.tag_ids,
      reviewed: true
    })

    // Update local asset data to reflect the approval
    if (assetData.value) {
      assetData.value.reviewed = true
      assetData.value.description = payload.description
      // Fetch the updated asset to get the full tag objects
      const updatedAsset = catalogStore.assets[payload.id]
      if (updatedAsset) {
        assetData.value.tags = updatedAsset.tags
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
      business_domains: currentTermData.business_domains,
      reviewed: true
    })

    if (termData.value) {
      termData.value.definition = currentTermData.definition
      termData.value.synonyms = currentTermData.synonyms
      termData.value.business_domains = currentTermData.business_domains
      termData.value.reviewed = true
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
    name: 'CatalogPage',
    query: { assetId }
  })
}
</script>
