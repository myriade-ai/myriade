<template>
  <div class="space-y-6">
    <Field
      name="Connection Name"
      :model-value="nameValue"
      @update:model-value="$emit('update:name', $event)"
      placeholder="A nice name for your connection, like 'My Production Database'"
      :rules="nameRequired ? 'required' : ''"
    />

    <!-- PostgreSQL/MySQL Fields -->
    <div v-if="engine === 'postgres' || engine === 'mysql'" class="space-y-4">
      <div class="text-sm text-muted-foreground" v-if="showEngineTitle">
        <p>{{ getDatabaseTypeName(engine) }} connection details</p>
      </div>
      <div :class="layout === 'grid' ? 'grid grid-cols-1' : 'space-y-4'">
        <Field
          name="Host"
          v-model="details.host"
          :rules="isRequiredField('host') ? 'required' : ''"
          placeholder="localhost"
        />
        <!-- Information box for IP whitelisting -->
        <BaseNotification
          v-if="!shouldHideNetworkConfig"
          color="warning"
          title="Cloud Database Network Configuration"
          :message="`If necessary, please whitelist the following IP in your cloud-database network rules: ${serverIp}`"
          class="bg-warning-50"
        />
        <Field
          name="Port"
          v-model="details.port"
          type="number"
          :placeholder="engine === 'postgres' ? '5432' : '3306'"
          :rules="isRequiredField('port') ? 'required' : ''"
        />
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field
          :name="layout === 'grid' ? 'Username' : 'User'"
          v-model="details.user"
          :rules="userRequired ? 'required' : ''"
          class="w-full"
        />
        <InputPassword name="Password" v-model="details.password" placeholder="Enter password" />
      </div>
      <Field
        name="Database"
        v-model="details.database"
        :rules="isRequiredField('database') ? 'required' : ''"
      />
    </div>

    <!-- SQLite Fields -->
    <div v-if="engine === 'sqlite'" class="space-y-4">
      <div class="text-sm text-muted-foreground" v-if="showEngineTitle">
        <p>SQLite connection details</p>
      </div>
      <Field
        name="Path"
        v-model="details.filename"
        :rules="isRequiredField('filename') ? 'required' : ''"
        placeholder="/path/to/database.sqlite"
      />
    </div>

    <!-- Snowflake Fields -->
    <div v-if="engine === 'snowflake'" class="space-y-4">
      <div class="text-sm text-muted-foreground" v-if="showEngineTitle">
        <p>Snowflake connection details</p>
      </div>
      <Field
        name="Account Identifier"
        v-model="details.account"
        :rules="isRequiredField('account') ? 'required' : ''"
        placeholder="ORGANIZATION-ACCOUNT"
      />
      <Field
        :name="layout === 'grid' ? 'Username' : 'User'"
        v-model="details.user"
        :rules="isRequiredField('user') ? 'required' : ''"
      />

      <!-- RSA Key Authentication -->
      <div class="space-y-4">
        <div class="space-y-2">
          <label class="block text-sm font-medium text-muted-foreground"
            >Private Key File <span class="text-red-500">*</span></label
          >
          <div class="flex items-center justify-center w-full">
            <label
              class="flex flex-col items-center justify-center w-full h-32 border-2 border-input border-dashed rounded-lg cursor-pointer bg-muted hover:bg-muted"
              :class="{
                'border-primary-400 bg-primary-50': details.private_key_pem,
                'border-red-400 bg-red-50 dark:bg-red-900/20': privateKeyError
              }"
            >
              <div class="flex flex-col items-center justify-center pt-5 pb-6">
                <CloudArrowUpIcon class="w-8 h-8 mb-4 text-muted-foreground" />
                <p class="mb-2 text-sm text-muted-foreground">
                  <span class="font-semibold">Click to upload</span> your private key
                </p>
                <p class="text-xs text-muted-foreground">.pem, .key, or .p8 files (max 1MB)</p>
                <p v-if="details.private_key_pem" class="mt-2 text-sm text-primary-600 font-medium">
                  ✓ Private key file uploaded
                </p>
                <p v-if="privateKeyError" class="mt-2 text-sm text-red-600 font-medium">
                  {{ privateKeyError }}
                </p>
              </div>
              <input
                type="file"
                class="hidden"
                accept=".pem,.key,.p8"
                @change="handlePrivateKeyUpload"
              />
            </label>
          </div>
        </div>
        <InputPassword
          name="Private Key Passphrase (Optional)"
          v-model="details.private_key_passphrase"
          placeholder="Enter passphrase if key is encrypted"
        />
      </div>

      <div :class="layout === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-4' : 'space-y-4'">
        <Field
          name="Warehouse"
          v-model="details.warehouse"
          placeholder="COMPUTE_WH"
          :rules="isRequiredField('warehouse') ? 'required' : ''"
        />
        <Field
          name="Role"
          v-model="details.role"
          placeholder="ACCOUNTADMIN"
          :rules="isRequiredField('role') ? 'required' : ''"
        />
      </div>
      <Field
        name="Database (Optional)"
        v-model="details.database"
        placeholder="Leave empty to access all databases"
      />
    </div>

    <!-- BigQuery Fields -->
    <div v-if="engine === 'bigquery'" class="space-y-4">
      <div class="text-sm text-muted-foreground" v-if="showEngineTitle">
        <p>BigQuery connection details</p>
      </div>
      <Field
        name="Project ID"
        v-model="details.project_id"
        :rules="isRequiredField('project_id') ? 'required' : ''"
        placeholder="your-gcp-project-id"
      />
      <div class="space-y-2">
        <label class="block text-sm font-medium text-muted-foreground">
          Service Account JSON Key
          <span class="text-xs font-normal text-muted-foreground"
            >(optional - will use Application Default Credentials if not provided)</span
          >
        </label>
        <div class="flex items-center justify-center w-full">
          <label
            class="flex flex-col items-center justify-center w-full h-64 border-2 border-input border-dashed rounded-lg cursor-pointer bg-muted hover:bg-muted"
            :class="{
              'border-primary-400 bg-primary-50': details.service_account_json
            }"
          >
            <div class="flex flex-col items-center justify-center pt-5 pb-6">
              <CloudArrowUpIcon class="w-8 h-8 mb-4 text-muted-foreground" />
              <p class="mb-2 text-sm text-muted-foreground">
                <span class="font-semibold">Click to upload</span> your service account JSON
              </p>
              <p class="text-xs text-muted-foreground">JSON files only</p>
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
      <Field
        name="Database (Optional)"
        v-model="details.database"
        placeholder="Leave empty to access all datasets"
      />
    </div>

    <!-- MotherDuck Fields -->
    <div v-if="engine === 'motherduck'" class="space-y-4">
      <div class="text-sm text-muted-foreground" v-if="showEngineTitle">
        <p>MotherDuck connection details</p>
      </div>
      <Field
        name="Token"
        v-model="details.token"
        :rules="isRequiredField('token') ? 'required' : ''"
        placeholder="Enter your token"
      />
      <Field
        name="Database (Optional)"
        v-model="details.database"
        placeholder="Leave empty to access all databases"
      />
    </div>

    <!-- Oracle Fields -->
    <div v-if="engine === 'oracle'" class="space-y-4">
      <div class="text-sm text-muted-foreground" v-if="showEngineTitle">
        <p>Oracle connection details</p>
      </div>
      <div :class="layout === 'grid' ? 'grid grid-cols-1' : 'space-y-4'">
        <Field
          name="Host"
          v-model="details.host"
          :rules="isRequiredField('host') ? 'required' : ''"
          placeholder="localhost"
        />
        <!-- Information box for IP whitelisting -->
        <BaseNotification
          v-if="!shouldHideNetworkConfig"
          color="warning"
          title="Cloud Database Network Configuration"
          :message="`If necessary, please whitelist the following IP in your cloud-database network rules: ${serverIp}`"
          class="bg-warning-50"
        />
        <Field
          name="Port"
          v-model="details.port"
          type="number"
          placeholder="1521"
          :rules="isRequiredField('port') ? 'required' : ''"
        />
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field
          :name="layout === 'grid' ? 'Username' : 'User'"
          v-model="details.user"
          :rules="userRequired ? 'required' : ''"
          class="w-full"
        />
        <InputPassword name="Password" v-model="details.password" placeholder="Enter password" />
      </div>
      <div class="space-y-2">
        <p class="text-sm text-muted-foreground">
          Provide either Service Name (recommended) or SID:
        </p>
        <Field
          name="Service Name"
          v-model="details.service_name"
          placeholder="ORCL (recommended)"
          :rules="isRequiredField('service_name') ? 'required' : ''"
        />
        <Field
          name="SID"
          v-model="details.sid"
          placeholder="Alternative to service name"
          :rules="isRequiredField('sid') ? 'required' : ''"
        />
      </div>
    </div>

    <!-- Write Mode Selection -->
    <div class="p-4 bg-muted rounded-lg max-w-lg" v-if="!enginesWithoutSafeMode.includes(engine)">
      <h3 class="text-sm font-medium text-foreground">Write Operation Handling</h3>
      <p class="text-sm text-muted-foreground mb-4">
        Choose how to handle write operations like CREATE, DROP, INSERT, UPDATE, DELETE
      </p>

      <RadioGroup
        :model-value="writeMode || 'confirmation'"
        @update:model-value="$emit('update:writeMode', $event)"
        class="space-y-3"
      >
        <div class="flex items-start space-x-3">
          <RadioGroupItem value="read-only" id="read-only" class="mt-1" />
          <label for="read-only" class="cursor-pointer flex-1">
            <div class="text-sm font-medium text-foreground">Read-only</div>
            <div class="text-xs text-muted-foreground">Block all write operations entirely</div>
          </label>
        </div>

        <div class="flex items-start space-x-3">
          <RadioGroupItem value="confirmation" id="confirmation" class="mt-1" />
          <label for="confirmation" class="cursor-pointer flex-1">
            <div class="text-sm font-medium text-foreground">Ask for confirmation</div>
            <div class="text-xs text-muted-foreground">
              Prompt user to confirm write operations (recommended)
            </div>
          </label>
        </div>

        <div class="flex items-start space-x-3">
          <RadioGroupItem value="skip-confirmation" id="skip-confirmation" class="mt-1" />
          <label for="skip-confirmation" class="cursor-pointer flex-1">
            <div class="text-sm font-medium text-foreground">Allow all operations</div>
            <div class="text-xs text-muted-foreground">
              Execute all queries without confirmation
            </div>
          </label>
        </div>
      </RadioGroup>
    </div>
  </div>
