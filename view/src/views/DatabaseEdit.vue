<template>
  <Form @submit="clickSave" class="max-w-7xl mx-auto px-4">
    <nav class="flex items-center justify-between px-4 sm:px-0">
      <div class="-mt-px flex w-0 flex-1">
        <a
          @click.prevent="clickCancel"
          class="inline-flex items-center border-t-2 border-transparent pt-4 pr-1 text-sm font-medium text-gray-500 hover:text-gray-700 cursor-pointer"
        >
          <ArrowLeftIcon class="mr-3 h-5 w-5 text-gray-400" aria-hidden="true" />
          Return to all databases
        </a>
      </div>
    </nav>
    <br />
    <div class="sm:col-span-6" v-if="!isNew">
      <DatabaseConnectionForm
        v-model="database"
        :engine="database.engine"
        layout="stack"
        :show-engine-title="true"
        :name-required="true"
        name-placeholder=""
        description-placeholder="Database used for X,Y and Z..."
      />

      <DatabaseTypeSelector
        v-model="database.engine"
        layout="dropdown"
        :included-types="['postgres', 'sqlite', 'snowflake', 'mysql']"
      />

      <div class="mt-4 block text-sm font-medium text-gray-700" @click="toggleDbtSupport">
        <p>DBT Support <span v-if="isDbtSupportOpen">▼</span><span v-else>▶</span></p>
      </div>
    </div>

    <div v-else class="sm:col-span-6">
      <DatabaseSetupForm
        save-button-text="Save Database"
        @database-saved="onDatabaseSaved"
        @save-error="onSaveError"
      />
    </div>

    <div v-if="isDbtSupportOpen && !isNew">
      <p class="text-sm text-gray-500">
        Add DBT json files so the AI can leverage DBT (experimental)
      </p>
      <div class="flex flex-col">
        <label class="text-gray-700">Catalog</label>
        <a
          v-if="databasesStore.databaseSelected.dbt_catalog"
          :href="
            'data:text/json;charset=utf-8,' +
            encodeURIComponent(JSON.stringify(databasesStore.databaseSelected.dbt_catalog))
          "
          download="catalog.json"
          class="text-blue-600 hover:text-blue-800"
          >catalog.json</a
        >
        <input
          type="file"
          @change="handleCatalogFileUpload"
          class="mb-2 cursor-pointer file:mr-4 file:py-2 file:px-4 file:rounded-sm file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />

        <label class="text-gray-700 mt-4">Manifest</label>
        <a
          v-if="databasesStore.databaseSelected.dbt_manifest"
          :href="
            'data:text/json;charset=utf-8,' +
            encodeURIComponent(JSON.stringify(databasesStore.databaseSelected.dbt_manifest))
          "
          download="manifest.json"
          class="text-blue-600 hover:text-blue-800"
          >manifest.json</a
        >
        <input
          type="file"
          @change="handleManifestFileUpload"
          class="mb-2 cursor-pointer file:mr-4 file:py-2 file:px-4 file:rounded-sm file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
      </div>
    </div>

    <BaseSwitch v-model="database.safe_mode" class="mt-1">
      <span class="text-gray-700">Safe mode (read-only)</span>
    </BaseSwitch>

    <hr class="mt-5" />

    <BaseAlert class="mt-5" v-if="apiError">
      <template #title> There is an error 😔 </template>
      {{ apiError }}
      <!-- Server IP whitelist information section - always visible -->
      <br />
      <br />
      <div v-if="isConnectionTimeout">
        <p>
          The server was unable to establish a connection to your database. This is often due to
          firewall rules or network restrictions that prevent our server from accessing your
          database.
        </p>
        <p class="font-medium">
          Please ensure that you have whitelisted the IP address of this server ({{ serverIp }}) in
          your database
        </p>
      </div>
    </BaseAlert>

    <div class="py-5" v-if="!isNew">
      <div class="flex justify-end">
        <button
          @click.prevent="clickDelete"
          type="button"
          class="rounded-md border border-gray-300 bg-white py-2 px-4 text-sm font-medium text-gray-700 shadow-xs hover:bg-gray-50 focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Delete
        </button>
        <button
          type="submit"
          class="ml-3 inline-flex justify-center rounded-md border border-transparent bg-blue-600 py-2 px-4 text-sm font-medium text-white shadow-xs hover:bg-blue-700 focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Save
        </button>
      </div>
    </div>
  </Form>
