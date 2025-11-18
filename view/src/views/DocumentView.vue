<template>
  <PageHeader :title="document?.title || 'Report'" :subtitle="subtitle" sticky>
    <template #actions>
      <div class="flex items-center gap-2">
        <Button
          v-if="document"
          variant="outline"
          size="sm"
          @click="handleDelete"
          :disabled="isDeleting"
          class="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-300"
        >
          Delete
        </Button>
        <Button
          v-if="document"
          variant="outline"
          size="sm"
          @click="toggleArchive"
          :disabled="isArchiving"
        >
          {{ document.archived ? 'Unarchive' : 'Archive' }}
        </Button>
        <!-- Export dropdown -->
        <PdfExportDropdown
          v-if="document"
          :document-id="documentId"
          :document-title="document.title || undefined"
        />
        <Button variant="outline" size="sm" @click="toggleVersionHistory">
          <Clock class="w-4 h-4 mr-2" />
          Version History
        </Button>
        <Button
          v-if="document && !viewingVersion && !document.archived"
          variant="default"
          size="sm"
          @click="saveDocument"
          :disabled="!hasUnsavedChanges || isSaving"
        >
          <Loader2 v-if="isSaving" class="animate-spin h-4 w-4 mr-2" />
          {{ isSaving ? 'Saving...' : hasUnsavedChanges ? 'Save' : 'Saved' }}
        </Button>
      </div>
    </template>
  </PageHeader>

  <div class="flex-1 overflow-auto">
    <div class="px-8 py-6 max-w-4xl mx-auto">
      <!-- Loading state -->
      <div v-if="documentQuery.isPending.value" class="text-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-4 text-gray-500">Loading report...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="documentQuery.isError.value" class="text-center py-12">
        <div class="text-error-500">
          <p>{{ documentQuery.error.value?.message || 'Failed to load report' }}</p>
        </div>
      </div>

      <!-- Version History Sidebar -->
      <div v-else-if="showVersionHistory && document" class="space-y-4">
        <h3 class="text-lg font-semibold mb-4">Version History</h3>
        <div v-if="versionsQuery.isPending.value" class="text-center text-gray-500 py-8">
          Loading versions...
        </div>
        <div v-else class="space-y-3">
          <Card
            v-for="version in versions"
            :key="version.id"
            class="p-4 hover:bg-gray-50 cursor-pointer"
            @click="viewVersion(version)"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="font-medium text-gray-900">Version {{ version.versionNumber }}</span>
              <span class="text-xs text-gray-500">{{ formatDate(version.createdAt) }}</span>
            </div>
            <p v-if="version.changeDescription" class="text-sm text-gray-600">
              {{ version.changeDescription }}
            </p>
          </Card>
        </div>
      </div>

      <!-- Document content -->
      <div v-else-if="document">
        <!-- Archived banner -->
        <div
          v-if="document.archived"
          class="mb-4 p-3 bg-gray-100 border border-gray-300 rounded-lg"
        >
          <div class="flex items-center gap-2">
            <Archive class="w-5 h-5 text-gray-600" />
            <span class="text-sm font-medium text-gray-700">This report is archived</span>
          </div>
        </div>

        <!-- Warning banner when viewing a historical version -->
        <div v-if="viewingVersion" class="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <AlertTriangle class="w-5 h-5 text-amber-600" />
              <span class="text-sm font-medium text-amber-800">
                Viewing version {{ viewingVersion.versionNumber }} ({{
                  formatDate(viewingVersion.createdAt)
                }})
              </span>
            </div>
            <button
              @click="viewCurrentVersion"
              class="text-sm text-amber-700 hover:text-amber-900 underline"
            >
              Back to current version
            </button>
          </div>
        </div>

        <!-- Unified Editor/Viewer (Notion-like) -->
        <div v-if="!viewingVersion">
          <MarkdownEditor
            :model-value="document.content"
            @update:model-value="handleContentChange"
            :disabled="document.archived"
            :document-id="documentId"
            placeholder="Click to start writing... Use @ to mention queries or charts"
          />
        </div>

        <!-- Historical Version View (read-only) -->
        <div v-else class="prose max-w-none">
          <template v-for="(part, index) in parsedContent" :key="index">
            <MarkdownDisplay
              v-if="part.type === 'markdown' && part.content"
              :content="part.content"
            />
            <div v-if="part.type === 'query' && part.query_id" class="my-4">
              <Card class="p-0 pb-3.5 pt-1">
                <CardContent>
                  <BaseEditorPreview :queryId="part.query_id" />
                </CardContent>
              </Card>
            </div>
            <div v-if="part.type === 'chart' && part.chart_id" class="my-4">
              <Card class="p-0 pb-3.5 pt-1">
                <CardContent>
                  <Chart :chartId="part.chart_id" />
                </CardContent>
              </Card>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BaseEditorPreview from '@/components/base/BaseEditorPreview.vue'
