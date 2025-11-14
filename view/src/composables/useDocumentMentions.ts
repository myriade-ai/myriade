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

const RECENT_MENTIONS_KEY = 'myriade_recent_mentions'
const MAX_RECENT_ITEMS = 5

/**
 * Get recent mentions from localStorage
 */
export function getRecentMentions(contextId: string): MentionItem[] {
  if (!contextId) return []

  try {
    const stored = localStorage.getItem(RECENT_MENTIONS_KEY)
    if (!stored) return []

    const allRecent = JSON.parse(stored) as Record<string, MentionItem[]>
    const contextRecent = allRecent[contextId] || []

    // Validate that items have required properties
    return contextRecent.filter((item) => item && item.id && item.title && item.type)
  } catch (error) {
    console.error('Failed to get recent mentions:', error)
    // Clear corrupted data
    localStorage.removeItem(RECENT_MENTIONS_KEY)
    return []
  }
}

/**
 * Add a mention to recent items
 */
export function addRecentMention(contextId: string, item: MentionItem): void {
  if (!contextId || !item || !item.id || !item.title || !item.type) return

  try {
    const stored = localStorage.getItem(RECENT_MENTIONS_KEY)
    const allRecent = stored ? (JSON.parse(stored) as Record<string, MentionItem[]>) : {}

    // Get current context's recent items
    let contextRecent = allRecent[contextId] || []

    // Remove if already exists (we'll add it to the front)
    contextRecent = contextRecent.filter((m) => m.id !== item.id)

    // Add to front
    contextRecent.unshift(item)

    // Limit to MAX_RECENT_ITEMS
    contextRecent = contextRecent.slice(0, MAX_RECENT_ITEMS)

    // Save back
    allRecent[contextId] = contextRecent
    localStorage.setItem(RECENT_MENTIONS_KEY, JSON.stringify(allRecent))
  } catch (error) {
    console.error('Failed to save recent mention:', error)
  }
}

/**
 * TanStack Query hook for fetching mentions (queries and charts)
 * with optional search
 */
export function useMentionsQuery(
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
    queryKey: computed(() => ['mentions', contextId.value, searchQuery.value]),
    queryFn: async (): Promise<MentionItem[]> => {
      const currentContextId = contextId.value
      if (!currentContextId) {
        throw new Error('No context selected')
      }

      const params = new URLSearchParams()
      if (searchQuery.value.trim()) {
        params.append('search', searchQuery.value.trim())
      }

      const response: AxiosResponse<MentionsResponse> = await axios.get(
        `/api/contexts/${currentContextId}/mentions${params.toString() ? `?${params.toString()}` : ''}`
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

    // Cache for 30 seconds
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

/**
 * Merge recent mentions with search results
 * Recent items appear first, followed by search results (without duplicates)
 */
export function mergeWithRecent(
  searchResults: MentionItem[],
  recentItems: MentionItem[]
): MentionItem[] {
  // Create a map of search results by ID
  const searchMap = new Map(searchResults.map((item) => [item.id, item]))

  // Start with recent items (filter out any that no longer exist in search results)
  const merged: MentionItem[] = recentItems.filter((item) => searchMap.has(item.id))

  // Add remaining search results that aren't in recent
  const recentIds = new Set(merged.map((item) => item.id))
  const remaining = searchResults.filter((item) => !recentIds.has(item.id))

  return [...merged, ...remaining]
}
