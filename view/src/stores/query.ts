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

export const loadQuery = async (id: number) => {
  const response = await axios.get(`/api/query/${id}`)

  const query = response.data
  await selectDatabaseById(query.databaseId)

  queryId.value = query.id
  if (query.sql) {
    queryTextTranslation.value = sqlPrettier.format(query.sql)
    querySQL.value = queryTextTranslation.value
  }
  queryValidated.value = query.validated
  if (querySQL.value) {
    await runQuery()
  }
  // querySQL.value = sqlPrettier.format(response.data.output);
}

export const runQuery = async () => {
  loading.value = true
  return await axios
    .post('/api/query/_run', {
      query: querySQL.value,
      databaseId: databaseSelectedId.value
    })
    .then((response) => {
      queryError.value = null
      queryResults.value = response.data.rows
      queryCount.value = response.data.count
      return queryResults.value
    })
    .catch((e) => {
      queryError.value = e.response.data.message
    })
    .finally(() => {
      loading.value = false
    })
}

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
