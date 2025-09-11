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

    <!-- DBT Support (edit mode only) -->
    <div v-if="mode === 'edit'" class="max-w-lg">
      <div class="block text-sm font-medium text-gray-700 cursor-pointer" @click="toggleDbtSupport">
        <p>
          DBT Support (experimental) <span v-if="isDbtSupportOpen">▼</span><span v-else>▶</span>
        </p>
      </div>

      <div v-if="isDbtSupportOpen" class="mt-4 space-y-4">
        <p class="text-sm text-gray-500">
          Add DBT json files so the AI can leverage DBT (experimental)
        </p>

        <!-- Catalog Upload -->
        <div class="flex flex-col">
          <label class="text-gray-700">Catalog</label>
          <a
            v-if="database.dbt_catalog"
            :href="
              'data:text/json;charset=utf-8,' +
              encodeURIComponent(JSON.stringify(database.dbt_catalog))
            "
            download="catalog.json"
            class="text-primary-600 hover:text-primary-800"
          >
            catalog.json
          </a>
          <input
            type="file"
            @change="handleCatalogFileUpload"
            class="mb-2 cursor-pointer file:mr-4 file:py-2 file:px-4 file:rounded-sm file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
          />
        </div>

        <!-- Manifest Upload -->
        <div class="flex flex-col">
          <label class="text-gray-700">Manifest</label>
          <a
            v-if="database.dbt_manifest"
            :href="
              'data:text/json;charset=utf-8,' +
              encodeURIComponent(JSON.stringify(database.dbt_manifest))
            "
            download="manifest.json"
            class="text-primary-600 hover:text-primary-800"
          >
            manifest.json
          </a>
          <input
            type="file"
            @change="handleManifestFileUpload"
            class="mb-2 cursor-pointer file:mr-4 file:py-2 file:px-4 file:rounded-sm file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
          />
        </div>
      </div>
    </div>
  </Form>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button'
import axios from '@/plugins/axios'
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

// State
const database = reactive<Database>(makeEmptyDatabase())
if (props.engine) {
  database.engine = props.engine
}
const isTestingConnection = ref(false)
const isSaving = ref(false)
const connectionStatus = ref<{ type: 'success' | 'error'; message: string } | null>(null)
const isDbtSupportOpen = ref(false)

// Computed
const canTestConnection = computed(() => {
  if (!database.engine) return false

  const details = database.details
  if (!details) return false
  switch (database.engine) {
    case 'postgres':
    case 'mysql':
      return details.host && details.user && details.database
    case 'snowflake':
      return details.account && details.user && details.database
    case 'sqlite':
      return details.filename
    case 'bigquery':
      return details.project_id && details.service_account_json
    case 'motherduck':
      return details.token && details.database
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
    console.log('database', database)
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
      // Set as selected and refresh list for create mode
      databasesStore.setDatabaseSelected(result)
      await databasesStore.fetchDatabases({ refresh: true })
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

const handleFileUpload = (event: any, key: 'dbt_catalog' | 'dbt_manifest') => {
  const file = event.target.files[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      database[key] = JSON.parse(e.target?.result as string)
    } catch (error) {
      console.error(`Error parsing JSON for ${key}:`, error)
    }
  }
  reader.readAsText(file)
}

const handleCatalogFileUpload = (event: any) => {
  handleFileUpload(event, 'dbt_catalog')
}

const handleManifestFileUpload = (event: any) => {
  handleFileUpload(event, 'dbt_manifest')
}

const toggleDbtSupport = () => {
  isDbtSupportOpen.value = !isDbtSupportOpen.value
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
