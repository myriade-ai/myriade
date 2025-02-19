import { ref, computed } from 'vue'
import type { Ref, WritableComputedRef } from 'vue'
import axios from '@/plugins/axios'

export interface Database {
  id: number
  name: string
  engine: string
  details: any
  privacy_mode: boolean
  safe_mode: boolean
  dbt_catalog: any
  dbt_manifest: any
}

const databases: Ref<Database[]> = ref([])
const databaseSelectedId: Ref<number | null> = ref(
  localStorage.getItem('databaseId') ? parseInt(localStorage.getItem('databaseId') ?? '') : null
)

const databaseSelected: WritableComputedRef<Database> = computed({
  get: () => {
    return databases.value.find((db) => db.id === databaseSelectedId.value) ?? ({} as Database)
  },
  set: (newDatabase: Database) => {
    databaseSelectedId.value = newDatabase.id
    localStorage.setItem('databaseId', String(newDatabase.id))
  }
})

const fetchDatabases = async ({ refresh }: { refresh: boolean }) => {
  if (databases.value.length > 0 && !refresh) return

  databases.value = await axios.get('/api/databases').then((res) => res.data)

  if (!databases.value.length || databaseSelectedId.value !== null) return

  databaseSelectedId.value = databases.value[0].id
}

export const fetchDatabaseTables = (databaseId: number) => {
  return axios.get(`/api/databases/${databaseId}/schema`).then((res) => res.data)
}

const selectDatabaseById = async (id: number) => {
  databaseSelectedId.value = id
  localStorage.setItem('databaseId', id.toString())
}

const updateDatabase = async (id: number, database: Database) => {
  return axios.put('/api/databases/' + id, database)
}

const createDatabase = async (database: Database): Promise<Database> => {
  return axios.post('/api/databases', database).then((response) => response.data)
}

const deleteDatabase = (id: number) => {
  return axios.delete('/api/databases/' + id)
}

const getDatabaseById = (id: number) => {
  return axios
    .get('/api/databases/')
    .then((response) => response.data.find((db: Database) => db.id === id))
}

export const useDatabases = () => {
  return {
    fetchDatabases,
    databases,
    databaseSelected,
    databaseSelectedId,
    selectDatabaseById,
    fetchDatabaseTables,
    updateDatabase,
    createDatabase,
    deleteDatabase,
    getDatabaseById
  }
}
