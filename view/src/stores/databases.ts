// stores/useDatabasesStore.ts
import axios from '@/plugins/axios'
import type { AssetTag } from '@/stores/catalog'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type Engine =
  | 'postgres'
  | 'mysql'
  | 'snowflake'
  | 'sqlite'
  | 'bigquery'
  | 'motherduck'
  | 'oracle'
export type WriteMode = 'read-only' | 'confirmation' | 'skip-confirmation'

export interface Database {
  id: string
  createdAt: Date
  name: string
  engine: Engine | null
  details: Record<string, string | number | undefined | null> | null
  public: boolean
  write_mode: WriteMode
  dbt_catalog?: unknown
  dbt_manifest?: unknown
  tags?: AssetTag[]
  organisationId?: string | null
  ownerId?: string | null
  // Metadata sync status
  sync_status?: 'idle' | 'syncing' | 'completed' | 'failed'
  sync_progress?: number
  sync_started_at?: Date
  sync_completed_at?: Date
  sync_error?: string
}

export const makeEmptyDatabase = () =>
  ({
    id: '',
    createdAt: new Date(),
    name: '',
    engine: null,
    details: null,
    write_mode: 'confirmation' as WriteMode,
    dbt_catalog: null,
    dbt_manifest: null,
    public: false
  }) satisfies Database

export const getDefaultDetailsForEngine = (engine: Engine) => {
  switch (engine) {
    case 'postgres':
      return { host: '', port: 5432, user: '', password: '', database: '' }
    case 'mysql':
      return { host: '', port: 3306, user: '', password: '', database: '' }
    case 'snowflake':
      // No database or schema field - connection-level only, will auto-discover databases
      return {
        account: '',
        user: '',
        role: '',
        warehouse: '',
        private_key_pem: null,
        private_key_passphrase: ''
      }
    case 'sqlite':
      return { filename: '' }
    case 'bigquery':
      // project_id is the database equivalent in BigQuery
      return { project_id: '', service_account_json: null }
    case 'motherduck':
      // No database field - connection-level only, will auto-discover databases
      return { token: '' }
    case 'oracle':
      // No database field - connection-level only, will auto-discover databases
      return { host: '', port: 1521, user: '', password: '', service_name: '', sid: '' }
    default:
      engine satisfies never
      throw new Error('Unsupported engine')
  }
}

export const getDatabaseTypeName = (engine: Engine) => {
  const engineNames: Record<Engine, string> = {
    postgres: 'PostgreSQL',
    mysql: 'MySQL',
    snowflake: 'Snowflake',
    sqlite: 'SQLite',
    bigquery: 'BigQuery',
    motherduck: 'MotherDuck',
    oracle: 'Oracle'
  }
  return engineNames[engine] || engine
}

export const useDatabasesStore = defineStore('databases', () => {
  // --------------------------------------------------------------------------
  // STATE
  // --------------------------------------------------------------------------
  const databases = ref<Database[]>([])
  const databaseSelectedId = ref<string | null>(
    localStorage.getItem('databaseId') ? (localStorage.getItem('databaseId') as string) : null
  )

  // --------------------------------------------------------------------------
  // GETTERS
  // --------------------------------------------------------------------------
  const databaseSelected = computed<Database>(() => {
    return databases.value.find((db) => db.id === databaseSelectedId.value) ?? ({} as Database)
  })

  const sortedDatabases = computed(() => {
    return [...databases.value].sort((a, b) => a.createdAt.getTime() - b.createdAt.getTime())
  })

  // --------------------------------------------------------------------------
  // ACTIONS
  // --------------------------------------------------------------------------
  async function fetchDatabases({ refresh }: { refresh: boolean }) {
    if (databases.value.length > 0 && !refresh) return

    databases.value = await axios.get('/api/databases').then((res) => {
      return res.data.map((db: Database) => ({
        ...db,
        createdAt: new Date(db.createdAt)
      }))
    })

    // If there's no database selected yet, and we got some from the API:
    if (databases.value.length > 0 && databaseSelectedId.value === null) {
      databaseSelectedId.value = databases.value[0].id
    }
  }

  function fetchDatabaseTables(databaseId: string) {
    return axios.get(`/api/databases/${databaseId}/schema`).then((res) => res.data)
  }

  function updateDatabase(id: string, database: Database) {
    return axios.put(`/api/databases/${id}`, database)
  }

  function createDatabase(database: Database): Promise<Database> {
    return axios.post('/api/databases', database).then((res) => res.data)
  }

  function deleteDatabase(id: string): Promise<void> {
    return axios.delete(`/api/databases/${id}`).then(() => {
      databases.value = databases.value.filter((db) => db.id !== id)
    })
  }

  function getDatabaseById(id: string) {
    return axios.get('/api/databases').then((res) => res.data.find((db: Database) => db.id === id))
  }

  function hasOnlyPublicDatabases() {
    return databases.value.every((db) => db.public)
  }

  function syncDatabaseMetadata(databaseId: string) {
    return axios.post(`/api/databases/${databaseId}/sync-metadata`).then((res) => res.data)
  }

  function getSyncStatus(databaseId: string) {
    return axios.get(`/api/databases/${databaseId}/sync-status`).then((res) => res.data)
  }

  function shareDatabaseToOrganisation(
    databaseId: string,
    shareToOrganisation: boolean
  ): Promise<Database> {
    return axios
      .put(`/api/databases/${databaseId}/share`, {
        share_to_organisation: shareToOrganisation
      })
      .then((res) => {
        // Update the database in the store
        const index = databases.value.findIndex((db) => db.id === databaseId)
        if (index !== -1) {
          databases.value[index] = { ...databases.value[index], ...res.data }
        }
        return res.data
      })
  }

  // Return everything you want available in the store
  return {
    // state
    databases,
    databaseSelectedId,
    // getters
    databaseSelected,
    sortedDatabases,
    hasOnlyPublicDatabases,
    // actions
    fetchDatabases,
    fetchDatabaseTables,
    updateDatabase,
    createDatabase,
    deleteDatabase,
    getDatabaseById,
    syncDatabaseMetadata,
    getSyncStatus,
    shareDatabaseToOrganisation
  }
})
