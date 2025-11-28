<template>
  <div
    class="px-6 py-4 border-b border-border bg-card/80 backdrop-blur-sm flex flex-col gap-4 lg:flex-row lg:justify-between lg:items-start"
  >
    <div class="flex-1 min-w-0">
      <div class="flex flex-col gap-2">
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <component :is="assetIcon" class="h-5 w-5 text-primary-600 flex-shrink-0" />
            <h2 class="text-lg font-semibold leading-tight break-words">
              {{ asset.name || assetLabel }}
            </h2>
          </div>
          <p class="text-sm text-muted-foreground break-words whitespace-normal">
            {{ tableSummary }}
          </p>
          <div
            v-if="asset?.type === 'TABLE'"
            class="mt-2 flex items-center gap-4 text-sm text-muted-foreground"
          >
            <span>{{ columnsCount }} columns</span>
          </div>
        </div>
      </div>
      <div v-if="asset.tags?.length" class="flex flex-wrap">
        <Badge v-for="tag in asset.tags" :key="tag.id" variant="secondary" class="text-xs">
          {{ tag.name }}
        </Badge>
      </div>
    </div>
    <div class="flex flex-col gap-2 items-end">
      <div class="flex items-center gap-2">
        <Tooltip v-if="asset.status === 'draft'" :disabled="!hasAiSuggestions">
          <TooltipTrigger as-child>
            <Button
              size="sm"
              class="whitespace-nowrap disabled:pointer-events-auto"
              :disabled="hasAiSuggestions"
              @click="$emit('publish')"
            >
              Publish
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Accept or reject suggested changes before publishing</p>
          </TooltipContent>
        </Tooltip>
      </div>
      <AssetBadgeStatus :status="asset.status" badge-class="text-xs" />
    </div>
  </div>
</template>

<script setup lang="ts">
import AssetBadgeStatus from '@/components/AssetBadgeStatus.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import type { CatalogAsset } from '@/stores/catalog'
import { computed, type Component } from 'vue'

interface Props {
  asset: CatalogAsset
  assetIcon: Component
  assetLabel: string
  tableSummary: string
  columnsCount: number
}

const props = defineProps<Props>()

defineEmits<{
  publish: []
}>()

const hasAiSuggestions = computed(() => {
  return (
    !!props.asset.ai_suggestion ||
    (props.asset.ai_suggested_tags && props.asset.ai_suggested_tags.length > 0)
  )
})
</script>
