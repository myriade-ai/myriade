<template>
  <div class="min-h-screen bg-sidebar/50">
    <Form @submit="clickSave" class="max-w-7xl mx-auto px-4 py-4">
      <div class="mb-4 p-4 border-l-4 border-yellow-500 bg-yellow-50">
        <div class="flex items-start gap-3">
          <LightBulbIcon class="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
          <div class="text-sm text-gray-700">
            <div class="font-medium text-yellow-800 mb-2">When to create a project?</div>
            <ul class="space-y-1 text-gray-600">
              <li>
                • When you lots of tables, and you want to focus on a specific subset of tables
              </li>
              <li>
                • When you want to analyze a specific business domain that needs context explanation
              </li>
              <li>• When you want to analyze the same business problem or metrics repeatedly</li>
            </ul>
          </div>
        </div>
      </div>
      <!-- Project Name -->
      <div class="mb-6">
        <Field
          name="Name"
          v-model="project.name"
          rules="required"
          placeholder="eg. 'Company Financial Performance'"
        />
      </div>

      <!-- Project Description -->
      <div class="mb-6">
        <div class="mb-4">
          <Label for="description">Project Description</Label>
          <p class="text-sm text-gray-600 mt-1">
            Provide clear context, as you would to new hire. <br />
          </p>
        </div>
        <Textarea
          name="Description"
          v-model="project.description"
          placeholder="What is your objective?
What are the business rules?
What are the key metrics?
What to be aware of?
"
          class="h-96 bg-white"
        />
      </div>

      <!-- Database Selection -->
      <div class="mb-6" v-if="false">
        <base-field name="Database">
          <VField
            name="databaseId"
            as="select"
            v-model="project.databaseId"
            @change="fetchDatabaseSchema"
            class="block w-full max-w-lg rounded-md border-gray-300 shadow-xs focus:border-primary-500 focus:ring-primary-500 sm:max-w-xs sm:text-sm"
            rules="required"
            :validate-on-change="true"
          >
            <option value="">Select a database</option>
            <option v-for="db in databasesStore.databases" :key="db.id" :value="db.id">
              {{ db.name }}
            </option>
          </VField>
          <ErrorMessage name="databaseId" class="text-error-500 text-sm mt-1" />
        </base-field>
      </div>

      <!-- Tables Selection -->
      <div v-if="selectedDatabase && !isLoading" class="mb-6">
        <label class="block text-gray-700 text-sm font-medium mb-2" for="tables">
          Tables linked to this project
        </label>
        <DatabaseTableSelector :groups="groups" v-model="selectedItems" />
      </div>

      <!-- Loading indicator -->
      <div v-if="isLoading" class="mb-6 text-center py-8">
        <div class="text-gray-600">Loading database schema...</div>
      </div>

      <BaseAlert class="mt-5" v-if="apiError">
        <template #title> There is an error 😔 </template>{{ apiError }}
      </BaseAlert>

      <div class="bottom-6 right-6 flex space-x-2 z-50 py-4 float-right">
        <Button
          variant="destructive"
          v-if="!isNew"
          @click="clickDelete"
          type="button"
          class="cursor-pointer"
        >
          Delete
        </Button>
        <Button type="submit" class="cursor-pointer"> Save </Button>
      </div>
    </Form>
  </div>
</template>

<script setup lang="ts">
import BaseAlert from '@/components/base/BaseAlert.vue'
import BaseField from '@/components/base/BaseField.vue'
import type { Group, Item } from '@/components/base/DatabaseTableSelector.vue'
import DatabaseTableSelector from '@/components/base/DatabaseTableSelector.vue'
import { Button } from '@/components/ui/button'
import Field from '@/components/ui/input/Field.vue'
import Label from '@/components/ui/label/Label.vue'
import { Textarea } from '@/components/ui/textarea'
import { useContextsStore } from '@/stores/contexts'
import { useDatabasesStore } from '@/stores/databases'
import type { Project } from '@/stores/projects'
import { useProjectsStore } from '@/stores/projects'
import { LightBulbIcon } from '@heroicons/vue/24/outline'
import { ErrorMessage, Form, Field as VField } from 'vee-validate'
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { createProject, updateProject, deleteProject, fetchProjectById } = useProjectsStore()
const contextsStore = useContextsStore()
const databasesStore = useDatabasesStore()

const route = useRoute()
const router = useRouter()
const apiError = ref<string | null>(null)
const selectedItems = ref<Item[]>([])
const groups = ref<Group[]>([])
const tables = ref<TableData[]>([])
const isLoading = ref(true)

