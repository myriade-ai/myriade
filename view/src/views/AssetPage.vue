<script setup lang="ts">
import CatalogAssetsView from '@/components/CatalogAssetsView.vue'
import PageHeader from '@/components/PageHeader.vue'
import { Button } from '@/components/ui/button'
import { useCatalogStore } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { useConversationsStore } from '@/stores/conversations'
import { SparklesIcon } from 'lucide-vue-next'
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'

const contextsStore = useContextsStore()
const catalogStore = useCatalogStore()
const conversationsStore = useConversationsStore()
const router = useRouter()

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

watch(
  () => contextsStore.contextSelected,
  async (newContext, oldContext) => {
    if (newContext && newContext.id !== oldContext?.id) {
      await catalogStore.fetchAssets(newContext.id, undefined)
    }
  }
)

onMounted(async () => {
  if (contextsStore.contextSelected) {
    await catalogStore.fetchAssets(contextsStore.contextSelected.id, undefined)
  }
})
</script>

<template>
  <PageHeader title="Catalog Assets" :subtitle="`${catalogStore.assetsArray.length} assets`">
    <template #actions>
      <Button @click="exploreDatabase">
        <SparklesIcon class="h-4 w-4 mr-2" />
        Explore & Describe Assets
      </Button>
    </template>
  </PageHeader>

  <div class="h-full px-4 py-4">
    <CatalogAssetsView />
  </div>
</template>
