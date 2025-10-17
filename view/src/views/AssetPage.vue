<script setup lang="ts">
import CatalogAssetsView from '@/components/CatalogAssetsView.vue'
import PageHeader from '@/components/PageHeader.vue'
import { Button } from '@/components/ui/button'
import { useCatalogStore } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { useConversationsStore } from '@/stores/conversations'
import { useDatabasesStore } from '@/stores/databases'
import { RefreshCwIcon, SparklesIcon } from 'lucide-vue-next'
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const contextsStore = useContextsStore()
const catalogStore = useCatalogStore()
const conversationsStore = useConversationsStore()
const databasesStore = useDatabasesStore()
const router = useRouter()
const isSyncing = ref(false)

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
    await Promise.all([
      catalogStore.fetchAssets(contextsStore.contextSelected.id),
      catalogStore.fetchStats(contextsStore.contextSelected.id)
    ])
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
      await Promise.all([
        catalogStore.fetchAssets(newContext.id),
        catalogStore.fetchStats(newContext.id)
      ])
    }
  }
)

onMounted(async () => {
  if (contextsStore.contextSelected) {
    await Promise.all([
      catalogStore.fetchAssets(contextsStore.contextSelected.id),
      catalogStore.fetchStats(contextsStore.contextSelected.id)
    ])
  }
})
</script>

<template>
  <div class="flex flex-col h-screen">
    <PageHeader class="flex-shrink-0" title="Catalog Assets">
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

    <!-- Stats Bar -->
    <div
      v-if="catalogStore.stats"
      class="flex gap-4 px-4 py-3 border-b bg-gray-50/50 flex-shrink-0"
    >
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">Total Assets:</span>
        <span class="text-sm font-semibold text-gray-900">{{
          catalogStore.stats.total_assets
        }}</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">Completion Score:</span>
        <span
          class="text-sm font-semibold"
          :class="
            catalogStore.stats.completion_score >= 70
              ? 'text-green-600'
              : catalogStore.stats.completion_score >= 40
                ? 'text-yellow-600'
                : 'text-red-600'
          "
          >{{ catalogStore.stats.completion_score }}%</span
        >
      </div>
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">To Review:</span>
        <span
          class="text-sm font-semibold"
          :class="catalogStore.stats.assets_to_review > 0 ? 'text-orange-600' : 'text-gray-900'"
          >{{ catalogStore.stats.assets_to_review }}</span
        >
      </div>
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">Validated:</span>
        <span class="text-sm font-semibold text-gray-900">{{
          catalogStore.stats.assets_validated
        }}</span>
      </div>
      <div v-if="catalogStore.stats.assets_with_ai_suggestions > 0" class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">AI Suggestions:</span>
        <span class="text-sm font-semibold text-purple-600">{{
          catalogStore.stats.assets_with_ai_suggestions
        }}</span>
      </div>
    </div>

    <div class="flex-1 min-h-0 h-full">
      <CatalogAssetsView />
    </div>
  </div>
</template>
