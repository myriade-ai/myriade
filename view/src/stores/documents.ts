import axios from '@/plugins/axios'
import type { Document, DocumentVersion } from '@/stores/conversations'
import { defineStore } from 'pinia'
import { reactive, ref } from 'vue'

export const useDocumentsStore = defineStore('documents', () => {
  // State
  const documents = reactive<Map<string, Document>>(new Map())
  const documentVersions = reactive<Map<string, DocumentVersion[]>>(new Map())
  const currentDocumentId = ref<string | null>(null)
  const isDocumentPanelOpen = ref(false)

  // Actions
  const fetchDocuments = async (
    databaseId: string,
    includeArchived: boolean = false
  ): Promise<Document[]> => {
    const response = await axios.get(
      `/api/databases/${databaseId}/documents?includeArchived=${includeArchived}`
    )
    const docs: Document[] = response.data

    // Update the documents map
    docs.forEach((doc) => {
      documents.set(doc.id, doc)
    })

    return docs
  }

  const fetchDocument = async (documentId: string): Promise<Document> => {
    const response = await axios.get(`/api/documents/${documentId}`)
    const doc: Document = response.data

    // Update the documents map
    documents.set(doc.id, doc)

    return doc
  }

  const updateDocument = async (
    documentId: string,
    updates: { content?: string; title?: string; changeDescription?: string }
  ): Promise<Document> => {
    const response = await axios.put(`/api/documents/${documentId}`, updates)
    const doc: Document = response.data

    // Update the documents map
    documents.set(doc.id, doc)

    return doc
  }

  const deleteDocument = async (documentId: string): Promise<void> => {
    await axios.delete(`/api/documents/${documentId}`)

    // Remove from map
    documents.delete(documentId)
    documentVersions.delete(documentId)

    // Close panel if this document is open
    if (currentDocumentId.value === documentId) {
      closeDocument()
    }
  }

  const fetchVersions = async (documentId: string): Promise<DocumentVersion[]> => {
    const response = await axios.get(`/api/documents/${documentId}/versions`)
    const versions: DocumentVersion[] = response.data

    // Update the versions map
    documentVersions.set(documentId, versions)

    return versions
  }

  const openDocument = async (documentId: string): Promise<void> => {
    // Always fetch the latest version from the server to ensure we have up-to-date content
    await fetchDocument(documentId)

    currentDocumentId.value = documentId
    isDocumentPanelOpen.value = true
  }

  const closeDocument = (): void => {
    currentDocumentId.value = null
    isDocumentPanelOpen.value = false
  }

  const getDocument = (documentId: string): Document | undefined => {
    return documents.get(documentId)
  }

  const getVersions = (documentId: string): DocumentVersion[] | undefined => {
    return documentVersions.get(documentId)
  }

  const archiveDocument = async (documentId: string, archived: boolean): Promise<Document> => {
    const response = await axios.post(`/api/documents/${documentId}/archive`, { archived })
    const doc: Document = response.data

    // Update the documents map
    documents.set(doc.id, doc)

    return doc
  }

  return {
    // State
    documents,
    documentVersions,
    currentDocumentId,
    isDocumentPanelOpen,

    // Actions
    fetchDocuments,
    fetchDocument,
    updateDocument,
    deleteDocument,
    fetchVersions,
    openDocument,
    closeDocument,
    getDocument,
    getVersions,
    archiveDocument
  }
})
