<template>
  <Form @submit="handleSave" class="space-y-4">
    <!-- Database Type Display (read-only when editing) -->
    <div class="max-w-lg" v-if="mode === 'edit'">
      <label class="block text-sm font-medium text-gray-700">Database Type</label>
      <div
        v-if="database.engine"
        class="mt-1 text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md border border-gray-300"
      >
        {{ getDatabaseTypeName(database.engine) }}<br />
        <i class="text-xs text-gray-500">Database type cannot be changed after creation</i>
      </div>
    </div>

    <!-- Connection Form -->
    <div v-if="database.engine" class="max-w-lg">
      <DatabaseConnectionForm
        v-if="database.details"
        v-model="database.details"
        :engine="database.engine"
        :layout="mode === 'edit' ? 'stack' : 'grid'"
        :show-engine-title="mode === 'edit'"
        :show-name-field="true"
        :name-value="database.name"
        :name-required="true"
        :user-required="mode === 'create'"
        :password-required="mode === 'create' && database.engine !== 'sqlite'"
        name-placeholder="My Database Connection"
        description-placeholder="Database used for X,Y and Z..."
        :write-mode="database.write_mode"
        @update:write-mode="database.write_mode = $event"
        @update:name="database.name = $event"
      />
    </div>

    <!-- Test Connection Button (for create mode) -->
    <Button
      v-if="mode === 'create' && connectionStatus?.type !== 'success'"
      :is-loading="isTestingConnection"
      :disabled="!canTestConnection || isTestingConnection"
      @click="testConnection"
    >
      <template #loading>Testing Connection...</template>
      Test Connection
    </Button>

    <!-- Connection Status Alert -->
    <ConnectionStatusAlert
      class="max-w-lg"
      :status="connectionStatus?.type || null"
      :message="connectionStatus?.message || ''"
    />

    <div v-if="mode === 'edit' && database.id" class="max-w-lg">
      <DatabaseGithubSettings :database-id="database.id" />
    </div>
  </Form>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button'
import axios from '@/plugins/axios'
import { useContextsStore } from '@/stores/contexts'
import {
  getDatabaseTypeName,
  getDefaultDetailsForEngine,
  makeEmptyDatabase,
  useDatabasesStore,
  type Database,
  type Engine
} from '@/stores/databases'
import { Form } from 'vee-validate'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import ConnectionStatusAlert from './ConnectionStatusAlert.vue'
import DatabaseConnectionForm from './DatabaseConnectionForm.vue'
import DatabaseGithubSettings from './DatabaseGithubSettings.vue'

interface Props {
  mode: 'create' | 'edit'
  databaseId?: string | null
  engine: Engine | null
}

const props = withDefaults(defineProps<Props>(), {
  databaseId: null,
  engine: null
})

const emit = defineEmits<{
  saved: [database: any]
  error: [error: any]
  'connection-tested': [success: boolean]
}>()

// Stores
const databasesStore = useDatabasesStore()
const contextsStore = useContextsStore()

// State
const database = reactive<Database>(makeEmptyDatabase())
if (props.engine) {
  database.engine = props.engine
}
const isTestingConnection = ref(false)
const isSaving = ref(false)
const connectionStatus = ref<{ type: 'success' | 'error'; message: string } | null>(null)

// Computed
const canTestConnection = computed(() => {
  if (!database.engine) return false

  const details = database.details
  if (!details) return false
  switch (database.engine) {
    case 'postgres':
      return details.host && details.user && details.database
    case 'mysql':
      return details.host && details.user && details.database
    case 'snowflake':
      return details.account && details.user && details.private_key_pem
    case 'sqlite':
      return details.filename
    case 'bigquery':
      return details.project_id
    case 'motherduck':
      return details.token
    case 'oracle':
      return details.host && (details.service_name || details.sid)
    default:
      database.engine satisfies never
      return false
  }
})

const canSave = computed(() => {
  if (props.mode === 'edit') return true
  return connectionStatus.value?.type === 'success'
})

// Initialize database data
onMounted(async () => {
  if (props.databaseId) {
    const selectedDatabase = await databasesStore.getDatabaseById(props.databaseId)
    Object.assign(database, selectedDatabase)
  }
})

// TODO: SHOULD IT BE IN DATABASECONNECTIONFORM?
// Watch for engine changes
watch(
  () => database.engine,
  (newEngine) => {
    if (newEngine && !database.details) {
      database.details = getDefaultDetailsForEngine(newEngine)
    }
    connectionStatus.value = null
  },
  { immediate: true }
)

watch(
  () => database.details,
  () => {
    connectionStatus.value = null
  },
  { deep: true }
)

// Methods
const testConnection = async () => {
  isTestingConnection.value = true
  connectionStatus.value = null

  try {
    const response = await axios.post('/api/databases/test-connection', {
      engine: database.engine,
      details: database.details
    })

    if (response.data.success) {
      connectionStatus.value = {
        type: 'success',
        message: response.data.message
      }
      emit('connection-tested', true)
    } else {
      connectionStatus.value = {
        type: 'error',
        message: response.data.message
      }
      emit('connection-tested', false)
    }
  } catch (error: any) {
    connectionStatus.value = {
      type: 'error',
      message:
        error.response?.data?.message ||
        error.message ||
        'Failed to connect to database. Please check your credentials and try again.'
    }
    emit('connection-tested', false)
  } finally {
    isTestingConnection.value = false
  }
}

const handleSave = async () => {
  isSaving.value = true

  try {
    let result
    if (database.id) {
      result = await databasesStore.updateDatabase(database.id, database)
    } else {
      result = await databasesStore.createDatabase(database)
      // Set the new database as the selected context
      await databasesStore.fetchDatabases({ refresh: true })
      contextsStore.setSelectedContext(`database-${result.id}`)
    }

    emit('saved', result)
  } catch (error: any) {
    console.error('Database save failed:', error)
    const errorMessage =
      error?.response?.data?.message ||
      error?.response?.data?.error ||
      error.message ||
      'Database save failed'

    connectionStatus.value = {
      type: 'error',
      message: errorMessage
    }
    emit('error', error)
  } finally {
    isSaving.value = false
  }
}

// Expose methods for parent components
defineExpose({
  testConnection,
  save: handleSave,
  database,
  canSave,
  canTestConnection,
  connectionStatus
})
</script>
