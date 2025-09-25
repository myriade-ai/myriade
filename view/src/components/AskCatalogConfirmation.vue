<template>
  <div>
    <div class="flex-1 text-sm">
      <div class="flex mt-2 space-x-1">
        <component :is="statusIcon" class="w-5 h-5" :class="statusIconClass" />

        <p v-if="!isReviewed" class="text-yellow-700 mb-3">
          This catalog update needs your approval to be marked as reviewed.
        </p>

        <p v-else class="text-green-700 mb-3">Catalog update approved and marked as reviewed.</p>
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
        <div class="border rounded-lg p-4">
          <h3 class="font-semibold text-lg mb-2">{{ termData.name }}</h3>
          <p class="text-sm text-gray-600 mb-2">{{ termData.definition }}</p>
          <div v-if="termData.synonyms && termData.synonyms.length" class="mb-2">
            <span class="text-xs font-medium text-gray-500">Synonyms:</span>
            <div class="flex flex-wrap gap-1 mt-1">
              <span
                v-for="synonym in termData.synonyms"
                :key="synonym"
                class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
              >
                {{ synonym }}
              </span>
            </div>
          </div>
          <div v-if="termData.business_domains && termData.business_domains.length" class="mb-2">
            <span class="text-xs font-medium text-gray-500">Business Domains:</span>
            <div class="flex flex-wrap gap-1 mt-1">
              <span
                v-for="domain in termData.business_domains"
                :key="domain"
                class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded"
              >
                {{ domain }}
              </span>
            </div>
          </div>
          <div v-if="!isReviewed" class="mt-4">
            <Button
              variant="default"
              size="sm"
              :disabled="isProcessing"
              :is-loading="isProcessing"
              @click="handleTermApprove"
              class="text-green-600"
            >
              <template #loading>Approving...</template>
              Approve
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useCatalogStore } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AssetBase from './AssetBase.vue'
import { Button } from './ui/button'

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

// Determine if this is an asset or term operation based on available data
const assetData = computed(() => props.asset)
const termData = computed(() => props.term)

const isReviewed = computed(() => {
  if (assetData.value) return assetData.value.reviewed
  if (termData.value) return termData.value.reviewed
  return false
})

const statusIcon = computed(() => (isReviewed.value ? CheckCircleIcon : ExclamationTriangleIcon))
const statusIconClass = computed(() => (isReviewed.value ? 'text-green-500' : 'text-yellow-400'))

const handleAssetApprove = async (payload: { id: string; description: string; tags: string[] }) => {
  const contextId = contextsStore.contextSelected?.id
  if (!contextId || !assetData.value) {
    console.warn('Cannot approve asset without context or asset data')
    return
  }

  try {
    isProcessing.value = true
    await catalogStore.updateAsset(contextId, payload.id, {
      description: payload.description,
      tags: payload.tags,
      reviewed: true
    })
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
    await catalogStore.updateTerm(contextId, termData.value.id, {
      reviewed: true
    })
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
