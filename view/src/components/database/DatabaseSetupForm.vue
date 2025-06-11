<template>
  <div class="space-y-6">
    <!-- Step 1: Database Type Selection -->
    <div v-if="currentStep === 0" class="space-y-6">
      <DatabaseTypeSelector
        v-model="databaseConfig.engine"
        layout="cards"
        :included-types="['postgres', 'mysql', 'snowflake', 'bigquery']"
        @update:model-value="onDatabaseTypeSelected"
      />
    </div>

    <!-- Step 2: Connection Details -->
    <div v-if="currentStep === 1" class="space-y-6">
      <div class="text-center">
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Database Connection Details</h2>
        <p class="text-gray-600">
          Enter your {{ getDatabaseTypeName() }} connection details to establish a secure
          connection.
        </p>
      </div>

      <Form @submit="testConnection" class="space-y-6 max-w-lg mx-auto">
        <DatabaseConnectionForm
          v-model="databaseConfig.details"
          :engine="databaseConfig.engine"
          :name-value="databaseConfig.name"
          @update:name="databaseConfig.name = $event"
          layout="grid"
          :show-engine-title="false"
          :user-required="true"
          :password-required="false"
          :safe-mode="databaseConfig.safe_mode"
          :show-name-field="true"
          @update:safe-mode="databaseConfig.safe_mode = $event"
        />

        <!-- Test Connection Button -->
        <div class="flex justify-center pt-4">
          <button
            type="submit"
            :disabled="isTestingConnection"
            class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="!isTestingConnection">Test Connection</span>
            <span v-else class="flex items-center">
              <svg
                class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                ></circle>
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Testing Connection...
            </span>
          </button>
        </div>

        <!-- Connection Status -->
        <div v-if="connectionStatus" class="mt-4">
          <div
            v-if="connectionStatus.type === 'success'"
            class="bg-green-50 border border-green-200 rounded-md p-4"
          >
            <div class="flex">
              <CheckCircleIcon class="h-5 w-5 text-green-400" aria-hidden="true" />
              <div class="ml-3">
                <h3 class="text-sm font-medium text-green-800">Connection Successful</h3>
                <div class="mt-2 text-sm text-green-700">
                  <p>{{ connectionStatus.message }}</p>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="bg-red-50 border border-red-200 rounded-md p-4">
            <div class="flex">
              <div class="w-full">
                <h3 class="text-sm font-medium text-red-800">Connection Failed</h3>
                <div class="mt-2 text-sm text-red-700 w-full break-words">
                  <p>{{ connectionStatus.message }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Form>
    </div>

    <!-- Navigation Buttons -->
    <div class="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
      <button
        v-if="currentStep > 0"
        @click="previousStep"
        class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        <ArrowLeftIcon class="w-4 h-4 mr-2" />
        Previous
      </button>
      <div v-else></div>

      <button
        v-if="currentStep < 1"
        @click="nextStep"
        :disabled="!canProceedToNextStep"
        class="inline-flex items-center px-6 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Continue
        <ArrowRightIcon class="w-4 h-4 ml-2" />
      </button>

      <button
        v-else
        @click="saveDatabase"
        :disabled="!canProceedToNextStep || isSaving"
        class="inline-flex items-center px-6 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span v-if="!isSaving">{{ saveButtonText }}</span>
        <span v-else class="flex items-center">
          <svg
            class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            ></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          Saving...
        </span>
        <CheckIcon class="w-4 h-4 ml-2" v-if="!isSaving" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from '@/plugins/axios'
import { useDatabasesStore } from '@/stores/databases'
import {
  ArrowLeftIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  CheckIcon,
  CircleStackIcon,
  CommandLineIcon,
  CubeIcon,
  TableCellsIcon
} from '@heroicons/vue/24/outline'
import { Form } from 'vee-validate'
import { computed, readonly, ref } from 'vue'
import DatabaseConnectionForm from './DatabaseConnectionForm.vue'
import DatabaseTypeSelector from './DatabaseTypeSelector.vue'

interface DatabaseFormData {
  name: string
  description: string
  engine: string
  details: any
  safe_mode: boolean
}

interface Props {
  saveButtonText?: string
  onSaveSuccess?: () => void
  showSteps?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  saveButtonText: 'Save Database',
  showSteps: true
})

const emit = defineEmits<{
  'database-saved': [database: any]
  'save-error': [error: any]
}>()

// Stores
const databasesStore = useDatabasesStore()

// State
const currentStep = ref(0)
const isTestingConnection = ref(false)
const isSaving = ref(false)
const connectionStatus = ref<{ type: 'success' | 'error'; message: string } | null>(null)

