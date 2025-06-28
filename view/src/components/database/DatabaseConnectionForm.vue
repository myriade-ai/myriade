<template>
  <div class="space-y-6">
    <!-- Basic Information -->
    <base-input
      v-if="showNameField"
      name="Connection Name"
      :model-value="nameValue || ''"
      :rules="nameRequired ? 'required' : ''"
      placeholder="A nice name for your connection, like 'My Production Database'"
      @update:model-value="$emit('update:name', $event)"
    />

    <!-- PostgreSQL/MySQL Fields -->
    <div v-if="engine === 'postgres' || engine === 'mysql'" class="space-y-4">
      <div class="text-sm text-gray-500" v-if="showEngineTitle">
        <p>{{ getDatabaseTypeName(engine) }} connection details</p>
      </div>
      <div :class="layout === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-4' : 'space-y-4'">
        <base-input name="Host" v-model="details.host" rules="required" placeholder="localhost" />
        <base-input
          name="Port"
          v-model="details.port"
          type="number"
          :placeholder="engine === 'postgres' ? '5432' : '3306'"
        />
      </div>
      <div :class="layout === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-4' : 'space-y-4'">
        <base-input
          :name="layout === 'grid' ? 'Username' : 'User'"
          v-model="details.user"
          :rules="userRequired ? 'required' : ''"
        />
        <base-input-password
          name="Password"
          v-model="details.password"
          placeholder="Enter password"
          :rules="passwordRequired ? 'required' : ''"
        />
      </div>
      <base-input
        :name="layout === 'grid' ? 'Database Name' : 'Database'"
        v-model="details.database"
        rules="required"
      />
    </div>

    <!-- SQLite Fields -->
    <div v-if="engine === 'sqlite'" class="space-y-4">
      <div class="text-sm text-gray-500" v-if="showEngineTitle">
        <p>SQLite connection details</p>
      </div>
      <base-input
        name="Path"
        v-model="details.filename"
        rules="required"
        placeholder="/path/to/database.sqlite"
      />
    </div>

    <!-- Snowflake Fields -->
    <div v-if="engine === 'snowflake'" class="space-y-4">
      <div class="text-sm text-gray-500" v-if="showEngineTitle">
        <p>Snowflake connection details</p>
      </div>
      <base-input
        name="Account"
        v-model="details.account"
        rules="required"
        placeholder="your-account.snowflakecomputing.com"
      />
      <div :class="layout === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-4' : 'space-y-4'">
        <base-input
          :name="layout === 'grid' ? 'Username' : 'User'"
          v-model="details.user"
          rules="required"
        />
        <base-input-password
          name="Password"
          v-model="details.password"
          placeholder="Enter password"
          rules="required"
        />
      </div>
      <div :class="layout === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-4' : 'space-y-4'">
        <base-input name="Database" v-model="details.database" rules="required" />
        <base-input name="Schema" v-model="details.schema" placeholder="PUBLIC" />
      </div>
      <div :class="layout === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-4' : 'space-y-4'">
        <base-input name="Warehouse" v-model="details.warehouse" placeholder="COMPUTE_WH" />
        <base-input name="Role" v-model="details.role" placeholder="ACCOUNTADMIN" />
      </div>
    </div>

    <!-- BigQuery Fields -->
    <div v-if="engine === 'bigquery'" class="space-y-4">
      <div class="text-sm text-gray-500" v-if="showEngineTitle">
        <p>BigQuery connection details</p>
      </div>
      <base-input
        name="Project ID"
        v-model="details.project_id"
        rules="required"
        placeholder="your-gcp-project-id"
      />
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700"> Service Account JSON Key </label>
        <div class="flex items-center justify-center w-full">
          <label
            class="flex flex-col items-center justify-center w-full h-64 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100"
            :class="{
              'border-primary-400 bg-primary-50': details.service_account_json
            }"
          >
            <div class="flex flex-col items-center justify-center pt-5 pb-6">
              <CloudArrowUpIcon class="w-8 h-8 mb-4 text-gray-500" />
              <p class="mb-2 text-sm text-gray-500">
                <span class="font-semibold">Click to upload</span> your service account JSON
              </p>
              <p class="text-xs text-gray-500">JSON files only</p>
              <p
                v-if="details.service_account_json"
                class="mt-2 text-sm text-primary-600 font-medium"
              >
                ✓ Service account file uploaded
              </p>
            </div>
            <input type="file" class="hidden" accept=".json" @change="handleServiceAccountUpload" />
          </label>
        </div>
      </div>
    </div>

    <!-- Safe Mode Toggle -->
    <div class="p-4 bg-gray-50 rounded-lg max-w-lg">
      <h3 class="text-sm font-medium text-gray-900">Safe Mode (read-only)</h3>
      <p class="text-sm text-gray-500 mb-3">
        When enabled, prevents destructive operations like DROP, DELETE, and UPDATE statements
      </p>
      <label class="relative inline-flex items-center cursor-pointer">
        <input
          type="checkbox"
          :checked="safeMode"
          @change="$emit('update:safeMode', ($event.target as HTMLInputElement).checked)"
          class="sr-only peer"
        />
        <div
          class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"
        ></div>
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
import BaseInput from '@/components/base/BaseInput.vue'
import BaseInputPassword from '@/components/base/BaseInputPassword.vue'
import { getDatabaseTypeName, getDefaultDetailsForEngine } from '@/utils/database'
import { CloudArrowUpIcon } from '@heroicons/vue/24/outline'
import { watch } from 'vue'

interface Props {
  modelValue: Record<string, any> // this is *details* only
  engine: string
  layout?: 'stack' | 'grid'
  showEngineTitle?: boolean
  showNameField?: boolean
  nameValue?: string
  nameRequired?: boolean
  userRequired?: boolean
  passwordRequired?: boolean
  namePlaceholder?: string
  descriptionPlaceholder?: string
  safeMode?: boolean
}
const props = defineProps<Props>()
const emit = defineEmits(['update:safeMode', 'update:name'])
const details = defineModel({ type: Object, required: true })
// Watch for engine changes and reset details
watch(
  () => props.engine,
  (newEngine) => {
    const newDetails = getDefaultDetailsForEngine(newEngine)
    Object.assign(details, newDetails)
  }
)

const handleServiceAccountUpload = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file && file.type === 'application/json') {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        details.value.service_account_json = JSON.parse(e.target?.result as string)
      } catch {
        console.error('Invalid JSON file')
      }
    }
    reader.readAsText(file)
  }
}
</script>
