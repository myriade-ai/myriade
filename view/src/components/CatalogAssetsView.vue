<template>
  <div class="space-y-4">
    <div class="md:flex space-y-2 gap-4">
      <Input v-model="filters.search" placeholder="Search assets..." class="flex-1" />
      <Select v-model="filters.type">
        <SelectTrigger
          :class="
            cn(
              'w-full md:w-auto transition-all duration-200 ease-out transform-gpu font-medium ',
              filters.type !== 'all'
                ? `bg-primary-600 text-white [&_svg:not([class*='text-'])]:text-white shadow-sm scale-100`
                : 'bg-transparent text-current'
            )
          "
        >
          <SelectValue placeholder="Filter by type" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Types</SelectItem>
          <SelectItem value="TABLE">Tables</SelectItem>
          <SelectItem value="COLUMN">Columns</SelectItem>
        </SelectContent>
      </Select>
      <Button
        :variant="filters.reviewed === 'not_approved' ? 'default' : 'outline'"
        @click="filters.reviewed = filters.reviewed === 'not_approved' ? 'all' : 'not_approved'"
        class="transition-all duration-200 ease-out transform-gpu"
      >
        To review ({{ catalogStore.assetsArray.filter((a) => isNeedingReview(a)).length }})
      </Button>

      <Button
        variant="outline"
        @click="clearFilters"
        class="transition-all duration-200 ease-out transform-gpu"
      >
        Clear Filters
      </Button>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-8">
      <LoaderIcon />
      <span class="ml-2">Loading assets...</span>
    </div>

    <div v-else-if="error" class="text-center py-8">
      <p class="text-red-600 mb-4">{{ error }}</p>
      <Button @click="refresh" variant="outline">Retry</Button>
    </div>

    <div v-else class="space-y-4">
      <div v-if="filteredAssets.length === 0" class="p-8 text-center text-gray-500">
        <p>No assets found</p>
        <p class="text-sm mt-1">Try adjusting your search or filters</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <AssetBase
          v-for="row in filteredAssets"
          :key="row.id"
          mode="catalog"
          :selected="highlightedAssetId === row.id"
          :asset="{
            id: row.id,
            type: row.type,
            name: row.name ?? '',
            description: row.description ?? '',
            tags: row.tags ?? [],
            dataType: row.column_facet?.data_type ?? null,
            privacy: row.column_facet?.privacy,
            schema: row.table_facet?.schema || row.column_facet?.parent_table_facet?.schema || '',
            tableName:
              row.table_facet?.table_name ||
              row.column_facet?.parent_table_facet?.table_name ||
              catalogStore.assetsArray.find((a) => a.id === row.column_facet?.parent_table_asset_id)
                ?.table_facet?.table_name ||
              '',
            reviewed: row.reviewed ?? false
          }"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import LoaderIcon from '@/components/icons/LoaderIcon.vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useCatalogStore, type AssetType, type CatalogAsset } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AssetBase from './AssetBase.vue'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { cn } from '@/lib/utils'

const catalogStore = useCatalogStore()
const contextsStore = useContextsStore()
const filtersInitialValue = { search: '', type: 'all', reviewed: 'all' } as const
const filters = ref<{
  search: string
  type: AssetType | 'all'
  reviewed: 'all' | 'approved' | 'not_approved'
}>(filtersInitialValue)
const expanded = ref<Record<string, boolean>>({})
const route = useRoute()
const highlightedAssetId = ref<string | null>(null)
const pendingAssetId = ref<string | null>(null)

const loading = computed(() => catalogStore.loading)
const error = computed(() => catalogStore.error)

const isNeedingReview = (asset: CatalogAsset) => {
  const isReviewed = !!asset.reviewed
  const hasDescription = Boolean(asset.description && asset.description.toString().trim().length)
  const hasTags = Array.isArray(asset.tags) && asset.tags.length > 0
  return !isReviewed && (hasDescription || hasTags)
}

const filteredAssets = computed(() => {
  const query = filters.value.search?.trim().toLowerCase() ?? ''
  return catalogStore.assetsArray.filter((asset) => {
    if (filters.value.type !== 'all' && asset.type !== filters.value.type) {
      return false
    }

    if (filters.value.reviewed !== 'all') {
      const isReviewed = !!asset.reviewed

      if (filters.value.reviewed === 'approved' && !isReviewed) return false
      // For 'not_approved' we only consider assets that have at least a description or tags
      if (filters.value.reviewed === 'not_approved' && (isReviewed || !isNeedingReview(asset)))
        return false
    }

    if (!query) {
      return true
    }

    const nameMatch = asset.name?.toLowerCase().includes(query)
    const descMatch = asset.description?.toLowerCase().includes(query)
    const tagsMatch = asset.tags?.some((tag) => tag.name.toLowerCase().includes(query))
    return !!(nameMatch || descMatch || tagsMatch)
  })
})

const routeAssetId = computed(() => {
  const queryParam = route.query.assetId
  if (Array.isArray(queryParam)) {
    return queryParam[0] ?? null
  }
  return typeof queryParam === 'string' && queryParam.trim().length > 0 ? queryParam : null
})

function scrollToAssetWhenAvailable(id: string) {
  if (!id) return

  nextTick(() => {
    if (typeof window === 'undefined') {
      return
    }

    const el = document.getElementById(id)
    if (!el) {
      return
    }

    highlightedAssetId.value = id
    pendingAssetId.value = null
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

watch(
  routeAssetId,
  (newId) => {
    if (!newId) {
      pendingAssetId.value = null
      highlightedAssetId.value = null
      return
    }

    pendingAssetId.value = newId
    scrollToAssetWhenAvailable(newId)
  },
  { immediate: true }
)

watch(filteredAssets, () => {
  if (pendingAssetId.value) {
    scrollToAssetWhenAvailable(pendingAssetId.value)
  }
})

const clearFilters = () => {
  filters.value.search = ''
  filters.value.type = 'all'
  filters.value.reviewed = 'all'
}

async function refresh() {
  if (contextsStore.contextSelected) {
    await catalogStore.fetchAssets(contextsStore.contextSelected.id)
  }
}

watch(
  () => contextsStore.contextSelected,
  async (newContext, oldContext) => {
    if (newContext && newContext.id !== oldContext?.id) {
      expanded.value = {}
      filters.value.search = ''
    }
  }
)
</script>
