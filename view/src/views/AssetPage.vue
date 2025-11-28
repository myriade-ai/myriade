<script setup lang="ts">
import { useCatalogAssetsQuery } from '@/components/catalog/useCatalogQuery'
import CatalogAssetsView from '@/components/CatalogAssetsView.vue'
import PageHeader from '@/components/PageHeader.vue'
import { Button } from '@/components/ui/button'
import { useCatalogStore } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { useDatabasesStore } from '@/stores/databases'
import { RefreshCwIcon, SparklesIcon } from 'lucide-vue-next'
import { storeToRefs } from 'pinia'
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const contextsStore = useContextsStore()
const catalogStore = useCatalogStore()
const databasesStore = useDatabasesStore()
const router = useRouter()
const { syncStatus, syncProgress } = storeToRefs(catalogStore)

const { data: assets, isLoading, isFetching } = useCatalogAssetsQuery()

const assetsCount = computed(() => assets.value?.length ?? 0)

const syncButtonText = computed(() => {
  switch (syncStatus.value) {
    case 'syncing':
      return `Syncing... ${syncProgress.value}%`
    case 'completed':
      return 'Re-Sync Catalog'
    case 'failed':
      return 'Retry Sync'
    default:
      return 'Sync Catalog'
  }
})

async function syncDatabaseMetadata() {
  if (!contextsStore.contextSelected) {
    console.error('No context selected')
    return
  }

  try {
    const databaseId = contextsStore.getSelectedContextDatabaseId()

    // Start the sync (returns immediately with 202)
    await databasesStore.syncDatabaseMetadata(databaseId)

    // Update local state - socket events will handle progress updates
    catalogStore.setSyncState('syncing', 0, null)
  } catch (error: unknown) {
    console.error('Error starting database metadata sync:', error)
    const err = error as { response?: { data?: { error?: string } } }
    catalogStore.setSyncState(
      'failed',
      syncProgress.value,
      err?.response?.data?.error || 'Failed to start sync'
    )
  }
}

function launchSmartScan() {
  router.push({ name: 'SmartScanPage' })
}

// Check sync status on mount
onMounted(async () => {
  if (!contextsStore.contextSelected) {
    return
  }

  try {
    const databaseId = contextsStore.getSelectedContextDatabaseId()
    const status = await databasesStore.getSyncStatus(databaseId)

    const normalizedStatus = (status.sync_status || 'idle') as
      | 'idle'
      | 'syncing'
      | 'completed'
      | 'failed'
    catalogStore.setSyncState(
      normalizedStatus,
      status.sync_progress || 0,
      status.sync_error || null
    )
  } catch (error: unknown) {
    console.error('Error checking initial sync status:', error)
  }
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
        <Button @click="launchSmartScan" variant="outline" class="md:gap-2">
          <SparklesIcon class="h-4 w-4" />
          <span class="hidden md:inline">Launch Smart Scan</span>
        </Button>
      </template>
    </PageHeader>

    <div class="flex-1 min-h-0 h-full">
      <CatalogAssetsView :is-loading="isLoading" :is-fetching="isFetching" />
    </div>
  </div>
</template>
