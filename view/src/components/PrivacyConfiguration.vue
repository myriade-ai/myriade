<template>
  <div class="space-y-6">
    <!-- Removed duplicate big heading to avoid redundancy with page title -->

    <!-- Legend / descriptions -->
    <div class="bg-gray-50 p-4 rounded-md">
      <h2 class="text-sm font-semibold mb-2">Privacy options</h2>
      <ul class="space-y-1 text-sm text-gray-600">
        <li v-for="opt in privacyOptions" :key="String(opt.key)">
          <span class="font-medium">{{ opt.label }}:</span> {{ opt.description }}
        </li>
      </ul>
    </div>

    <!-- User Group Selector -->
    <!-- <div class="flex items-center space-x-3">
      <label class="font-medium text-gray-700" for="userGroup">User group</label>
      <select
        id="userGroup"
        v-model="selectedGroup"
        class="border-gray-300 rounded-md shadow-xs focus:border-indigo-500 focus:ring-indigo-500 text-sm"
      >
        <option v-for="g in userGroups" :key="g.key" :value="g.key">{{ g.name }}</option>
      </select>
    </div> -->

    <!-- Tables & Columns -->
    <div class="space-y-4">
      <div
        v-for="table in tables"
        :key="table.name"
        class="border rounded-md divide-y divide-gray-200"
      >
        <!-- Table header -->
        <details>
          <summary
            class="flex justify-between items-center cursor-pointer px-4 py-2 bg-gray-50 hover:bg-gray-100"
          >
            <div class="flex flex-col">
              <div class="flex items-center space-x-2">
                <span class="font-medium">{{ table.schema }}.{{ table.name }}</span>
                <span class="text-xs text-gray-500" v-if="statsForTable(table)">
                  ({{ statsForTable(table) }})
                </span>
              </div>
              <span class="text-xs text-gray-500">{{ table.description }}</span>
            </div>
            <span class="text-xs text-gray-400">{{ table.type }}</span>
          </summary>

          <!-- Column list -->
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200 table-fixed">
              <thead class="bg-gray-50">
                <tr>
                  <th
                    class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/4"
                  >
                    Column
                  </th>
                  <th
                    class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/4"
                  >
                    Type
                  </th>
                  <th
                    class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/4"
                  >
                    Description
                  </th>
                  <th
                    class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/4"
                  >
                    Privacy
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="col in table.columns" :key="col.name">
                  <td class="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                    {{ col.name }}
                  </td>
                  <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-500">{{ col.type }}</td>
                  <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                    {{ col.description }}
                  </td>
                  <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-700">
                    <select
                      v-model="col.privacy[selectedGroup]"
                      :disabled="!isTextType(col.type)"
                      class="border-gray-300 rounded-md shadow-xs focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                      :class="[
                        col.privacy[selectedGroup] &&
                        col.privacy[selectedGroup] !== 'Default' &&
                        col.privacy[selectedGroup] !== 'Visible'
                          ? 'bg-blue-100'
                          : 'text-gray-700',
                        !isTextType(col.type) ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : ''
                      ]"
                    >
                      <option v-for="opt in privacyOptions" :key="String(opt.key)" :value="opt.key">
                        {{ opt.label }}
                      </option>
                    </select>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </details>
      </div>
    </div>

    <!-- Save Button -->
    <div class="flex justify-end">
      <button
        @click="saveConfig"
        :disabled="!hasUnsavedChanges"
        :class="[
          'px-4 py-2 rounded-md text-sm focus:outline-hidden focus:ring-2 focus:ring-offset-2',
          hasUnsavedChanges
            ? 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500'
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
        ]"
      >
        Save Configuration
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps, onMounted, ref, watch } from 'vue'
import axios from '../plugins/axios'

// -----------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------
type PrivacyOptionKey = 'Default' | 'Visible' | 'Encrypted' | 'Masked' | 'Redacted'

interface PrivacyOptionDef {
  key: PrivacyOptionKey
  label: string
  description: string
}

interface Column {
  name: string
  type: string
  description: string
  // Map of userGroupKey -> privacy setting key
  privacy: Record<string, PrivacyOptionKey>
}

interface Table {
  name: string
  schema: string
  type: string
  description: string
  columns: Column[]
}

interface UserGroup {
  key: string
  name: string
}

// -----------------------------------------------------------------------
// Reactive data (fetched from database schema API)
// -----------------------------------------------------------------------
const props = defineProps<{ databaseId: string }>()

