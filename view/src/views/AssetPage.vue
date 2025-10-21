<script setup lang="ts">
import CatalogAssetsView from '@/components/CatalogAssetsView.vue'
import SelectionSummaryPanel from '@/components/catalog/SelectionSummaryPanel.vue'
import PageHeader from '@/components/PageHeader.vue'
import { Button } from '@/components/ui/button'
import { useCatalogStore } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { useDatabasesStore } from '@/stores/databases'
import { RefreshCwIcon, SparklesIcon } from 'lucide-vue-next'
import { onMounted, ref, watch } from 'vue'

const contextsStore = useContextsStore()
const catalogStore = useCatalogStore()
const databasesStore = useDatabasesStore()
const isSyncing = ref(false)

async function syncDatabaseMetadata() {
  if (!contextsStore.contextSelected) {
    console.error('No context selected')
    return
  }

  try {
    isSyncing.value = true
    const databaseId = contextsStore.getSelectedContextDatabaseId()

    await databasesStore.syncDatabaseMetadata(databaseId)
    await catalogStore.fetchAssets(contextsStore.contextSelected.id)
  } catch (error: unknown) {
    console.error('Error syncing database metadata:', error)
  } finally {
    isSyncing.value = false
  }
}

watch(
  () => contextsStore.contextSelected,
  async (newContext, oldContext) => {
    if (newContext && newContext.id !== oldContext?.id) {
      await catalogStore.fetchAssets(newContext.id)
    }
  }
)

onMounted(async () => {
  if (contextsStore.contextSelected) {
    await catalogStore.fetchAssets(contextsStore.contextSelected.id)
  }
})
</script>

<template>
  <div class="flex flex-col h-screen">
    <PageHeader
      class="flex-shrink-0"
      title="Catalog Assets"
      :subtitle="`${catalogStore.assetsArray.length} assets`"
    >
      <template #actions>
        <Button @click="syncDatabaseMetadata" variant="outline" :disabled="isSyncing">
          <RefreshCwIcon class="h-4 w-4" :class="{ 'animate-spin': isSyncing }" />
          {{ isSyncing ? 'Syncing...' : 'Sync Database' }}
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

    <div class="flex-1 min-h-0 h-full">
      <CatalogAssetsView />
    </div>

    <!-- Selection Summary Panel (Floating) -->
    <SelectionSummaryPanel />
  </div>
</template>
