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

  const isRunning = computed(() => (queryId: string | undefined) => {
    if (!queryId) return false
    const query = queries.value.get(queryId)
    if (!query) return false
    return query.status === 'running'
  })

  const canBeCancelled = computed(() => (queryId: string | undefined) => {
    if (!queryId) return false
    const query = queries.value.get(queryId)
    if (!query) return false
    return query.status === 'running'
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

  const cancelQuery = async (queryId: string) => {
    if (!queryId) return false

    try {
      loading.value.add(queryId)
      errors.value.delete(queryId)

      // Try REST API first
      await axios.post(`/api/query/${queryId}/cancel`)
      
      // Update local state
      updateQuery(queryId, { status: 'cancelled' })
      
      return true
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || 'Failed to cancel query'
      errors.value.set(queryId, errorMsg)
      console.error('Failed to cancel query:', err)
      return false
    } finally {
      loading.value.delete(queryId)
    }
  }

  const cancelQueryViaSocket = (queryId: string) => {
    if (!queryId) return
    
    // Use WebSocket for real-time cancellation
    socket.emit('cancelQuery', queryId)
  }

  // Socket event handlers
  const setupSocketListeners = () => {
    // Listen for query status updates from backend
    socket.on('queryUpdated', (data: QueryData) => {
      console.log('queryUpdated', data)
      updateQuery(data.id, data)
    })
    
    // Listen for query cancellation confirmations
    socket.on('queryCancelled', (data: { queryId: string; message: string }) => {
      console.log('queryCancelled', data)
      updateQuery(data.queryId, { status: 'cancelled' })
    })
    
    // Listen for errors
    socket.on('error', (data: { message: string }) => {
      console.error('Socket error:', data.message)
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
    isRunning,
    canBeCancelled,
    fetchQuery,
    updateQuery,
    cancelQuery,
    cancelQueryViaSocket
  }
})
