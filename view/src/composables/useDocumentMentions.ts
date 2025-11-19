import axios from '@/plugins/axios'
import { useContextsStore } from '@/stores/contexts'
import { useQuery, type UseQueryReturnType } from '@tanstack/vue-query'
import type { AxiosResponse } from 'axios'
import { computed, type Ref } from 'vue'

export interface MentionItem {
  id: string
  title: string
  type: 'query' | 'chart'
  sql?: string // Only for queries
  updated_at?: string
}

interface MentionsResponse {
  queries: Array<{
    id: string
    title: string
    sql: string
    updated_at: string | null
  }>
  charts: Array<{
    id: string
    title: string
    updated_at: string | null
  }>
}

/**
 * TanStack Query hook for fetching recent mentions (queries and charts)
 * Returns the last 10 items (max 5 of each type) sorted by updatedAt
 */
export function useRecentMentionsQuery(): UseQueryReturnType<MentionItem[], Error> {
  const contextsStore = useContextsStore()

  const contextId = computed<string | null>(() => {
    const context = contextsStore.contextSelected
    if (!context) return null

    // Context ID is already in the format "project-{id}" or "database-{id}"
    return context.id
  })

  const query = useQuery({
    queryKey: computed(() => ['mentions', 'recent', contextId.value]),
    queryFn: async (): Promise<MentionItem[]> => {
      const currentContextId = contextId.value
      if (!currentContextId) {
        throw new Error('No context selected')
      }

      const response: AxiosResponse<MentionsResponse> = await axios.get(
        `/api/contexts/${currentContextId}/mentions/recent`
      )

      // Transform response into unified MentionItem array
      const queries: MentionItem[] = response.data.queries.map((q) => ({
        id: q.id,
        title: q.title,
        type: 'query' as const,
        sql: q.sql,
        updated_at: q.updated_at || undefined
      }))

      const charts: MentionItem[] = response.data.charts.map((c) => ({
        id: c.id,
        title: c.title,
        type: 'chart' as const,
        updated_at: c.updated_at || undefined
      }))

      // Combine and return
      return [...queries, ...charts]
    },
    // Only run query when we have a context selected
    enabled: computed(() => !!contextId.value),

    // Cache for 1 minute - recents don't change often
    staleTime: 60000,
    gcTime: 300000, // 5 minutes

    // Don't refetch on window focus
    refetchOnWindowFocus: false,

    // Retry failed requests
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
  })

  return query
}

/**
 * TanStack Query hook for searching mentions (queries and charts)
 * with a search query string
 */
export function useSearchMentionsQuery(
  searchQuery: Ref<string>
): UseQueryReturnType<MentionItem[], Error> {
  const contextsStore = useContextsStore()

  const contextId = computed<string | null>(() => {
    const context = contextsStore.contextSelected
    if (!context) return null

    // Context ID is already in the format "project-{id}" or "database-{id}"
    return context.id
  })

  const query = useQuery({
    queryKey: computed(() => ['mentions', 'search', contextId.value, searchQuery.value]),
    queryFn: async (): Promise<MentionItem[]> => {
      const currentContextId = contextId.value
      if (!currentContextId) {
        throw new Error('No context selected')
      }

      const trimmedSearch = searchQuery.value.trim()
      if (!trimmedSearch) {
        return []
      }

      const params = new URLSearchParams()
      params.append('q', trimmedSearch)

      const response: AxiosResponse<MentionsResponse> = await axios.get(
        `/api/contexts/${currentContextId}/mentions/search?${params.toString()}`
      )

      // Transform response into unified MentionItem array
      const queries: MentionItem[] = response.data.queries.map((q) => ({
        id: q.id,
        title: q.title,
        type: 'query' as const,
        sql: q.sql,
        updated_at: q.updated_at || undefined
      }))

      const charts: MentionItem[] = response.data.charts.map((c) => ({
        id: c.id,
        title: c.title,
        type: 'chart' as const,
        updated_at: c.updated_at || undefined
      }))

      // Combine and return
      return [...queries, ...charts]
    },
    // Only run query when we have a context selected AND a search query
    enabled: computed(() => !!contextId.value && searchQuery.value.trim().length > 0),

    // Cache for 30 seconds - search results might change
    staleTime: 30000,
    gcTime: 300000, // 5 minutes

    // Don't refetch on window focus
    refetchOnWindowFocus: false,

    // Retry failed requests
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
  })

  return query
}
