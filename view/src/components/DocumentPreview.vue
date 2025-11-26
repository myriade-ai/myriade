<template>
  <div
    class="document-preview border rounded-lg p-4 bg-card shadow-sm hover:shadow-md transition-shadow"
  >
    <div v-if="document" class="space-y-3">
      <!-- Header -->
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <svg
              class="w-5 h-5 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 class="text-lg font-semibold text-foreground">
              {{ document.title || 'Untitled Report' }}
            </h3>
          </div>
          <p class="text-xs text-muted-foreground mt-1">
            Updated {{ formatDate(document.updatedAt) }}
          </p>
        </div>
        <button
          @click="handleOpen"
          class="px-3 py-1.5 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md transition-colors"
        >
          Open
        </button>
      </div>

      <!-- Content Preview -->
      <div
        class="text-sm text-muted-foreground line-clamp-3 bg-muted p-3 rounded border border-border"
      >
        {{ contentExcerpt }}
      </div>
    </div>

    <!-- Loading state -->
    <div v-else class="flex items-center justify-center py-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDocumentQuery } from '@/composables/useDocumentsQuery'
import { useDocumentsStore } from '@/stores/documents'
import { computed, toRef } from 'vue'

const props = defineProps<{
  documentId: string
}>()

const emit = defineEmits<{
  open: [documentId: string]
}>()

const documentsStore = useDocumentsStore()

// Use TanStack Query to fetch document
const documentQuery = useDocumentQuery(toRef(props, 'documentId'))
const document = computed(() => documentQuery.data.value)

const contentExcerpt = computed(() => {
  if (!document.value) return ''
  const lines = document.value.content.split('\n').slice(0, 3)
  return lines.join('\n') || 'Empty report'
})

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

const handleOpen = () => {
  emit('open', props.documentId)
  documentsStore.openDocument(props.documentId)
}
</script>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
