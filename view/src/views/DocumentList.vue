<template>
  <div>
    <PageHeader title="Reports" subtitle="Reports and documents created by the AI assistant" />
    <div class="overflow-y-auto h-screen">
      <div class="px-8">
        <!-- Search bar and filters -->
        <div v-if="!documentsQuery.isPending.value" class="flex items-center gap-4 my-6">
          <div class="flex-1">
            <Input
              v-model="searchQuery"
              type="text"
              placeholder="Search reports..."
              class="w-full"
            />
          </div>
          <Button variant="outline" size="sm" @click="toggleShowArchived">
            {{ showArchived ? 'Hide Archived' : 'Show Archived' }}
          </Button>
        </div>

        <div v-if="documentsQuery.isPending.value" class="mt-4 text-center">
          <p>Loading reports...</p>
        </div>

        <div v-else-if="documentsQuery.isError.value" class="mt-4 text-center text-error-500">
          <p>{{ documentsQuery.error.value?.message || 'Failed to load reports' }}</p>
        </div>

        <div v-else class="space-y-6 my-4">
          <!-- Empty state -->
          <div v-if="documents.length === 0" class="text-center py-12">
            <div
              class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100"
            >
              <FileTextIcon class="h-6 w-6 text-blue-600" />
            </div>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No reports yet</h3>
            <p class="mt-1 text-sm text-gray-500">
              Start a chat and ask the AI to create a report for you!
            </p>
            <div class="mt-6">
              <RouterLink
                to="/chat/new"
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg
                  class="-ml-1 mr-2 h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                Create your first report
              </RouterLink>
            </div>
          </div>

          <!-- Documents grid -->
          <div v-else class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Card
              v-for="doc in documents"
              :key="doc.id"
              class="overflow-hidden gap-0 h-fit hover:shadow-md transition-shadow"
              :class="{ 'opacity-60': doc.archived }"
            >
              <CardHeader @click="navigateToDocument(doc.id)" class="cursor-pointer">
                <div class="flex items-start gap-3">
                  <div
                    class="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center"
                  >
                    <FileTextIcon class="h-5 w-5 text-blue-600" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                      <CardTitle class="text-lg truncate">
                        {{ doc.title || 'Untitled Report' }}
                      </CardTitle>
                      <span
                        v-if="doc.archived"
                        class="px-2 py-0.5 text-xs bg-gray-200 text-gray-600 rounded"
                      >
                        Archived
                      </span>
                    </div>
                    <p class="text-xs text-gray-500 mt-1">
                      Updated {{ formatDate(doc.updatedAt) }}
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent @click="navigateToDocument(doc.id)" class="cursor-pointer">
                <div class="text-sm text-gray-600 line-clamp-4">
                  {{ getContentExcerpt(doc.content) }}
                </div>
              </CardContent>
              <CardFooter class="pt-2 justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  @click.stop="toggleArchive(doc)"
                  class="text-gray-600 hover:text-gray-800"
                >
                  {{ doc.archived ? 'Unarchive' : 'Archive' }}
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import PageHeader from '@/components/PageHeader.vue'
import Button from '@/components/ui/button/Button.vue'
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardFooter from '@/components/ui/card/CardFooter.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import Input from '@/components/ui/input/Input.vue'
import { useDocumentsQuery } from '@/composables/useDocumentsQuery'
import { useDocumentsStore } from '@/stores/documents'
import { FileText as FileTextIcon } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

const documentsStore = useDocumentsStore()
const router = useRouter()
const searchQuery = ref('')
const showArchived = ref(false)

// Use TanStack Query - automatically refetches when context changes
const documentsQuery = useDocumentsQuery(showArchived)

const documents = computed(() => {
  const docs = documentsQuery.data.value || []

  // Filter by search query if provided
  if (!searchQuery.value.trim()) {
    return docs
  }

  const query = searchQuery.value.toLowerCase().trim()
  return docs.filter((doc) => {
    const matchesTitle = doc.title?.toLowerCase().includes(query) || false
    const matchesContent = doc.content.toLowerCase().includes(query)
    return matchesTitle || matchesContent
  })
})

const navigateToDocument = (documentId: string) => {
  router.push(`/documents/${documentId}`)
}

const toggleShowArchived = () => {
  // Toggle the ref - TanStack Query will automatically refetch
  showArchived.value = !showArchived.value
}

const toggleArchive = async (doc: any) => {
  try {
    await documentsStore.archiveDocument(doc.id, !doc.archived)
    // Refetch to update the UI
    documentsQuery.refetch()
  } catch (err) {
    console.error('Failed to toggle archive:', err)
    alert('Failed to update archive status. Please try again.')
  }
}

const getContentExcerpt = (content: string): string => {
  // Remove markdown tags and get first few lines
  const plainText = content
    .replace(/<QUERY:[^>]+>/g, '[Query]')
    .replace(/<CHART:[^>]+>/g, '[Chart]')
    .replace(/#{1,6}\s/g, '')
    .replace(/[*_`]/g, '')
  const lines = plainText.split('\n').filter((line) => line.trim())
  return lines.slice(0, 3).join(' ') || 'Empty report'
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return 'today'
  if (days === 1) return 'yesterday'
  if (days < 7) return `${days} days ago`
  return date.toLocaleDateString()
}
</script>

<style scoped>
.line-clamp-4 {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
