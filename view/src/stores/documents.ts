import axios from '@/plugins/axios'
import type { Document } from '@/stores/conversations'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDocumentsStore = defineStore('documents', () => {
  // State - Only for panel management, not for data caching (TanStack Query handles that)
  const currentDocumentId = ref<string | null>(null)
  const isDocumentPanelOpen = ref(false)

  // Mutations - These trigger server updates and return updated data

  const updateDocument = async (
    documentId: string,
    updates: { content?: string; title?: string; changeDescription?: string }
  ): Promise<Document> => {
    const response = await axios.put(`/api/documents/${documentId}`, updates)
    return response.data
  }

  const deleteDocument = async (documentId: string): Promise<void> => {
    await axios.delete(`/api/documents/${documentId}`)

    // Close panel if this document is open
    if (currentDocumentId.value === documentId) {
      closeDocument()
    }
  }

  const archiveDocument = async (documentId: string, archived: boolean): Promise<Document> => {
    const response = await axios.post(`/api/documents/${documentId}/archive`, { archived })
    return response.data
  }

  const createDocument = async (databaseId: string, title: string): Promise<Document> => {
    const response = await axios.post(`/api/databases/${databaseId}/documents`, { title })
    return response.data
  }

  // Panel management
  const openDocument = (documentId: string): void => {
    currentDocumentId.value = documentId
    isDocumentPanelOpen.value = true
  }

  const closeDocument = (): void => {
    currentDocumentId.value = null
    isDocumentPanelOpen.value = false
  }

  return {
    // State
    currentDocumentId,
    isDocumentPanelOpen,

    // Mutations (server updates)
    createDocument,
    updateDocument,
    deleteDocument,
    archiveDocument,

    // Panel management
    openDocument,
    closeDocument
  }
})
