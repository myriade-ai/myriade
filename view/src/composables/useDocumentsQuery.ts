import axios from '@/plugins/axios'
import { useContextsStore } from '@/stores/contexts'
import type { Document, DocumentVersion } from '@/stores/conversations'
import { useQuery, type UseQueryReturnType } from '@tanstack/vue-query'
import type { AxiosResponse } from 'axios'
import { computed, type Ref } from 'vue'

/**
 * TanStack Query hook for fetching documents list
 * Automatically refetches when context changes
 */
export function useDocumentsQuery(
  includeArchived: Ref<boolean>
): UseQueryReturnType<Document[], Error> {
  const contextsStore = useContextsStore()

  const databaseId = computed<string | null>(() => {
    try {
      return contextsStore.getSelectedContextDatabaseId()
    } catch {
      return null
    }
  })

  const query = useQuery({
    queryKey: computed(() => ['documents', databaseId.value, includeArchived.value]),
    queryFn: async (): Promise<Document[]> => {
      const currentDatabaseId = databaseId.value
      if (!currentDatabaseId) {
        throw new Error('No database selected')
      }

      const response: AxiosResponse<Document[]> = await axios.get(
        `/api/databases/${currentDatabaseId}/documents?includeArchived=${includeArchived.value}`
      )

      return response.data
    },
    // Only run query when we have a context selected
    enabled: computed(() => !!databaseId.value),

    // No caching - always fetch fresh data
    staleTime: 0,
    gcTime: 0,

    // Don't refetch on window focus
    refetchOnWindowFocus: false,

    // Retry failed requests with exponential backoff
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
  })

  return query
}

/**
 * TanStack Query hook for fetching a single document
 */
export function useDocumentQuery(
  documentId: Ref<string | null | undefined>
): UseQueryReturnType<Document, Error> {
  const query = useQuery({
    queryKey: computed(() => ['document', documentId.value]),
    queryFn: async (): Promise<Document> => {
      const currentDocumentId = documentId.value
      if (!currentDocumentId) {
        throw new Error('No document ID provided')
      }

      const response: AxiosResponse<Document> = await axios.get(
        `/api/documents/${currentDocumentId}`
      )

      return response.data
    },
    // Only run query when we have a document ID
    enabled: computed(() => !!documentId.value),

    // No caching - always fetch fresh data
    staleTime: 0,
    gcTime: 0,

    // Don't refetch on window focus
    refetchOnWindowFocus: false,

    // Retry failed requests
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
  })

  return query
}

/**
 * TanStack Query hook for fetching document versions
 */
export function useDocumentVersionsQuery(
  documentId: Ref<string | null | undefined>
): UseQueryReturnType<DocumentVersion[], Error> {
  const query = useQuery({
    queryKey: computed(() => ['document', 'versions', documentId.value]),
    queryFn: async (): Promise<DocumentVersion[]> => {
      const currentDocumentId = documentId.value
      if (!currentDocumentId) {
        throw new Error('No document ID provided')
      }

      const response: AxiosResponse<DocumentVersion[]> = await axios.get(
        `/api/documents/${currentDocumentId}/versions`
      )

      return response.data
    },
    // Only run query when we have a document ID
    enabled: computed(() => !!documentId.value),

    // No caching - always fetch fresh data
    staleTime: 0,
    gcTime: 0,

    // Don't refetch on window focus
    refetchOnWindowFocus: false,

    // Retry failed requests
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
  })

  return query
}