</template>

<script setup lang="ts">
import BaseNotification from '@/components/base/BaseNotification.vue'
import Field from '@/components/ui/input/Field.vue'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { useServerInfo } from '@/composables/useServerInfo'
import { getDatabaseTypeName, getDefaultDetailsForEngine, type Engine } from '@/stores/databases'
import { CloudArrowUpIcon } from '@heroicons/vue/24/outline'
import { computed, ref, watch } from 'vue'
import InputPassword from '../ui/input/InputPassword.vue'

const { serverIp } = useServerInfo()

type WriteMode = 'read-only' | 'confirmation' | 'skip-confirmation'

interface Props {
  modelValue: Record<string, unknown> // this is *details* only
  engine: Engine
  layout?: 'stack' | 'grid'
  showEngineTitle?: boolean
  showNameField?: boolean
  nameValue?: string
  nameRequired?: boolean
  userRequired?: boolean
  passwordRequired?: boolean
  namePlaceholder?: string
  descriptionPlaceholder?: string
  writeMode?: WriteMode
}
const props = defineProps<Props>()
defineEmits(['update:writeMode', 'update:name'])
const details = defineModel({ type: Object, required: true })

// State for private key upload errors
const privateKeyError = ref<string | null>(null)

// Check if we should show network configuration notification
const shouldHideNetworkConfig = computed(() => {
  const host = details.value?.host?.trim()
  return !host || 'localhost'.startsWith(host) || '127.0.0.1'.startsWith(host)
})