const selectedDatabaseId = computed(() => contextsStore.getSelectedContextDatabaseId())
const selectedDatabase = computed(() => {
  if (!databasesStore.databases || !selectedDatabaseId.value) {
    return null
  }
  return databasesStore.databases.find((db) => db.id === selectedDatabaseId.value)
})

const project = ref({
  id: null,
  name: '',
  description: '',
  databaseId: selectedDatabaseId.value,
  tables: []
} as Project)

const clickDelete = async () => {
  if (project.value.id && (await deleteProject(project.value.id))) {
    router.push({ name: 'ProjectList' })
  }
}

const clickSave = async () => {
  try {
    if (isNew.value) {
      project.value = await createProject(project.value)
    } else {
      await updateProject(project.value.id as string, project.value)
    }

    await nextTick()

    await router.push('/projects')
  } catch (error: unknown) {
    console.error(error)
    const errorMessage =
      error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { message?: string } } }).response?.data?.message
        : 'An error occurred'
    apiError.value = errorMessage || 'An error occurred'
  }
}

const fetchDatabaseSchema = async () => {
  const databaseId = selectedDatabaseId.value
  if (!databaseId) {
    console.warn('No database ID available for schema fetch')
    return
  }

  try {
    // Fetch schema (fetchDatabaseTables) and tables for the selected database
    const fetchedTables = await databasesStore.fetchDatabaseTables(databaseId)

    // Transform the fetched tables to match our TableData interface
    const tableData: TableData[] = (fetchedTables as FetchedTable[]).map((table) => ({
      name: table.name,
      schema: table.schema,
      description: table.description || '',
      columns: table.columns || []
    }))

    tables.value = tableData
    groups.value = transformTablesToGroups(tableData)

    selectedItems.value = groups.value
      .flatMap((group) => group.items)
      .filter((item) =>
        project.value.tables.some((table) => `${table.schemaName}.${table.tableName}` === item.id)
      )
  } catch (error) {
    console.error('Error fetching database schema:', error)
    apiError.value = 'Failed to load database schema'
  }
}

interface TableColumn {
  name: string
  description?: string
}

interface TableData {
  name: string
  schema: string
  columns: TableColumn[]
  description?: string
}

interface FetchedTable {
  name: string
  schema: string
  columns?: TableColumn[]
  description?: string
}

interface ProjectTable {
  schemaName: string
  tableName: string
}

function transformTablesToGroups(tables: TableData[]) {
  const schemaGroups: Record<
    string,
    {
      id: string
      label: string
      items: Item[]
    }
  > = {}

  tables.forEach((table) => {
    if (!schemaGroups[table.schema]) {
      schemaGroups[table.schema] = {
        id: table.schema,
        label: `Schema ${table.schema}`,
        items: []
      }
    }

    const item: Item = {
      id: `${table.schema}.${table.name}`,
      label: table.name,
      description: table.description || ''
    }

    // Add columns as a custom property (allowed by index signature)
    const itemWithColumns = item as Item & { columns: TableColumn[] }
    itemWithColumns.columns = table.columns.map((column: TableColumn) => ({
      name: column.name,
      description: column.description
    }))

    schemaGroups[table.schema].items.push(itemWithColumns)
  })

  return Object.values(schemaGroups)
}

watch(
  selectedItems,
  (newSelectedItems) => {
    project.value.tables = newSelectedItems.map(
      (item): ProjectTable => ({
        schemaName: item.id.split('.')[0],
        tableName: item.id.split('.')[1]
      })
    )
  },
  { deep: true }
)

const isNew = computed(() => route.params.id === 'new')

// Initialize component data
const initializeComponent = async () => {
  try {
    isLoading.value = true

    if (!isNew.value) {
      const projectId = Array.isArray(route.params.id) ? route.params.id[0] : route.params.id
      project.value = await fetchProjectById(projectId)
    }

    // Always fetch database schema if we have a selected database
    await fetchDatabaseSchema()
  } catch (error) {
    console.error('Error initializing component:', error)
    apiError.value = 'Failed to initialize project data'
  } finally {
    isLoading.value = false
  }
}

// Watch for database ID changes and refetch schema
watch(
  selectedDatabaseId,
  async (newDatabaseId) => {
    if (newDatabaseId) {
      // Update project's database ID when context changes
      project.value.databaseId = newDatabaseId
      await fetchDatabaseSchema()
    }
  },
  { immediate: false }
)

// Initialize when component mounts
initializeComponent()
</script>
