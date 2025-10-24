<script setup lang="ts">
import SelectionSummaryPanel from '@/components/catalog/SelectionSummaryPanel.vue'
import { useCatalogAssetsQuery } from '@/components/catalog/useCatalogQuery'
import CatalogAssetsView from '@/components/CatalogAssetsView.vue'
import PageHeader from '@/components/PageHeader.vue'
import { Button } from '@/components/ui/button'
import { useCatalogStore } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { useDatabasesStore } from '@/stores/databases'
import { computeCatalogStats } from '@/utils/catalog-stats'
import { RefreshCwIcon, SparklesIcon } from 'lucide-vue-next'
import { computed, onMounted, onUnmounted, ref } from 'vue'

const contextsStore = useContextsStore()
const catalogStore = useCatalogStore()
const databasesStore = useDatabasesStore()
const syncStatus = ref<'idle' | 'syncing' | 'completed' | 'failed'>('idle')
const syncProgress = ref(0)
const syncError = ref<string | null>(null)

let pollInterval: ReturnType<typeof setInterval> | null = null

const { data: assets, isLoading, isFetching, refetch } = useCatalogAssetsQuery()

const assetsCount = computed(() => assets.value?.length ?? 0)

// Compute stats from assets directly in the frontend
const stats = computed(() => {
  if (!assets.value || assets.value.length === 0) {
    return null
  }
  return computeCatalogStats(assets.value)
})

const syncButtonText = computed(() => {
  switch (syncStatus.value) {
    case 'syncing':
      return `Syncing... ${syncProgress.value}%`
    case 'completed':
      return 'Sync Database'
    case 'failed':
      return 'Retry Sync'
    default:
      return 'Sync Database'
  }
})

async function pollSyncStatus(databaseId: string) {
  try {
    const status = await databasesStore.getSyncStatus(databaseId)
    syncStatus.value = status.sync_status || 'idle'
    syncProgress.value = status.sync_progress || 0
    syncError.value = status.sync_error || null

    // If sync completed or failed, stop polling
    if (syncStatus.value === 'completed' || syncStatus.value === 'failed') {
      if (pollInterval) {
        clearInterval(pollInterval)
        pollInterval = null
      }

      // Refresh assets after successful sync
      if (syncStatus.value === 'completed') {
        await refetch()
      }
    }
  } catch (error: unknown) {
    console.error('Error polling sync status:', error)
  }
}

function startPolling(databaseId: string) {
  // Poll every 2 seconds
  pollInterval = setInterval(() => {
    pollSyncStatus(databaseId)
  }, 2000)

  // Also poll immediately
  pollSyncStatus(databaseId)
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

async function syncDatabaseMetadata() {
  if (!contextsStore.contextSelected) {
    console.error('No context selected')
    return
  }

  try {
    const databaseId = contextsStore.getSelectedContextDatabaseId()

    // Start the sync (returns immediately with 202)
    await databasesStore.syncDatabaseMetadata(databaseId)

    // Update local state
    syncStatus.value = 'syncing'
    syncProgress.value = 0
    syncError.value = null

    // Start polling for status updates
    startPolling(databaseId)
  } catch (error: unknown) {
    console.error('Error starting database metadata sync:', error)
    syncStatus.value = 'failed'
    const err = error as { response?: { data?: { error?: string } } }
    syncError.value = err?.response?.data?.error || 'Failed to start sync'
  }
}

// Check sync status on mount and start polling if already syncing
onMounted(async () => {
  if (!contextsStore.contextSelected) {
    return
  }

  try {
    const databaseId = contextsStore.getSelectedContextDatabaseId()
    const status = await databasesStore.getSyncStatus(databaseId)

    syncStatus.value = status.sync_status || 'idle'
    syncProgress.value = status.sync_progress || 0
    syncError.value = status.sync_error || null

    // If database is already syncing, start polling
    if (syncStatus.value === 'syncing') {
      startPolling(databaseId)
    }
  } catch (error: unknown) {
    console.error('Error checking initial sync status:', error)
  }
})

// Cleanup on unmount
onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="flex flex-col h-screen">
    <PageHeader class="flex-shrink-0" title="Catalog Assets" :subtitle="`${assetsCount} assets`">
      <template #actions>
        <Button
          @click="syncDatabaseMetadata"
          variant="outline"
          :disabled="syncStatus === 'syncing'"
        >
          <RefreshCwIcon class="h-4 w-4" :class="{ 'animate-spin': syncStatus === 'syncing' }" />
          {{ syncButtonText }}
        </Button>
        <Button
          @click="catalogStore.toggleSelectionMode"
          :variant="catalogStore.selectionMode ? 'default' : 'outline'"
        >
          <SparklesIcon class="h-4 w-4" />
          {{ catalogStore.selectionMode ? 'Exit Selection Mode' : 'Select Assets for Analysis' }}
        </Button>
      </template>
    </PageHeader>

    <!-- Stats Bar -->
    <div v-if="stats" class="flex gap-4 px-4 py-3 border-b bg-gray-50/50 flex-shrink-0">
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">Total Assets:</span>
        <span class="text-sm font-semibold text-gray-900">{{ stats.total_assets }}</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">Completion Score:</span>
        <span
          class="text-sm font-semibold"
          :class="
            stats.completion_score >= 70
              ? 'text-green-600'
              : stats.completion_score >= 40
                ? 'text-yellow-600'
                : 'text-red-600'
          "
          >{{ stats.completion_score }}%</span
        >
      </div>
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">To Review:</span>
        <span
          class="text-sm font-semibold"
          :class="stats.assets_to_review > 0 ? 'text-orange-600' : 'text-gray-900'"
          >{{ stats.assets_to_review }}</span
        >
      </div>
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">Validated:</span>
        <span class="text-sm font-semibold text-gray-900">{{ stats.assets_validated }}</span>
      </div>
      <div v-if="stats.assets_with_ai_suggestions > 0" class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">AI Suggestions:</span>
        <span class="text-sm font-semibold text-purple-600">{{
          stats.assets_with_ai_suggestions
        }}</span>
      </div>
    </div>

    <div class="flex-1 min-h-0 h-full">
      <CatalogAssetsView :is-loading="isLoading" :is-fetching="isFetching" />
    </div>

    <!-- Selection Summary Panel (Floating) -->
    <SelectionSummaryPanel />
  </div>
</template>
