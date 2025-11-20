<template>
  <!-- Backdrop overlay -->
  <Transition name="fade">
    <div
      v-if="documentsStore.isDocumentPanelOpen"
      class="fixed inset-0 bg-black opacity-30 z-40"
      @click="documentsStore.closeDocument()"
    ></div>
  </Transition>

  <!-- Side panel -->
  <Transition name="slide">
    <div
      v-if="documentsStore.isDocumentPanelOpen && document"
      class="fixed right-0 top-0 bottom-0 w-[600px] bg-white shadow-2xl z-50 flex flex-col"
    >
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b bg-gray-50">
        <input
          v-if="isEditingTitle"
          v-model="editedTitle"
          @blur="saveTitle"
          @keydown.enter="saveTitle"
          @keydown.escape="cancelTitleEdit"
          class="text-xl font-semibold flex-1 mr-4 px-2 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          autofocus
        />
        <h2 v-else class="text-xl font-semibold flex-1 mr-4 cursor-pointer" @click="startTitleEdit">
          {{ document.title || 'Untitled Report' }}
        </h2>

        <div class="flex items-center gap-2">
          <!-- Save button -->
          <button
            v-if="!viewingVersion && !showVersionHistory"
            @click="saveDocument"
            :disabled="!hasUnsavedChanges || isSaving"
            class="px-3 py-1.5 text-sm font-medium rounded-md transition-colors"
            :class="
              hasUnsavedChanges && !isSaving
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            "
            title="Save changes"
          >
            <span v-if="isSaving" class="flex items-center gap-2">
              <Loader2 class="animate-spin h-4 w-4" />
              Saving...
            </span>
            <span v-else>{{ hasUnsavedChanges ? 'Save' : 'Saved' }}</span>
          </button>

          <!-- Export dropdown -->
          <PdfExportDropdown
            v-if="document && documentsStore.currentDocumentId"
            :document-id="documentsStore.currentDocumentId"
            :document-title="document.title || undefined"
          >
            <template #trigger>
              <button
                class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors flex items-center gap-2"
              >
                <span>Export</span>
              </button>
            </template>
          </PdfExportDropdown>

          <!-- Version history button -->
          <button
            @click="toggleVersionHistory"
            class="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
            title="Version History"
          >
            <Clock class="w-5 h-5" />
          </button>

          <!-- Close button -->
          <button
            @click="documentsStore.closeDocument()"
            class="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
          >
            <X class="w-6 h-6" />
          </button>
        </div>
      </div>

      <!-- Content area -->
      <div class="flex-1 overflow-y-auto p-6">
        <!-- Warning banner when viewing a historical version -->
        <div
          v-if="viewingVersion && !showVersionHistory"
          class="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg"
        >
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

        <!-- Version History View -->
        <div v-if="showVersionHistory" class="space-y-4">
          <h3 class="text-lg font-semibold mb-4">Version History</h3>
          <div v-if="versions.length === 0" class="text-center text-gray-500 py-8">
            Loading versions...
          </div>
          <div v-else class="space-y-3">
            <div
              v-for="version in versions"
              :key="version.id"
              class="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
              @click="viewVersion(version)"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="font-medium text-gray-900">Version {{ version.versionNumber }}</span>
                <span class="text-xs text-gray-500">{{ formatDate(version.createdAt) }}</span>
              </div>
              <p v-if="version.changeDescription" class="text-sm text-gray-600">
                {{ version.changeDescription }}
              </p>
            </div>
          </div>
        </div>

        <!-- Unified Editor/Viewer (Notion-like) -->
        <div v-else-if="!viewingVersion">
          <MarkdownEditor
            :model-value="document.content"
            @update:model-value="handleContentChange"
            :disabled="false"
            :document-id="documentsStore.currentDocumentId || undefined"
            placeholder="Start writing... Use @ to mention queries or charts"
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

      <!-- Footer -->
      <div class="border-t p-4 bg-gray-50 flex items-center justify-between">
        <div class="text-sm text-gray-500">
          <span v-if="showVersionHistory">{{ versions.length }} versions</span>
          <span v-else-if="viewingVersion">
            Version {{ viewingVersion.versionNumber }} - {{ formatDate(viewingVersion.createdAt) }}
          </span>
          <span v-else-if="hasUnsavedChanges" class="text-amber-600 font-medium">
            Unsaved changes
          </span>
          <span v-else> Updated {{ formatDate(document.updatedAt) }} </span>
        </div>

        <div class="flex gap-2">
          <button
            v-if="showVersionHistory"
            @click="backToDocument"
            class="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
          >
            Back to Document
          </button>
          <button
            v-else-if="viewingVersion"
            @click="viewCurrentVersion"
            class="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
          >
            Current Version
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import BaseEditorPreview from '@/components/base/BaseEditorPreview.vue'
import Chart from '@/components/Chart.vue'
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'
import MarkdownEditor from '@/components/MarkdownEditor.vue'
import PdfExportDropdown from '@/components/PdfExportDropdown.vue'
import { Card, CardContent } from '@/components/ui/card'
import { useDocumentQuery, useDocumentVersionsQuery } from '@/composables/useDocumentsQuery'
import type { DocumentVersion } from '@/stores/conversations'
import { useDocumentsStore } from '@/stores/documents'
import { AlertTriangle, Clock, Loader2, X } from 'lucide-vue-next'
import { computed, ref, toRef, watch } from 'vue'