const userGroups = ref<UserGroup[]>([
  // { key: 'users', name: 'Users' },
  { key: 'llm', name: 'LLM / AI Provider' }
])

const privacyOptions: PrivacyOptionDef[] = [
  {
    key: 'Default',
    label: 'Default (Visible)',
    description:
      'No explicit privacy rule set. The value will inherit the default behaviour (Visible).'
  },
  /* {
    key: 'Visible',
    label: 'Visible',
    description: 'Value is shown as-is. (e.g. benjamin.dupont@example.com)'
  }, */
  {
    key: 'Encrypted',
    label: 'Encrypted',
    description: 'Value is replaced by an encrypted ID (e.g. EMAIL_1234).'
  }
  /* {
    key: 'Masked',
    label: 'Masked',
    description: 'Value is partially hidden (e.g. b********t@example.com).'
  }, */
  /* {
    key: 'Redacted',
    label: 'Redacted',
    description: 'Value is removed entirely and replaced with *REDACTED*.'
  } */
]

// Holds fetched tables / columns and original copy to check changes
const tables = ref<Table[]>([])
const originalTables = ref<Table[]>([])

// -----------------------------------------------------------------------
// Fetch helpers
// -----------------------------------------------------------------------
async function fetchSchema() {
  if (!props.databaseId) {
    tables.value = []
    return
  }

  try {
    const rawTables = await axios
      .get(`/api/databases/${props.databaseId}/schema`)
      .then((res) => res.data)

    // Map API response to the interface expected by the UI
    tables.value = rawTables.map((t: any) => ({
      ...t,
      type: t.is_view ? 'VIEW' : 'TABLE',
      columns: t.columns.map((c: any) => {
        const basePrivacy: Record<string, PrivacyOptionKey> = c.privacy ?? {}
        // Fill missing groups with Default
        userGroups.value.forEach((g) => {
          if (basePrivacy[g.key] === undefined || basePrivacy[g.key] === null) {
            basePrivacy[g.key] = 'Default'
          }
        })

        return {
          name: c.name,
          type: c.type ?? c.datatype ?? '',
          description: c.description ?? '',
          privacy: basePrivacy
        }
      })
    }))

    // Store original snapshot for dirty-checking
    originalTables.value = JSON.parse(JSON.stringify(tables.value))
  } catch (err) {
    console.error('Failed to fetch schema', err)
    tables.value = []
  }
}

// Fetch at component mount and whenever selected database changes
onMounted(fetchSchema)
watch(
  () => props.databaseId,
  () => {
    fetchSchema()
  }
)

// -----------------------------------------------------------------------
// Dirty state computation
// -----------------------------------------------------------------------
const hasUnsavedChanges = computed(() => {
  return JSON.stringify(tables.value) !== JSON.stringify(originalTables.value)
})

// Selected group state
const selectedGroup = ref(userGroups.value[0].key)

// -----------------------------------------------------------------------
// Utility to check if a column type is text-based
// -----------------------------------------------------------------------
const isTextType = (type: string) => /^(text|varchar)/i.test(type)

// -----------------------------------------------------------------------
// Methods
// -----------------------------------------------------------------------
function saveConfig() {
  if (!props.databaseId) return
  if (!hasUnsavedChanges.value) return

  // Deep-copy tables before sending (remove Vue proxies)
  const payload = JSON.parse(JSON.stringify(tables.value))

  axios
    .put(`/api/databases/${props.databaseId}/privacy`, payload)
    .then(() => {
      // Update snapshot
      originalTables.value = JSON.parse(JSON.stringify(tables.value))
    })
    .catch((err) => {
      console.error(err)
      alert('Failed to save configuration')
    })
}

// -----------------------------------------------------------------------
// Utility: stats per table for current group
// -----------------------------------------------------------------------
function statsForTable(table: Table) {
  const counts: Record<PrivacyOptionKey, number> = {
    Default: 0,
    Visible: 0,
    Encrypted: 0,
    Masked: 0,
    Redacted: 0
  }

  table.columns.forEach((col) => {
    const key = (col.privacy[selectedGroup.value] as PrivacyOptionKey) || 'Default'
    counts[key] = (counts[key] || 0) + 1
  })

  const parts: string[] = []
  ;['Visible', 'Masked', 'Encrypted', 'Redacted'].forEach((k) => {
    const c = counts[k as PrivacyOptionKey]
    if (c) parts.push(`${c} ${k.toLowerCase()}`)
  })

  return parts.join(', ')
}
</script>