import Chart from '@/components/Chart.vue'
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'
import MarkdownEditor from '@/components/MarkdownEditor.vue'
import PageHeader from '@/components/PageHeader.vue'
import PdfExportDropdown from '@/components/PdfExportDropdown.vue'
import Button from '@/components/ui/button/Button.vue'
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import { useDocumentQuery, useDocumentVersionsQuery } from '@/composables/useDocumentsQuery'
import type { DocumentVersion } from '@/stores/conversations'
import { useDocumentsStore } from '@/stores/documents'
import { useQueryClient } from '@tanstack/vue-query'
import { AlertTriangle, Archive, Clock, Loader2 } from 'lucide-vue-next'
import { computed, ref, toRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const documentsStore = useDocumentsStore()
const queryClient = useQueryClient()

const isSaving = ref(false)
const isArchiving = ref(false)
const isDeleting = ref(false)
const showVersionHistory = ref(false)
const viewingVersion = ref<DocumentVersion | null>(null)
const currentContent = ref('')

const documentId = computed(() => {
  return Array.isArray(route.params.id) ? route.params.id[0] : route.params.id
})

// Use TanStack Query to fetch document and versions
const documentQuery = useDocumentQuery(toRef(() => documentId.value))
const versionsQuery = useDocumentVersionsQuery(toRef(() => documentId.value))

const document = computed(() => documentQuery.data.value || null)
const versions = computed(() => versionsQuery.data.value || [])

const subtitle = computed(() => {
  if (!document.value) return ''
  return `Updated ${formatDate(document.value.updatedAt)}`
})

const hasUnsavedChanges = computed(() => {
  if (!document.value || !currentContent.value) return false
  return currentContent.value !== document.value.content
})

// Initialize current content from document
watch(
  document,
  (newDoc) => {
    if (newDoc && !currentContent.value) {
      currentContent.value = newDoc.content
    }
  },
  { immediate: true }
)

const parsedContent = computed<
  Array<{ type: string; content?: string; query_id?: string; chart_id?: string }>
>(() => {
  if (!document.value) return []

  // Use viewing version content, or current edited content
  const content = viewingVersion.value
    ? viewingVersion.value.content
    : currentContent.value || document.value.content

  const chunks: Array<{
    type: string
    content?: string
    query_id?: string
    chart_id?: string
  }> = []

  const tagRegex = /(<QUERY:([^>]+)>)|(<CHART:([^>]+)>)/g

  let lastEnd = 0
  let match: RegExpExecArray | null

  while ((match = tagRegex.exec(content)) !== null) {
    const start = match.index
    const end = start + match[0].length

    if (start > lastEnd) {
      chunks.push({
        type: 'markdown',
        content: content.slice(lastEnd, start)
      })
    }

    if (match[1]) {
      chunks.push({
        type: 'query',
        query_id: match[2].trim()
      })
    } else if (match[3]) {
      chunks.push({
        type: 'chart',
        chart_id: match[4].trim()
      })
    }

    lastEnd = end
  }

  if (lastEnd < content.length) {
    chunks.push({
      type: 'markdown',
      content: content.slice(lastEnd)
    })
  }

  if (chunks.length === 0) {
    return [{ type: 'markdown', content }]
  }

  return chunks
})

// Handle content changes (no auto-save, just update local state)
const handleContentChange = (newContent: string) => {
  currentContent.value = newContent
}

const saveDocument = async () => {
  if (!document.value || !documentId.value || !currentContent.value) return

  // Don't save if content hasn't changed
  if (currentContent.value === document.value.content) return

  try {
    isSaving.value = true

    // Update document and get the response with updated metadata
    const updatedDocument = await documentsStore.updateDocument(documentId.value, {
      content: currentContent.value,
      changeDescription: 'Manual save'
    })

    // Update cache with the saved document
    queryClient.setQueryData(['document', documentId.value], updatedDocument)

    // Refetch versions if version history is currently visible
    if (showVersionHistory.value) {
      versionsQuery.refetch()
    }
  } catch (err: unknown) {
    console.error('Failed to save document:', err)
    alert('Failed to save document. Please try again.')
  } finally {
    isSaving.value = false
  }
}

const toggleVersionHistory = () => {
  // Simply toggle - TanStack Query will handle fetching if needed
  showVersionHistory.value = !showVersionHistory.value
}

const viewVersion = (version: DocumentVersion) => {
  viewingVersion.value = version
  showVersionHistory.value = false
}

const viewCurrentVersion = () => {
  viewingVersion.value = null
}

const toggleArchive = async () => {
  if (!document.value || !documentId.value) return

  try {
    isArchiving.value = true
    await documentsStore.archiveDocument(documentId.value, !document.value.archived)
    // Refetch to show updated status
    documentQuery.refetch()
  } catch (err) {
    console.error('Failed to toggle archive:', err)
    alert('Failed to update archive status. Please try again.')
  } finally {
    isArchiving.value = false
  }
}

const handleDelete = async () => {
  if (!document.value || !documentId.value) return

  const confirmed = confirm(
    'Are you sure you want to delete this report? This action can be undone.'
  )
  if (!confirmed) return

  try {
    isDeleting.value = true
    await documentsStore.deleteDocument(documentId.value)
    // Navigate back to documents list
    router.push('/documents')
  } catch (err) {
    console.error('Failed to delete document:', err)
    alert('Failed to delete report. Please try again.')
  } finally {
    isDeleting.value = false
  }
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
.prose {
  color: #374151;
  max-width: 100%;
}

.prose :deep(h1) {
  font-size: 1.875rem;
  font-weight: 700;
  margin-top: 2rem;
  margin-bottom: 1rem;
}

.prose :deep(h2) {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

.prose :deep(h3) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
}

.prose :deep(p) {
  margin-bottom: 1rem;
  line-height: 1.75;
}

.prose :deep(ul),
.prose :deep(ol) {
  margin-bottom: 1rem;
  padding-left: 1.5rem;
}

.prose :deep(li) {
  margin-bottom: 0.5rem;
}

.prose :deep(code) {
  background-color: #f3f4f6;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

.prose :deep(pre) {
  background-color: #1f2937;
  color: #f9fafb;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin-bottom: 1rem;
}

.prose :deep(pre code) {
  background-color: transparent;
  padding: 0;
}
</style>