const documentsStore = useDocumentsStore()

// Reactive state
const isSaving = ref(false)
const isEditingTitle = ref(false)
const showVersionHistory = ref(false)
const editedTitle = ref('')
const viewingVersion = ref<DocumentVersion | null>(null)
const currentContent = ref('')

// Use TanStack Query to fetch document and versions
const documentQuery = useDocumentQuery(toRef(documentsStore, 'currentDocumentId'))
const versionsQuery = useDocumentVersionsQuery(toRef(documentsStore, 'currentDocumentId'))

// Computed
const document = computed(() => documentQuery.data.value || null)
const versions = computed(() => versionsQuery.data.value || [])

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

  // Get the content to parse (either viewing version or current edited content)
  const content = viewingVersion.value
    ? viewingVersion.value.content
    : currentContent.value || document.value.content

  const chunks: Array<{
    type: string
    content?: string
    query_id?: string
    chart_id?: string
  }> = []

  // Regex to find <QUERY:id> or <CHART:id> tags
  const tagRegex = /(<QUERY:([^>]+)>)|(<CHART:([^>]+)>)/g

  let lastEnd = 0
  let match: RegExpExecArray | null

  while ((match = tagRegex.exec(content)) !== null) {
    const start = match.index
    const end = start + match[0].length

    // Add preceding markdown content if it exists
    if (start > lastEnd) {
      chunks.push({
        type: 'markdown',
        content: content.slice(lastEnd, start)
      })
    }

    // Check which group matched to determine type and get the ID
    if (match[1]) {
      // Matched <QUERY:id>
      const queryId = match[2].trim()
      chunks.push({
        type: 'query',
        query_id: queryId
      })
    } else if (match[3]) {
      // Matched <CHART:id>
      const chartId = match[4].trim()
      chunks.push({
        type: 'chart',
        chart_id: chartId
      })
    }

    lastEnd = end
  }

  // Add any remaining markdown content after the last tag
  if (lastEnd < content.length) {
    chunks.push({
      type: 'markdown',
      content: content.slice(lastEnd)
    })
  }

  // If no tags were found, return the whole content as markdown
  if (chunks.length === 0) {
    return [{ type: 'markdown', content }]
  }

  return chunks
})

// Watch for document changes to reset state
watch(
  () => documentsStore.currentDocumentId,
  (newId) => {
    if (newId) {
      showVersionHistory.value = false
      viewingVersion.value = null
      currentContent.value = ''
    }
  }
)

// Handle content changes (no auto-save, just update local state)
const handleContentChange = (newContent: string) => {
  currentContent.value = newContent
}

const saveDocument = async () => {
  if (!document.value || !documentsStore.currentDocumentId || currentContent.value == null) return

  // Don't save if content hasn't changed
  if (currentContent.value === document.value.content) return

  try {
    isSaving.value = true
    await documentsStore.updateDocument(documentsStore.currentDocumentId, {
      content: currentContent.value,
      changeDescription: 'Manual save'
    })
    // Refetch to update metadata (timestamps, etc.)
    documentQuery.refetch()
    versionsQuery.refetch()
  } catch (error) {
    console.error('Failed to save document:', error)
    alert('Failed to save document. Please try again.')
  } finally {
    isSaving.value = false
  }
}

const startTitleEdit = () => {
  if (!document.value) return
  editedTitle.value = document.value.title || ''
  isEditingTitle.value = true
}

const cancelTitleEdit = () => {
  isEditingTitle.value = false
  editedTitle.value = ''
}

const saveTitle = async () => {
  if (!document.value || !documentsStore.currentDocumentId) return

  try {
    await documentsStore.updateDocument(documentsStore.currentDocumentId, {
      title: editedTitle.value
    })
    isEditingTitle.value = false
    // Refetch to show updated title
    documentQuery.refetch()
  } catch (error) {
    console.error('Failed to update title:', error)
    alert('Failed to update title. Please try again.')
  }
}

const toggleVersionHistory = () => {
  // Simply toggle - TanStack Query will handle fetching if needed
  showVersionHistory.value = !showVersionHistory.value
}

const viewVersion = (version: DocumentVersion) => {
  // Show the selected version in read-only mode with a warning banner
  viewingVersion.value = version
  showVersionHistory.value = false
}

const viewCurrentVersion = () => {
  // Return to viewing the current version
  viewingVersion.value = null
}

const backToDocument = () => {
  // Go back from version history to document view
  showVersionHistory.value = false
  viewingVersion.value = null
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
/* Transition animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}

/* Prose styles for markdown rendering */
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
