<template>
  <div>
    <div class="flex-1 text-sm">
      <div class="flex mt-2 space-x-1" v-if="assetData || termData">
        <component :is="statusIcon" class="w-5 h-5" :class="statusIconClass" />

        <p v-if="!isReviewed" class="text-yellow-700 mb-3">
          This catalog update needs your approval to be marked as reviewed.
        </p>

        <p v-else-if="isReviewed" class="text-green-700 mb-3">
          Catalog update approved and marked as reviewed.
        </p>
      </div>

      <!-- Asset Display -->
      <div v-if="assetData" class="space-y-3">
        <AssetBase
          :asset="assetData"
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
    tags?: string[] | null
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
  tags: string[] | null
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
      tags: payload.tags,
      reviewed: true
    })

    // Update local asset data to reflect the approval
    if (assetData.value) {
      assetData.value.reviewed = true
      assetData.value.description = payload.description
      assetData.value.tags = payload.tags
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