</template>

<script setup lang="ts">
import BaseAlert from '@/components/base/BaseAlert.vue'
import BaseSwitch from '@/components/base/BaseSwitch.vue'
import DatabaseConnectionForm from '@/components/database/DatabaseConnectionForm.vue'
import DatabaseSetupForm from '@/components/database/DatabaseSetupForm.vue'
import DatabaseTypeSelector from '@/components/database/DatabaseTypeSelector.vue'
import router from '@/router'
import { useDatabasesStore } from '@/stores/databases'
import { ArrowLeftIcon } from '@heroicons/vue/24/solid'
import { Form } from 'vee-validate'
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const apiError = ref<string | null>(null)
const serverIp = ref('')

const getServerIp = async () => {
  try {
    const response = await fetch('/api/server-info')
    const data = await response.json()
    serverIp.value = data.ip
  } catch (error) {
    console.error('Error fetching server IP:', error)
  }
}
getServerIp()

// Type our response to include server_ip
const database = ref({
  id: null,
  name: '',
  description: '',
  engine: 'postgres',
  details: {
    user: '',
    password: '',
    database: ''
  },
  safe_mode: true,
  dbt_catalog: null,
  dbt_manifest: null
} as any)

const databasesStore = useDatabasesStore()
const { selectDatabaseById, createDatabase, updateDatabase, deleteDatabase } = databasesStore

const isNew = computed(() => route.params.id === 'new')
if (!isNew.value) {
  const databaseId = route.params.id as string
  await selectDatabaseById(databaseId)
  // Copy the databaseSelected to the database
  database.value.id = databasesStore.databaseSelected.id
  database.value.name = databasesStore.databaseSelected.name
  database.value.engine = databasesStore.databaseSelected.engine
  database.value.details = databasesStore.databaseSelected.details

  database.value.safe_mode = databasesStore.databaseSelected.safe_mode
  database.value.dbt_catalog = databasesStore.databaseSelected.dbt_catalog
  database.value.dbt_manifest = databasesStore.databaseSelected.dbt_manifest
}

const clickDelete = async () => {
  await deleteDatabase(database.value.id)
  router.push({ name: 'DatabaseList' })
}

// Redirect to /databases
const clickCancel = () => {
  router.push({ name: 'DatabaseList' })
}

const clickSave = async () => {
  try {
    if (isNew.value) {
      database.value = await createDatabase(database.value)
    } else {
      await updateDatabase(database.value.id, database.value)
    }
    router.push({ name: 'DatabaseList' })
  } catch (error: any) {
    console.error(error)
    apiError.value =
      error.response?.data?.message || error.message || 'An unexpected error occurred'
  }
}

const isConnectionTimeout = computed(() => {
  return apiError.value?.includes('timeout') || false
})

const handleFileUpload = (event: any, key: 'dbt_catalog' | 'dbt_manifest') => {
  const file = event.target.files[0]
  const reader = new FileReader()
  reader.onload = (event: any) => {
    try {
      database.value[key] = JSON.parse(event.target.result)
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

const isDbtSupportOpen = ref(database.value.dbt_catalog || database.value.dbt_manifest)
const toggleDbtSupport = () => {
  isDbtSupportOpen.value = !isDbtSupportOpen.value
}

const onDatabaseSaved = () => {
  // Handle the event when a new database is saved
  router.push({ name: 'DatabaseList' })
}

const onSaveError = (error: any) => {
  // Handle the event when there's an error during database save
  console.error('Database save error:', error)
}
</script>
