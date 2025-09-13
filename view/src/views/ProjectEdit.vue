<template>
  <div class="min-h-screen bg-sidebar/50">
    <Form @submit="clickSave" class="max-w-7xl mx-auto px-4 py-4">
      <!-- Project Name -->
      <div class="mb-6">
        <Field name="Name" v-model="project.name" rules="required" />
      </div>

      <!-- Project Description -->
      <div class="mb-6">
        <div class="mb-4">
          <Label for="description" class="text-lg font-semibold">Project Description</Label>
          <p class="text-sm text-gray-600 mt-1">
            This description helps the Agent understand your project context and provide better
            assistance.
          </p>
        </div>

        <div class="mb-4 p-4 border-l-4 border-blue-500 bg-blue-50">
          <div class="flex items-start gap-3">
            <LightBulbIcon class="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div class="text-sm text-gray-700">
              <div class="font-medium text-blue-800 mb-2">When to create a project:</div>
              <ul class="space-y-1 text-gray-600">
                <li>• Focusing on a specific subset of tables</li>
                <li>• Managing complex business domains that need context explanation</li>
                <li>• Repeatedly analyzing the same business problem or metrics</li>
              </ul>
            </div>
          </div>
        </div>

        <Textarea
          name="Description"
          v-model="project.description"
          placeholder="Example:

      Financial Performance Analysis Project

      This project focuses on analyzing quarterly financial performance using our ERP database. We work with accounting, sales, and procurement tables to track revenue trends, cost optimization, and profitability by business unit.

      Key business context:
      - Revenue recognition follows a subscription model with monthly recurring billing
      - Cost centers are organized by department with shared infrastructure costs
      - We need to track EBITDA margins and compare against industry benchmarks

      Regular analysis includes monthly P&L reviews, quarterly board reporting, and annual budget planning."
          class="h-96 bg-white"
        />
      </div>

      <!-- Database Selection -->
      <div class="mb-6">
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
      <div v-if="selectedDatabase" class="mb-6">
        <label class="block text-gray-700 text-sm font-medium mb-2" for="tables">
          Tables linked to this project
        </label>
        <DatabaseTableSelector :groups="groups" v-model="selectedItems" />
      </div>

      <BaseAlert class="mt-5" v-if="apiError">
        <template #title> There is an error 😔 </template>{{ apiError }}
      </BaseAlert>

      <div class="fixed bottom-6 right-6 flex space-x-2 z-50">
        <Button v-if="!isNew" @click.prevent="clickDelete" type="button" variant="secondary">
          Delete
        </Button>
        <Button type="submit"> Save </Button>
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
import { useDatabasesStore } from '@/stores/databases'
import type { Project, ProjectTable } from '@/stores/projects'
import { useProjectsStore } from '@/stores/projects'
import { LightBulbIcon } from '@heroicons/vue/24/outline'
import { ErrorMessage, Form, Field as VField } from 'vee-validate'
import { computed, ref, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { createProject, updateProject, deleteProject, fetchProjectById } = useProjectsStore()
const databasesStore = useDatabasesStore()
await databasesStore.fetchDatabases({ refresh: false })

const route = useRoute()
const router = useRouter()
const apiError = ref<string | null>(null)

const selectedItems = ref<Item[]>([])
const groups = ref<Group[]>([])

const project = ref({
  id: null,
  name: '',
  description: '',
  databaseId: null,
  tables: []
} as Project)

const tables = ref<TableData[]>([])

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

const selectedDatabase = computed(() => {
  if (!databasesStore.databases) {
    return null
  }
  return databasesStore.databases.find((db) => db.id === project.value.databaseId)
})

const fetchDatabaseSchema = async () => {
  if (project.value.databaseId) {
    // Fetch schema (fetchDatabaseTables) and tables for the selected database
    // and update the groups and tables state
    const fetchedTables = await databasesStore.fetchDatabaseTables(project.value.databaseId)

    // Transform the fetched tables to match our TableData interface
    const tableData: TableData[] = (fetchedTables as FetchedTable[]).map((table) => ({
      name: table.name,
      schema: table.schema,
      description: table.description || '',
      columns: table.columns || []
    }))

    tables.value = tableData
    groups.value = transformTablesToGroups(tableData)

    // update selectedItems with project.tables
    // 1. extract items from groups
    const items = groups.value.flatMap((group) => group.items)
    // 2. filter items by project.tables
    const filteredItems = items.filter((item) => {
      return project.value.tables.some((table) => {
        return `${table.schemaName}.${table.tableName}` === item.id
      })
    })
    // 3. update selectedItems
    selectedItems.value = filteredItems
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

function projectTablesFromSelectedItems(selectedItems: Item[]): ProjectTable[] {
  // Take id of items and return project tables
  return selectedItems.map((item) => {
    return {
      databaseName: selectedDatabase.value?.name as string,
      schemaName: item.id.split('.')[0],
      tableName: item.id.split('.')[1]
    }
  })
}

// on selectedItems change, update project.tables
watch(
  selectedItems,
  (newVal) => {
    project.value.tables = projectTablesFromSelectedItems(newVal)
  },
  { deep: true }
)

const isNew = computed(() => route.params.id === 'new')
if (!isNew.value) {
  const projectId = Array.isArray(route.params.id) ? route.params.id[0] : route.params.id
  project.value = await fetchProjectById(projectId)
  await fetchDatabaseSchema()
}
</script>
