import axios from '@/plugins/axios'
import router from '@/router'
import { useDatabasesStore } from '@/stores/databases'
import { defineStore } from 'pinia'
// @ts-expect-error: No types for sql-prettier
import sqlPrettier from 'sql-prettier'
import { computed, ref } from 'vue'

export const useQueryStore = defineStore('query', () => {
  // Pull in anything needed from your Databases store
  const databasesStore = useDatabasesStore()

  // Same variable names as requested
  const queryRef = ref<any>(null)
  const queryTitle = ref('')
  const queryId = ref<string | null>(null)
  const querySQL = ref('')
  const queryResults = ref<any[] | null>(null)
  const queryCount = ref<number | null>(null)
  const queryError = ref<string | null>(null)
  const queryIsFavorite = ref<boolean>(false)
  const loading = ref(false)

  // Same methods, now inside Pinia store

  const fetchQueryResults = async (id: string) => {
    const response = await axios.get(`/api/query/${id}/results`)
    return response.data
  }

  const fetchQuery = async (id: string) => {
    const response = await axios.get(`/api/query/${id}`)
    return response.data
  }

  const loadQuery = async (id: string) => {
    queryId.value = id
    const response = await axios.get(`/api/query/${id}`)
    const query = response.data

    // Format SQL
    query.sql = sqlPrettier.format(query.sql)

    // Update store values
    queryRef.value = query
    queryTitle.value = query.title
    await databasesStore.selectDatabaseById(query.databaseId)

    if (query.sql) {
      querySQL.value = query.sql
    }

    if (querySQL.value) {
      runQuery(query.databaseId)
    }

    queryIsFavorite.value = query.is_favorite
  }

  const executeQuery = async (
    databaseId: string | null,
    sql: string
  ): Promise<{ rows: any[]; count: number }> => {
    if (!databaseId) throw new Error('No database selected')
    try {
      const response = await axios.post('/api/query/_run', {
        query: sql,
        databaseId: databaseId
      })
      return {
        rows: response.data.rows as any[],
        count: response.data.count as number
      }
    } catch (error: any) {
      throw new Error(error.response.data.message)
    }
  }

  const runQuery = async (databaseId: string | null) => {
    loading.value = true
    try {
      const { rows, count } = await executeQuery(databaseId, querySQL.value)
      queryError.value = null
      queryResults.value = rows
      queryCount.value = count
      return queryResults.value
    } catch (message: any) {
      queryError.value = message
    } finally {
      loading.value = false
    }
  }

  const updateQuery = async (databaseId: string | null) => {
    if (!databaseId) throw new Error('No database selected')
    if (queryId.value) {
      // Update existing query
      await axios.put(`/api/query/${queryId.value}`, {
        title: queryTitle.value,
        sql: querySQL.value
      })
    } else {
      // Create new query
      const response = await axios.post('/api/query', {
        title: queryTitle.value,
        sql: querySQL.value,
        databaseId: databaseId
      })
      queryId.value = response.data.id
      router.push({ name: 'Query', params: { id: queryId.value } })
    }
    // Reload after create or update
    loadQuery(queryId.value as string)
  }

  const queryIsModified = computed(() => {
    return querySQL.value !== queryRef.value?.sql || queryTitle.value !== queryRef.value?.title
  })

  // Return everything we want to expose
  return {
    // State
    queryRef,
    queryTitle,
    queryId,
    querySQL,
    queryResults,
    queryCount,
    queryError,
    loading,

    // Getters / Computed
    queryIsModified,

    // Actions
    fetchQueryResults,
    fetchQuery,
    loadQuery,
    executeQuery,
    runQuery,
    updateQuery
  }
})
