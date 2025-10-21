<script setup lang="ts">
import CatalogAssetsView from '@/components/CatalogAssetsView.vue'
import PageHeader from '@/components/PageHeader.vue'
import { Button } from '@/components/ui/button'
import { useCatalogAssetsQuery } from '@/components/catalog/useCatalogQuery'
import { useContextsStore } from '@/stores/contexts'
import { useConversationsStore } from '@/stores/conversations'
import { useDatabasesStore } from '@/stores/databases'
import { RefreshCwIcon, SparklesIcon } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const contextsStore = useContextsStore()
const conversationsStore = useConversationsStore()
const databasesStore = useDatabasesStore()
const router = useRouter()
const isSyncing = ref(false)

const { data: assets, isLoading, isFetching, refetch } = useCatalogAssetsQuery()

const assetsCount = computed(() => assets.value?.length ?? 0)

async function exploreDatabase() {
  const prompt = `Explore the database and help fill in descriptions for the most important assets in our data catalog. Before writing any asset descriptions, please:

1. **Perform a global business understanding check**:
   - Analyze the overall database structure and schema
   - Identify key business domains and data relationships
   - Understand the primary business processes reflected in the data

2. **Prioritize assets for description**:
   - Identify core tables and columns
   - Consider tables with the most relationships or references

3. **Write short and concise asset descriptions that include**:
   - Key relationships with other tables
   - Data freshness and update patterns if observable
   - Important business rules or constraints
   - Relevant tags based on business domain, data sensitivity, usage patterns, and data quality characteristics

Please start by exploring the database structure to understand our business context, then provide descriptions for the most important assets you identify. Focus on clarity and business value rather than technical implementation details.`

  if (!contextsStore.contextSelected) {
    console.error('No context selected')
    return
  }

  try {
    const newConversation = await conversationsStore.createConversation(
      contextsStore.contextSelected.id
    )

    await conversationsStore.sendMessage(newConversation.id, prompt, 'text')

    router.push({ name: 'ChatPage', params: { id: newConversation.id.toString() } })
  } catch (error) {
    console.error('Error creating conversation and sending message:', error)
  }
}

async function syncDatabaseMetadata() {
  if (!contextsStore.contextSelected) {
    console.error('No context selected')
    return
  }

  try {
    isSyncing.value = true
    const databaseId = contextsStore.getSelectedContextDatabaseId()

    await databasesStore.syncDatabaseMetadata(databaseId)
    await refetch()
  } catch (error: unknown) {
    console.error('Error syncing database metadata:', error)
  } finally {
    isSyncing.value = false
  }
}
</script>

<template>
  <div class="flex flex-col h-screen">
    <PageHeader class="flex-shrink-0" title="Catalog Assets" :subtitle="`${assetsCount} assets`">
      <template #actions>
        <Button @click="syncDatabaseMetadata" variant="outline" :disabled="isSyncing">
          <RefreshCwIcon class="h-4 w-4" :class="{ 'animate-spin': isSyncing }" />
          {{ isSyncing ? 'Syncing...' : 'Sync Database' }}
        </Button>
        <Button @click="exploreDatabase">
          <SparklesIcon class="h-4 w-4" />
          Explore & Describe Assets
        </Button>
      </template>
    </PageHeader>

    <div class="flex-1 min-h-0 h-full">
      <CatalogAssetsView :is-loading="isLoading" :is-fetching="isFetching" />
    </div>
  </div>
</template>
