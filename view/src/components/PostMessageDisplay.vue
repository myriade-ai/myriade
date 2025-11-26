<template>
  <div class="border border-gray-200 rounded-lg overflow-hidden my-3">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
      <div class="flex items-center gap-2">
        <CheckCircleIcon class="w-4 h-4 text-green-500" />
        <span class="text-sm font-medium text-gray-700"
          >Posted to {{ assetName }} activity feed</span
        >
      </div>
      <Button
        variant="ghost"
        size="sm"
        @click="navigateToAsset"
        class="text-gray-500 hover:text-gray-700"
      >
        <ArrowRightIcon class="w-4 h-4" />
      </Button>
    </div>

    <!-- Content -->
    <div class="p-4">
      <MarkdownDisplay :content="message" class="text-sm text-gray-700" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button'
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'
import { ArrowRightIcon, CheckCircleIcon } from '@heroicons/vue/24/outline'
import { useRouter } from 'vue-router'

interface Props {
  assetId: string
  assetName: string
  assetType: 'TABLE' | 'COLUMN' | 'DATABASE' | 'SCHEMA'
  message: string
}

const props = defineProps<Props>()
const router = useRouter()

const navigateToAsset = () => {
  // Navigate to asset page with feed tab selected
  router.push({
    name: 'AssetPage',
    query: { assetId: props.assetId }
  })
}
</script>