const databaseConfig = ref<DatabaseFormData>({
  name: '',
  description: '',
  engine: '',
  details: {
    host: '',
    port: '',
    user: '',
    password: '',
    database: '',
    filename: '',
    account: '',
    schema: '',
    role: '',
    warehouse: '',
    project_id: '',
    service_account_json: null
  },
  safe_mode: true
})

// Database types
const databaseTypes = [
  {
    value: 'postgres',
    name: 'PostgreSQL',
    description: 'Popular open-source database',
    icon: CircleStackIcon,
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600'
  },
  {
    value: 'mysql',
    name: 'MySQL',
    description: "World's most popular database",
    icon: TableCellsIcon,
    iconBg: 'bg-orange-100',
    iconColor: 'text-orange-600'
  },
  {
    value: 'snowflake',
    name: 'Snowflake',
    description: 'Cloud data platform',
    icon: CubeIcon,
    iconBg: 'bg-cyan-100',
    iconColor: 'text-cyan-600'
  },
  {
    value: 'bigquery',
    name: 'BigQuery',
    description: "Google's data warehouse",
    icon: CommandLineIcon,
    iconBg: 'bg-green-100',
    iconColor: 'text-green-600'
  }
]

// Computed properties
const canProceedToNextStep = computed(() => {
  switch (currentStep.value) {
    case 0:
      return databaseConfig.value.engine !== ''
    case 1:
      return connectionStatus.value?.type === 'success'
    default:
      return false
  }
})

// Methods
const onDatabaseTypeSelected = (engine: string) => {
  databaseConfig.value.engine = engine
  databaseConfig.value.details = getDefaultDetailsForEngine(engine)
}

const getDefaultDetailsForEngine = (engine: string) => {
  switch (engine) {
    case 'postgres':
      return { host: '', port: 5432, user: '', password: '', database: '' }
    case 'mysql':
      return { host: '', port: 3306, user: '', password: '', database: '' }
    case 'snowflake':
      return {
        account: '',
        user: '',
        password: '',
        database: '',
        schema: '',
        role: '',
        warehouse: ''
      }
    case 'bigquery':
      return { project_id: '', service_account_json: null }
    default:
      return {}
  }
}

const getDatabaseTypeName = () => {
  const dbType = databaseTypes.find((db) => db.value === databaseConfig.value.engine)
  return dbType?.name || 'Database'
}

const testConnection = async () => {
  isTestingConnection.value = true
  connectionStatus.value = null

  try {
    // Call the real test connection API
    const response = await axios.post('/api/databases/test-connection', {
      engine: databaseConfig.value.engine,
      details: databaseConfig.value.details
    })

    if (response.data.success) {
      connectionStatus.value = {
        type: 'success',
        message: response.data.message
      }
    } else {
      connectionStatus.value = {
        type: 'error',
        message: response.data.message
      }
    }
  } catch (error: any) {
    connectionStatus.value = {
      type: 'error',
      message:
        error.response?.data?.message ||
        error.message ||
        'Failed to connect to database. Please check your credentials and try again.'
    }
  } finally {
    isTestingConnection.value = false
  }
}

const nextStep = () => {
  if (currentStep.value < 1) {
    currentStep.value++
  }
}

const previousStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const saveDatabase = async () => {
  isSaving.value = true

  try {
    // Create database with the same structure as DatabaseEdit.vue
    const databaseData = {
      id: null,
      name: databaseConfig.value.name,
      description: databaseConfig.value.description,
      engine: databaseConfig.value.engine,
      details: databaseConfig.value.details,
      safe_mode: databaseConfig.value.safe_mode,
      dbt_catalog: null,
      dbt_manifest: null
    } as any

    const createdDatabase = await databasesStore.createDatabase(databaseData)

    // Set the created database as selected
    databasesStore.setDatabaseSelected(createdDatabase)

    // Refresh the databases list
    await databasesStore.fetchDatabases({ refresh: true })

    // Emit success event
    emit('database-saved', createdDatabase)

    // Call success callback if provided
    if (props.onSaveSuccess) {
      props.onSaveSuccess()
    }
  } catch (error) {
    console.error('Database save failed:', error)
    const errorMessage =
      (error as any)?.response?.data?.message || (error as Error).message || 'Database save failed'
    emit('save-error', error)
    alert('Database save failed: ' + errorMessage)
  } finally {
    isSaving.value = false
  }
}

// Public methods for parent components
defineExpose({
  saveDatabase,
  testConnection,
  databaseConfig: readonly(databaseConfig),
  canProceedToNextStep,
  currentStep: readonly(currentStep)
})
</script>
