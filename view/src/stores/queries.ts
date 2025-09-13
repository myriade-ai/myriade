import axios from '@/plugins/axios'
import { socket } from '@/plugins/socket'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export interface QueryData {
  id: string
  status: 'pending_confirmation' | 'running' | 'completed' | 'cancelled' | 'failed'
  sql?: string | null
  operationType?: string | null
  startedAt?: string | null
  completedAt?: string | null
  errorMessage?: string | null
}

export const useQueriesStore = defineStore('queries', () => {
  const queries = ref<Map<string, QueryData>>(new Map())
  const loading = ref<Set<string>>(new Set())
  const errors = ref<Map<string, string>>(new Map())

  // Computed helpers
  const getQuery = computed(() => (queryId: string | undefined) => {
    if (!queryId) return null
    return queries.value.get(queryId) || null
  })

  const needsConfirmation = computed(() => (queryId: string | undefined) => {
    if (!queryId) return false
    const query = queries.value.get(queryId)
    if (!query) return false
    const status = query.status
    return status === 'pending_confirmation'
  })

  const isLoading = computed(() => (queryId: string | undefined) => {
    if (!queryId) return false
    return loading.value.has(queryId)
  })

  const getError = computed(() => (queryId: string | undefined) => {
    if (!queryId) return null
    return errors.value.get(queryId) || null
  })

  // Actions
  const fetchQuery = async (queryId: string) => {
    if (!queryId) return

    try {
      loading.value.add(queryId)
      errors.value.delete(queryId)

      const response = await axios.get(`/api/query/${queryId}`)
      const queryData: QueryData = response.data

      queries.value.set(queryId, queryData)
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || 'Failed to fetch query'
      errors.value.set(queryId, errorMsg)
      console.error('Failed to fetch query:', err)
    } finally {
      loading.value.delete(queryId)
    }
  }

  const updateQuery = (queryId: string, updates: Partial<QueryData>) => {
    const existing = queries.value.get(queryId)
    if (existing) {
      const newMap = new Map(queries.value)
      newMap.set(queryId, { ...existing, ...updates })
      queries.value = newMap
    }
  }

  // Socket event handlers
  const setupSocketListeners = () => {
    // Listen for query status updates from backend
    socket.on('queryUpdated', (data: QueryData) => {
      console.log('queryUpdated', data)
      updateQuery(data.id, data)
    })
  }

  // Initialize socket listeners
  setupSocketListeners()

  return {
    queries: computed(() => queries.value),
    getQuery,
    needsConfirmation,
    isLoading,
    getError,
    fetchQuery,
    updateQuery
  }
})
