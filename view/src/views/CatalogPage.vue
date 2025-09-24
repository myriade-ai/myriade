<template>
  <div class="catalog-page flex flex-col h-full">
    <!-- Header -->
    <PageHeader
      title="Data Catalog"
      :subtitle="`${catalogStore.assetsArray.length} assets • ${catalogStore.termsArray.length} terms`"
    >
      <template #actions>
        <Button @click="exploreDatabase" variant="outline" class="mr-2">
          <SparklesIcon class="h-4 w-4 mr-2" />
          Explore & Describe Assets
        </Button>
        <Button @click="refresh"> Refresh </Button>
      </template>
    </PageHeader>

    <!-- Loading State -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <LoaderIcon />
      <span class="ml-2">Loading catalog...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <p class="text-red-600 mb-4">{{ error }}</p>
        <Button @click="refresh" variant="outline">Try Again</Button>
      </div>
    </div>

    <!-- Main Tabbed Interface -->
    <div v-else class="flex-1 overflow-hidden">
      <Tabs default-value="assets" class="h-full flex flex-col">
        <div class="flex-none px-6 py-3 border-b border-gray-200 bg-white">
          <TabsList class="grid w-full grid-cols-2">
            <TabsTrigger value="assets">Assets Table</TabsTrigger>
            <TabsTrigger value="terms">Business Terms</TabsTrigger>
          </TabsList>
        </div>

        <!-- Assets Table Tab -->
        <TabsContent value="assets" class="flex-1 overflow-hidden m-0 p-0">
          <div class="h-full px-6 py-4">
            <CatalogAssetsTable />
          </div>
        </TabsContent>

        <!-- Terms Tab -->
        <TabsContent value="terms" class="flex-1 overflow-y-auto m-0 p-0">
          <div class="px-6 py-4">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-medium text-gray-900">Business Terms</h3>
              <Button @click="showCreateTerm = true" variant="outline"> Add Term </Button>
            </div>

            <!-- Terms List -->
            <div v-if="catalogStore.termsArray.length > 0" class="space-y-4">
              <div
                v-for="term in catalogStore.termsArray"
                :key="term.id"
                class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <h3 class="text-lg font-medium text-gray-900">{{ term.name }}</h3>
                    <p class="text-sm text-gray-600 mt-1">{{ term.definition }}</p>

                    <!-- Synonyms -->
                    <div v-if="term.synonyms?.length" class="mt-2">
                      <span class="text-xs text-gray-500">Synonyms: </span>
                      <span class="text-xs text-gray-700">{{ term.synonyms.join(', ') }}</span>
                    </div>

                    <!-- Business Domains -->
                    <div v-if="term.business_domains?.length" class="mt-2 flex flex-wrap gap-1">
                      <span
                        v-for="domain in term.business_domains"
                        :key="domain"
                        class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-purple-100 text-purple-800"
                      >
                        {{ domain }}
                      </span>
                    </div>
                  </div>

                  <span
                    class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800 ml-4"
                  >
                    TERM
                  </span>
                </div>
              </div>
            </div>

            <!-- Empty Terms State -->
            <div v-else class="text-center py-8">
              <p class="text-gray-500 mb-2">No business terms defined</p>
              <p class="text-sm text-gray-400 mb-4">
                Create terms to help define your business vocabulary
              </p>
              <Button @click="showCreateTerm = true"> Create Your First Term </Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>

    <!-- Create Term Modal -->
    <div
      v-if="showCreateTerm"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click="showCreateTerm = false"
    >
      <div class="bg-white rounded-lg p-6 max-w-lg w-full mx-4" @click.stop>
        <h3 class="text-lg font-semibold mb-4">Create Business Term</h3>

        <form @submit.prevent="createTerm" class="space-y-4">
          <div>
            <Label for="termName">Name</Label>
            <Input id="termName" v-model="newTerm.name" required class="mt-1" />
          </div>

          <div>
            <Label for="termDefinition">Definition</Label>
            <Textarea
              id="termDefinition"
              v-model="newTerm.definition"
              required
              class="mt-1"
              rows="3"
            />
          </div>

          <div>
            <Label for="termSynonyms">Synonyms (comma-separated)</Label>
            <Input id="termSynonyms" v-model="newTerm.synonyms" class="mt-1" />
          </div>

          <div>
            <Label for="termDomains">Business Domains (comma-separated)</Label>
            <Input id="termDomains" v-model="newTerm.businessDomains" class="mt-1" />
          </div>

          <div class="flex justify-end space-x-3 mt-6">
            <Button type="button" @click="showCreateTerm = false" variant="outline">
              Cancel
            </Button>
            <Button type="submit" :disabled="!newTerm.name || !newTerm.definition">
              Create Term
            </Button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import CatalogAssetsTable from '@/components/CatalogAssetsTable.vue'
