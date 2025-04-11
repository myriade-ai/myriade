// stores/useDatabasesStore.ts
import axios from '@/plugins/axios'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

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

export const useDatabasesStore = defineStore('databases', () => {
  // --------------------------------------------------------------------------
  // STATE
  // --------------------------------------------------------------------------
  const databases = ref<Database[]>([])
  const databaseSelectedId = ref<number | null>(
    localStorage.getItem('databaseId')
      ? parseInt(localStorage.getItem('databaseId') as string, 10)
      : null
  )

  // --------------------------------------------------------------------------
  // GETTERS
  // --------------------------------------------------------------------------
  const databaseSelected = computed<Database>(() => {
    return databases.value.find((db) => db.id === databaseSelectedId.value) ?? ({} as Database)
  })

  const sortedDatabases = computed(() => {
    return [...databases.value].sort((a, b) => a.id - b.id)
  })

  // --------------------------------------------------------------------------
  // ACTIONS
  // --------------------------------------------------------------------------
  function setDatabaseSelected(newDatabase: Database) {
    databaseSelectedId.value = newDatabase.id
    localStorage.setItem('databaseId', String(newDatabase.id))
  }

  async function fetchDatabases({ refresh }: { refresh: boolean }) {
    if (databases.value.length > 0 && !refresh) return

    console.log('fetching databases')
    databases.value = await axios.get('/api/databases').then((res) => res.data)

    // If there's no database selected yet, and we got some from the API:
    if (databases.value.length > 0 && databaseSelectedId.value === null) {
      databaseSelectedId.value = databases.value[0].id
    }
  }

  function fetchDatabaseTables(databaseId: number) {
    return axios.get(`/api/databases/${databaseId}/schema`).then((res) => res.data)
  }

  function selectDatabaseById(id: number) {
    databaseSelectedId.value = id
    localStorage.setItem('databaseId', String(id))
  }

  function updateDatabase(id: number, database: Database) {
    return axios.put(`/api/databases/${id}`, database)
  }

  function createDatabase(database: Database): Promise<Database> {
    return axios.post('/api/databases', database).then((res) => res.data)
  }

  function deleteDatabase(id: number) {
    return axios.delete(`/api/databases/${id}`)
  }

  function getDatabaseById(id: number) {
    return axios.get('/api/databases/').then((res) => res.data.find((db: Database) => db.id === id))
  }

  // Return everything you want available in the store
  return {
    // state
    databases,
    databaseSelectedId,

    // getters
    databaseSelected,
    sortedDatabases,
    // actions
    setDatabaseSelected,
    fetchDatabases,
    fetchDatabaseTables,
    selectDatabaseById,
    updateDatabase,
    createDatabase,
    deleteDatabase,
    getDatabaseById
  }
})