const enginesWithoutSafeMode: Engine[] = ['snowflake', 'motherduck']

// Watch for engine changes and reset details
watch(
  () => props.engine,
  (newEngine) => {
    const newDetails = getDefaultDetailsForEngine(newEngine)
    if (details.value) {
      Object.keys(details.value).forEach((key) => {
        if (!(key in newDetails)) {
          delete details.value[key]
        }
      })
      Object.assign(details.value, newDetails)
    } else {
      details.value = newDetails
    }
    privateKeyError.value = null
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

const requiredFieldsByEngine: Record<Engine, string[]> = {
  postgres: ['host', 'user', 'database'],
  mysql: ['host', 'user', 'database'],
  snowflake: ['account', 'user', 'private_key_pem'],
  sqlite: ['filename'],
  bigquery: ['project_id'],
  motherduck: ['token'],
  oracle: ['host', 'user']
}

const isRequiredField = (field: string): boolean => {
  const requiredFields = requiredFieldsByEngine[props.engine] || []
  return requiredFields.includes(field)
}

const handlePrivateKeyUpload = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return

  // Reset error state
  privateKeyError.value = null

  // Validate file extension
  const validExtensions = ['.pem', '.key', '.p8']
  const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()

  if (!validExtensions.includes(fileExtension)) {
    privateKeyError.value = 'Invalid file type. Please upload a .pem, .key, or .p8 file'
    details.value.private_key_pem = undefined
    return
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const content = e.target?.result as string

      // Basic validation: check if it looks like a PEM file
      if (
        content.includes('-----BEGIN') &&
        content.includes('PRIVATE KEY') &&
        content.includes('-----END')
      ) {
        details.value.private_key_pem = content
        privateKeyError.value = null
      } else {
        privateKeyError.value = 'Invalid private key format. File must be in PEM format.'
        details.value.private_key_pem = undefined
      }
    } catch {
      privateKeyError.value = 'Failed to read file. Please try again.'
      details.value.private_key_pem = undefined
    }
  }

  reader.onerror = () => {
    privateKeyError.value = 'Failed to read file. Please try again.'
    details.value.private_key_pem = undefined
  }

  reader.readAsText(file)
}
</script>