import LoaderIcon from '@/components/icons/LoaderIcon.vue'
import PageHeader from '@/components/PageHeader.vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import Label from '@/components/ui/label/Label.vue'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs/'
import { Textarea } from '@/components/ui/textarea'
import { useCatalogStore } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { useConversationsStore } from '@/stores/conversations'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { SparklesIcon } from '@heroicons/vue/24/solid'

const catalogStore = useCatalogStore()
const contextsStore = useContextsStore()
const conversationsStore = useConversationsStore()
const router = useRouter()

// State
const showCreateTerm = ref(false)
const newTerm = ref({
  name: '',
  definition: '',
  synonyms: '',
  businessDomains: ''
})

// Computed
const loading = computed(() => catalogStore.loading)
const error = computed(() => catalogStore.error)

// Methods
function refresh() {
  if (contextsStore.contextSelected) {
    catalogStore.fetchTerms(contextsStore.contextSelected.id)
  }
}

async function exploreDatabase() {
  const prompt = `Explore the database and help fill in descriptions for the most important assets in our data catalog. Before writing any asset descriptions, please:

1. **Perform a global business understanding check**:
   - Analyze the overall database structure and schema
   - Identify key business domains and data relationships
   - Understand the primary business processes reflected in the data

2. **Prioritize assets for description**:
   - Identify core tables
   - Consider tables with the most relationships or references

3. **Write short and concise asset descriptions that include**:
   - Key relationships with other tables
   - Data freshness and update patterns if observable
   - Important business rules or constraints

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

async function createTerm() {
  if (!contextsStore.contextSelected || !newTerm.value.name || !newTerm.value.definition) {
    return
  }

  try {
    const synonyms = newTerm.value.synonyms
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0)

    const domains = newTerm.value.businessDomains
      .split(',')
      .map((d) => d.trim())
      .filter((d) => d.length > 0)

    await catalogStore.createTerm(contextsStore.contextSelected.id, {
      name: newTerm.value.name,
      definition: newTerm.value.definition,
      synonyms: synonyms.length > 0 ? synonyms : undefined,
      business_domains: domains.length > 0 ? domains : undefined
    })

    // Reset form
    newTerm.value = { name: '', definition: '', synonyms: '', businessDomains: '' }
    showCreateTerm.value = false

    // Refresh terms
    refresh()
  } catch (error) {
    console.error('Error creating term:', error)
  }
}

// Watch for context changes
watch(
  () => contextsStore.contextSelected,
  async (newContext, oldContext) => {
    if (newContext && newContext.id !== oldContext?.id) {
      // Fetch both terms and assets for the new context
      await Promise.all([
        catalogStore.fetchTerms(newContext.id),
        catalogStore.fetchAssets(newContext.id, undefined)
      ])
    }
  }
)

// Initialize on mount
onMounted(async () => {
  if (contextsStore.contextSelected) {
    // Fetch both terms and assets for the catalog
    await Promise.all([
      catalogStore.fetchTerms(contextsStore.contextSelected.id),
      catalogStore.fetchAssets(contextsStore.contextSelected.id, undefined)
    ])
  }
})
</script>
