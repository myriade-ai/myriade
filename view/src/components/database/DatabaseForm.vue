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
      <div class="p-4 bg-gray-50 rounded-lg max-w-lg">
        <h3 class="text-sm font-medium text-warning-900">DBT Support (🚧 experimental)</h3>
        <p class="text-sm text-gray-500 mb-4">
          Configure DBT integration by providing a local repository path.
        </p>

        <!-- Repository Path Configuration -->
        <div class="space-y-4">
          <div class="flex flex-col">
            <label class="text-sm font-medium text-gray-700">DBT Repository Path</label>
            <p class="text-xs text-gray-500 mb-2">
              Path to your local DBT project directory (must contain dbt_project.yml)
            </p>
            <div class="flex space-x-2">
              <Input
                type="text"
                v-model="database.dbt_repo_path"
                placeholder="/path/to/your/dbt/project"
                class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <Button
                type="button"
                :disabled="!database.dbt_repo_path || isValidatingRepo"
                :is-loading="isValidatingRepo"
                @click="validateRepository"
                :variant="repoValidationStatus ? 'outline' : 'default'"
              >
                <template #loading>Validating...</template>
                Validate
              </Button>
            </div>

            <!-- Validation Status -->
            <div v-if="repoValidationStatus" class="mt-2">
              <div
                v-if="repoValidationStatus.success"
                class="text-green-600 text-sm flex items-center"
              >
                <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fill-rule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clip-rule="evenodd"
                  />
                </svg>
                {{ repoValidationStatus.message }}
              </div>
              <div v-else class="text-red-600 text-sm flex items-center">
                <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fill-rule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                    clip-rule="evenodd"
                  />
                </svg>
                {{ repoValidationStatus.message }}
              </div>
            </div>

            <!-- Generate Docs Button -->
            <Button
              v-if="database.dbt_repo_path && repoValidationStatus?.success"
              type="button"
              :disabled="isGeneratingDocs"
              :is-loading="isGeneratingDocs"
              @click="generateDbtDocs"
              variant="default"
              class="mt-2"
            >
              <template #loading>Generating...</template>
              Generate DBT Documentation
            </Button>

            <!-- Generation Status -->
            <div v-if="docsGenerationStatus" class="mt-2">
              <div v-if="docsGenerationStatus.success" class="text-green-600 text-sm">
                {{ docsGenerationStatus.message }}
              </div>
              <div v-else class="text-red-600 text-sm">
                {{ docsGenerationStatus.message }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="mode === 'edit' && database.id" class="max-w-lg">
      <DatabaseGithubSettings :database-id="database.id" />
    </div>
  </Form>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
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

// DBT-related state
const isValidatingRepo = ref(false)
const isGeneratingDocs = ref(false)
const repoValidationStatus = ref<{ success: boolean; message: string } | null>(null)
const docsGenerationStatus = ref<{ success: boolean; message: string } | null>(null)

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
      return details.account && details.user && details.database && details.private_key_pem
    case 'sqlite':
      return details.filename
    case 'bigquery':
      return details.project_id && details.service_account_json
    case 'motherduck':
      return details.token && details.database
    case 'oracle':
      return details.host && details.user && details.database
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

const validateRepository = async () => {
  if (!database.dbt_repo_path || !database.id) return

  isValidatingRepo.value = true
  repoValidationStatus.value = null

  try {
    const response = await axios.post(`/api/databases/${database.id}/validate-dbt-repo`, {
      repo_path: database.dbt_repo_path
    })

    repoValidationStatus.value = {
      success: response.data.success,
      message: response.data.message
    }
  } catch (error: any) {
    repoValidationStatus.value = {
      success: false,
      message: error.response?.data?.message || 'Failed to validate repository'
    }
  } finally {
    isValidatingRepo.value = false
  }
}

const generateDbtDocs = async () => {
  if (!database.id) return

  isGeneratingDocs.value = true
  docsGenerationStatus.value = null

  try {
    const response = await axios.post(`/api/databases/${database.id}/generate-dbt-docs`)

    docsGenerationStatus.value = {
      success: response.data.success,
      message: response.data.message
    }

    // Refresh database data to get the generated catalog/manifest
    if (response.data.success && database.id) {
      const updatedDatabase = await databasesStore.getDatabaseById(database.id)
      database.dbt_catalog = updatedDatabase.dbt_catalog
      database.dbt_manifest = updatedDatabase.dbt_manifest
    }
  } catch (error: any) {
    docsGenerationStatus.value = {
      success: false,
      message: error.response?.data?.message || 'Failed to generate documentation'
    }
  } finally {
    isGeneratingDocs.value = false
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
