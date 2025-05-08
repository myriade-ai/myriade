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
    <div class="sm:col-span-6">
      <base-input name="Name" v-model="database.name" rules="required" />
      <base-input
        name="Description"
        v-model="database.description"
        placeholder="Database used for X,Y and Z..."
      />

      <base-field name="Engine">
        <div class="select">
          <select
            v-model="database.engine"
            class="block w-full max-w-lg rounded-md border-gray-300 shadow-xs focus:border-blue-500 focus:ring-blue-500 sm:max-w-xs sm:text-sm"
          >
            <option>postgres</option>
            <option>sqlite</option>
            <option>snowflake</option>
            <option>mysql</option>
          </select>
        </div>
      </base-field>

      <div class="mt-4 text-sm text-gray-500" v-if="database.engine === 'postgres'">
        <p>Postgres connection details</p>
        <base-input
          name="Host"
          v-model="database.details.host"
          placeholder="localhost"
          rules="required"
        />
        <base-input name="Port" v-model="database.details.port" type="number" />
        <base-input name="User" v-model="database.details.user" />
        <base-input-password
          name="Password"
          v-model="database.details.password"
          placeholder="Enter password"
        />
        <base-input name="Database" v-model="database.details.database" rules="required" />
      </div>
      <div class="mt-4 text-sm text-gray-500" v-if="database.engine === 'mysql'">
        <p>Mysql connection details</p>
        <base-input
          name="Host"
          v-model="database.details.host"
          placeholder="localhost"
          rules="required"
        />
        <base-input name="Port" v-model="database.details.port" type="number" />
        <base-input name="User" v-model="database.details.user" />
        <base-input-password
          name="Password"
          v-model="database.details.password"
          placeholder="Enter password"
        />
        <base-input name="Database" v-model="database.details.database" rules="required" />
      </div>
    </div>
    <div class="mt-4 text-sm text-gray-500" v-if="database.engine === 'sqlite'">
      <p>Sqlite connection details</p>
      <base-input name="Path" v-model="database.details.filename" rules="required" />
    </div>
    <div class="mt-4 text-sm text-gray-500" v-if="database.engine === 'snowflake'">
      <p>Snowflake connection details</p>
      <base-input name="Account" v-model="database.details.account" rules="required" />
      <base-input name="User" v-model="database.details.user" rules="required" />
      <base-input-password
        name="Password"
        v-model="database.details.password"
        placeholder="Enter password"
        rules="required"
      />
      <base-input name="Database" v-model="database.details.database" rules="required" />
      <base-input name="Schema" v-model="database.details.schema" />
      <base-input name="Role" v-model="database.details.role" />
      <base-input name="Warehouse" v-model="database.details.warehouse" />
    </div>

    <div class="mt-4 block text-sm font-medium text-gray-700" @click="toggleDbtSupport">
      <p>DBT Support <span v-if="isDbtSupportOpen">▼</span><span v-else>▶</span></p>
    </div>
    <div v-if="isDbtSupportOpen">
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

    <div class="py-5">
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
import BaseField from '@/components/base/BaseField.vue'
import BaseInput from '@/components/base/BaseInput.vue'
import BaseInputPassword from '@/components/base/BaseInputPassword.vue'
import BaseSwitch from '@/components/base/BaseSwitch.vue'
import router from '@/router'
import { useDatabasesStore } from '@/stores/databases'
import { ArrowLeftIcon } from '@heroicons/vue/24/solid'
import { Form } from 'vee-validate'
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const apiError = ref(null)
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
  const databaseId = parseInt(route.params.id as string)
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

const clickDelete = () => {
  if (deleteDatabase(database.value.id)) {
    router.push({ name: 'DatabaseList' })
  }
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
  return apiError.value?.includes('timeout')
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
</script>
