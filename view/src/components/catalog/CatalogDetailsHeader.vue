<template>
  <div class="px-6 py-4 border-b border-slate-200 bg-white/80 backdrop-blur-sm">
    <div class="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <div class="flex items-center gap-2">
          <component :is="assetIcon" class="h-5 w-5 text-primary-600" />
          <h2 class="text-lg font-semibold leading-tight">
            {{ asset.name || assetLabel }}
          </h2>
        </div>
        <p class="text-sm text-muted-foreground">
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
    <div v-if="asset.tags?.length" class="mt-3 flex flex-wrap gap-2">
      <Badge v-for="tag in asset.tags" :key="tag.id" variant="secondary" class="text-xs">
        {{ tag.name }}
      </Badge>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import type { CatalogAsset } from '@/stores/catalog'
import type { Component } from 'vue'

interface Props {
  asset: CatalogAsset
  assetIcon: Component
  assetLabel: string
  tableSummary: string
  columnsCount: number
}

defineProps<Props>()
</script>
