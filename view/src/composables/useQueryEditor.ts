import { formatSQL } from '@/lib/utils'
import axios from '@/plugins/axios'
import router from '@/router'
import { useContextsStore } from '@/stores/contexts'
import { computed, reactive, ref } from 'vue'

export interface Query {
  id: string | number
  title?: string
  sql?: string
  rows?: Record<string, any>[]
}

// Core reactive state
const query = reactive<{
  id: string | number | null
  title: string
  sql: string
  is_favorite?: boolean
}>({ id: null, title: '', sql: '', is_favorite: false })
const results = ref<any[] | null>(null)
const count = ref<number | null>(null)
const columns = ref<Array<{ name: string }>>([])
const error = ref<string | null>(null)
const loading = ref(false)
const databaseId = ref<string | null>(null)
// Keep a copy of the loaded backend query for diffing
const loadedQuery = ref<any>(null)

// Actions
const fetchQueryResults = async (id: string) => {
  const response = await axios.get(`/api/query/${id}/results`)
  return response.data
}

const fetchQuery = async (id: string) => {
  const response = await axios.get(`/api/query/${id}`)
  return response.data
}

const executeQuery = async (
  sql: string
): Promise<{ rows: any[]; count: number; columns: Array<{ name: string }> }> => {
  try {
    const response = await axios.post('/api/query/_run', {
      query: sql,
      databaseId: databaseId.value
    })
    return {
      rows: response.data.rows as any[],
      count: response.data.count as number,
      columns: (response.data.columns as Array<{ name: string }>) || []
    }
  } catch (error: any) {
    throw new Error(error.response?.data?.message || 'Query failed')
  }
}

const runQuery = async () => {
  loading.value = true
  try {
    const { rows, count: c, columns: cols } = await executeQuery(query.sql)
    error.value = null
    results.value = rows
    count.value = c
    columns.value = cols
    return results.value
  } catch (message: any) {
    error.value = message
  } finally {
    loading.value = false
  }
}

const loadQuery = async (id: string) => {
  query.id = id
  const response = await axios.get(`/api/query/${id}`)
  const q = response.data

  if (q.sql) q.sql = formatSQL(q.sql)

  // Update values
  loadedQuery.value = q
  query.title = q.title
  query.sql = q.sql || ''
  query.is_favorite = q.is_favorite

  // Select context from the query
  const contextsStore = useContextsStore()
  contextsStore.setSelectedContext(`database-${q.databaseId}`)
  databaseId.value = q.databaseId
  if (query.sql) runQuery()
}

const updateQuery = async () => {
  if (query.id) {
    await axios.put(`/api/query/${query.id}`, {
      title: query.title,
      sql: query.sql
    })
  } else {
    const response = await axios.post('/api/query', {
      title: query.title,
      sql: query.sql,
      databaseId: databaseId.value
    })
    query.id = response.data.id
    router.push({ name: 'Query', params: { id: query.id } })
  }
  // Reload after create or update
  await loadQuery(String(query.id))
}

const queryIsModified = computed(() => {
  return query.sql !== loadedQuery.value?.sql || query.title !== loadedQuery.value?.title
})

export function useQueryEditor() {
  return {
    // Core state
    query,
    results,
    count,
    columns,
    error,
    loading,
    databaseId,
    // Derived
    queryIsModified,
    // Actions
    fetchQueryResults,
    fetchQuery,
    loadQuery,
    executeQuery,
    runQuery,
    updateQuery
  }
}
