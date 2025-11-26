<template>
  <div class="bg-green-50 border border-green-200 rounded-lg p-4 my-3">
    <div class="flex items-start">
      <CheckCircleIcon class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />

      <div class="flex-1">
        <h4 class="text-sm font-medium text-green-800 mb-2">Message Posted to Asset Feed</h4>

        <div class="bg-white rounded border border-green-200 p-3 mb-3">
          <p class="text-sm text-gray-700 whitespace-pre-wrap">{{ message }}</p>
        </div>

        <div class="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            @click="navigateToAsset"
            class="text-green-700 border-green-300 hover:bg-green-100"
          >
            <ArrowRightIcon class="w-4 h-4 mr-1" />
            View in {{ assetTypeName }} Feed
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button'
import { ArrowRightIcon, CheckCircleIcon } from '@heroicons/vue/24/outline'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

interface Props {
  assetId: string
  assetName: string
  assetType: 'TABLE' | 'COLUMN' | 'DATABASE' | 'SCHEMA'
  message: string
}

const props = defineProps<Props>()
const router = useRouter()

const assetTypeName = computed(() => {
  return props.assetType.charAt(0) + props.assetType.slice(1).toLowerCase()
})

const navigateToAsset = () => {
  // Navigate to asset page with feed tab selected
  router.push({
    name: 'AssetPage',
    query: { assetId: props.assetId }
  })
}
</script>
