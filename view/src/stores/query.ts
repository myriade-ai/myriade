import { computed, ref } from 'vue'
import axios from 'axios'
import sqlPrettier from 'sql-prettier'
import { useDatabases } from './databases'
import router from '../router'

const { selectDatabaseById, databaseSelectedId } = useDatabases()

export const queryId = ref<number | null>(null)
export const queryTextTranslation = ref('')
export const querySQL = ref('')
export const queryValidated = ref(false)
export const queryResults = ref(null)
export const queryCount = ref(null)
export const queryError = ref(null)
export const loading = ref(false)
export const visualisationParams = ref(null)

export const loadQuery = async (id: number) => {
  queryId.value = id
  const response = await axios.get(`/api/query/${id}`)

  const query = response.data
  visualisationParams.value = query.visualisationParams
  await selectDatabaseById(query.databaseId)

  if (query.sql) {
    queryTextTranslation.value = sqlPrettier.format(query.sql)
    querySQL.value = queryTextTranslation.value
  }
  queryValidated.value = query.validated
  if (querySQL.value) {
    runQuery()
  }
  // querySQL.value = sqlPrettier.format(response.data.output);
}

export const executeQuery = async (
  databaseId: number,
  sql: string
): Promise<{ rows: any[]; count: number }> => {
  return await axios
    .post('/api/query/_run', {
      query: sql,
      databaseId: databaseId
    })
    .then((response) => {
      return {
        rows: response.data.rows as any[],
        count: response.data.count as number
      }
    })
    .catch((e) => {
      throw new Error(e.response.data.message)
    })
}

export const runQuery = async () => {
  loading.value = true
  // @ts-ignore
  return executeQuery(databaseSelectedId.value, querySQL.value)
    .then(({ rows, count }) => {
      queryError.value = null
      // @ts-ignore
      queryResults.value = rows
      // @ts-ignore
      queryCount.value = count
      return queryResults.value
    })
    .catch((message) => {
      queryError.value = message
    })
    .finally(() => {
      loading.value = false
    })
}

export const updateQuery = async () => {
  console.log('updateQuery', queryId)
  await axios.put(`/api/query/${queryId.value}`, {
    query: querySQL.value,
    visualisationParams: visualisationParams.value
  })
}

export const updateVisualisationParams = async (params: any) => {
  console.log('updateVisualisationParams...', params)
  visualisationParams.value = params
  await updateQuery()
}

// TODO: delete query?
export const validateQuery = async () => {
  queryTextTranslation.value = querySQL.value
  await axios.post(`/api/query/${queryId.value}/validate`, {
    query: querySQL.value
  })
  queryValidated.value = true
}

export const queryIsModified = computed(() => {
  return querySQL.value !== queryTextTranslation.value
})
