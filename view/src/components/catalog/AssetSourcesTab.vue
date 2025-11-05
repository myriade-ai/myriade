<template>
  <div class="h-full flex flex-col min-h-0">
    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-8">
      <LoaderIcon />
      <span class="text-sm text-slate-600">Loading sources...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-red-600 mb-4">Failed to load source metadata: {{ error.message }}</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="!hasSources" class="text-center py-8 text-slate-600">
      <p>No data provider metadata available for this asset.</p>
      <p class="text-sm text-slate-500 mt-2">
        Metadata is displayed when the data provider supports it (e.g., Snowflake tags and
        comments).
      </p>
    </div>

    <!-- Provider Sources -->
    <div v-else class="flex-1 overflow-auto">
      <div
        v-for="(metadata, providerName) in sources"
        :key="providerName"
        class="border-b border-slate-200 p-4 bg-white"
      >
        <div class="flex items-center gap-2 mb-3">
          <div class="w-8 h-8 flex items-center justify-center">
            <img
              v-if="providerName === 'snowflake'"
              src="/datasources/snowflake.svg"
              alt="Snowflake"
              class="w-5 h-5"
            />
            <svg
              v-else
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              class="w-5 h-5 text-blue-600"
            >
              <path
                d="M12 2L3 7v5l9 5 9-5V7l-9-5zm0 2.18L17.82 7 12 9.82 6.18 7 12 4.18zM5 9.18l6 3.33v6.31l-6-3.33V9.18zm8 9.64v-6.31l6-3.33v6.31l-6 3.33z"
              />
            </svg>
          </div>
          <h3 class="font-semibold text-lg capitalize text-slate-800">{{ providerName }}</h3>
        </div>

        <div class="space-y-3">
          <div v-if="metadata.description">
            <h4 class="text-sm font-medium text-muted-foreground mb-1">Description</h4>
            <div class="text-sm leading-relaxed text-slate-700">
              <MarkdownDisplay :content="metadata.description" />
            </div>
          </div>

          <div v-if="metadata.tags && metadata.tags.length > 0">
            <h4 class="text-sm font-medium text-muted-foreground mb-2">Tags</h4>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="tag in metadata.tags"
                :key="tag"
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
              >
                {{ tag }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import LoaderIcon from '@/components/icons/LoaderIcon.vue'
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'
import { useAssetSourcesQuery } from './useCatalogQuery'
import { computed, toRef } from 'vue'

interface Props {
  assetId: string | null
}

const props = defineProps<Props>()

const assetIdRef = toRef(props, 'assetId')

const { data: sources, isLoading, error } = useAssetSourcesQuery(assetIdRef)
const hasSources = computed(() => {
  if (!sources.value) return false
  return Object.keys(sources.value).length > 0
})
</script>
