<template>
  <PageHeader title="Reports" subtitle="Reports and documents created by the AI assistant" sticky />
  <div class="flex-1 overflow-auto">
    <div class="px-8">
      <!-- Search bar and filters -->
      <div v-if="!documentsQuery.isPending.value" class="flex items-center gap-4 my-6">
        <div class="flex-1">
          <Input v-model="searchQuery" type="text" placeholder="Search reports..." class="w-full" />
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
            class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 dark:bg-blue-900/30"
          >
            <FileTextIcon class="h-6 w-6 text-blue-600 dark:text-blue-400" />
          </div>
          <h3 class="mt-2 text-sm font-medium text-foreground">No reports yet</h3>
          <p class="mt-1 text-sm text-muted-foreground">
            Start a chat and ask the AI to create a report for you!
          </p>
          <div class="mt-6">
            <RouterLink
              to="/chat/new"
              class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-primary-foreground bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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

        <!-- Documents table -->
        <div v-else class="mt-4 border rounded-lg bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead class="w-[50%]">Title</TableHead>
                <TableHead class="w-[30%]">Preview</TableHead>
                <TableHead class="w-[10%]">Updated</TableHead>
                <TableHead class="w-[10%] text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow
                v-for="doc in documents"
                :key="doc.id"
                class="cursor-pointer"
                :class="{ 'opacity-60': doc.archived }"
                @click="navigateToDocument(doc.id)"
              >
                <TableCell>
                  <div class="flex items-center gap-3">
                    <div
                      class="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center"
                    >
                      <FileTextIcon class="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2">
                        <p class="font-medium text-foreground truncate max-w-md">
                          {{ doc.title || 'Untitled Report' }}
                        </p>
                        <span
                          v-if="doc.archived"
                          class="px-2 py-0.5 text-xs bg-muted text-muted-foreground rounded flex-shrink-0"
                        >
                          Archived
                        </span>
                      </div>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <div class="text-sm text-muted-foreground truncate max-w-md">
                    {{ getContentExcerpt(doc.content) }}
                  </div>
                </TableCell>
                <TableCell>
                  <span class="text-sm text-muted-foreground">{{ formatDate(doc.updatedAt) }}</span>
                </TableCell>
                <TableCell class="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    @click.stop="toggleArchive(doc)"
                    class="text-muted-foreground hover:text-foreground"
                  >
                    {{ doc.archived ? 'Unarchive' : 'Archive' }}
                  </Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import PageHeader from '@/components/PageHeader.vue'
import Button from '@/components/ui/button/Button.vue'
import Input from '@/components/ui/input/Input.vue'
import Table from '@/components/ui/table/Table.vue'
import TableBody from '@/components/ui/table/TableBody.vue'
import TableCell from '@/components/ui/table/TableCell.vue'
import TableHead from '@/components/ui/table/TableHead.vue'
import TableHeader from '@/components/ui/table/TableHeader.vue'
import TableRow from '@/components/ui/table/TableRow.vue'
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
