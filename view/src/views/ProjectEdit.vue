<template>
  <Form @submit="clickSave" class="max-w-7xl mx-auto px-4">
    <nav class="flex items-center justify-between px-4 sm:px-0">
      <div class="-mt-px flex w-0 flex-1">
        <a
          @click.prevent="clickCancel"
          class="inline-flex items-center border-t-2 border-transparent pt-4 pr-1 text-sm font-medium text-gray-500 hover:text-gray-700 cursor-pointer"
        >
          <ArrowLeftIcon class="mr-3 h-5 w-5 text-gray-400" aria-hidden="true" />
          Return to all projects
        </a>
      </div>
    </nav>
    <br />
    <div class="sm:col-span-6">
      <base-input name="Name" v-model="project.name" rules="required" />
      <label class="block text-gray-700 text-sm font-medium mt-2 mb-1" for="description"
        >Description</label
      >
      <textarea
        name="Description"
        v-model="project.description"
        placeholder="Project used for X,Y and Z..."
        class="w-full h-96 rounded-md border-gray-300 shadow-xs focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
      />
      <base-field name="Database">
        <Field
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
        </Field>
        <ErrorMessage name="databaseId" class="text-error-500 text-sm mt-1" />
      </base-field>
      <div v-if="selectedDatabase" class="mt-2">
        <label class="block text-gray-700 text-sm font-medium mt-2" for="tables"
          >Tables linked to this project</label
        >
        <BaseMultiSelect class="w-full max-w-lg" :groups="groups" v-model="selectedItems" />
      </div>
    </div>

    <hr class="mt-5" />

    <BaseAlert class="mt-5" v-if="apiError">
      <template #title> There is an error 😔 </template>{{ apiError }}
    </BaseAlert>

    <div class="py-5">
      <div class="flex justify-end">
        <button
          @click.prevent="clickDelete"
          type="button"
          class="rounded-md border border-gray-300 bg-white py-2 px-4 text-sm font-medium text-gray-700 shadow-xs hover:bg-gray-50 focus:outline-hidden focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        >
          Delete
        </button>
        <button
          type="submit"
          class="ml-3 inline-flex justify-center rounded-md border border-transparent bg-primary-600 py-2 px-4 text-sm font-medium text-white shadow-xs hover:bg-primary-700 focus:outline-hidden focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
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
import type { Group, Item } from '@/components/base/BaseMultiSelect.vue'
import BaseMultiSelect from '@/components/base/BaseMultiSelect.vue'
import router from '@/router'
import { useDatabasesStore } from '@/stores/databases'
import type { Project, ProjectTable } from '@/stores/projects'
import { useProjectsStore } from '@/stores/projects'
import { ArrowLeftIcon } from '@heroicons/vue/24/solid'
import { ErrorMessage, Field, Form } from 'vee-validate'
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const { createProject, updateProject, deleteProject, fetchProjectById } = useProjectsStore()
const databasesStore = useDatabasesStore()
await databasesStore.fetchDatabases({ refresh: false })

const route = useRoute()
const apiError = ref(null)

const selectedItems = ref<Item[]>([])
const groups = ref<Group[]>([])

const project = ref({
  id: null,
  name: '',
  description: '',
  databaseId: null,
  tables: []
} as Project)

const tables = ref([
  {
    name: 'table1',
    database: 'xxx',
    schema: 'yyy'
  },
  {
    name: 'table2',
    database: 'xxx',
    schema: 'yyy'
  }
])

const clickDelete = async () => {
  if (await deleteProject(project.value.id)) {
    router.push({ name: 'ProjectList' })
  }
}

const clickCancel = () => {
  router.push({ name: 'ProjectList' })
}

const clickSave = async () => {
  try {
    if (isNew.value) {
      project.value = await createProject(project.value)
    } else {
      await updateProject(project.value.id as string, project.value)
    }
    router.push({ name: 'ProjectList' })
  } catch (error) {
    console.error(error)
    apiError.value = error.response.data.message
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
    tables.value = await databasesStore.fetchDatabaseTables(project.value.databaseId)
    groups.value = transformTablesToGroups(tables.value)

    // update selectedItems with project.tables
    // 1. exctract items from groups
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

function transformTablesToGroups(tables: any[]) {
  const schemaGroups: Record<
    string,
    {
      id: string
      label: string
      items: any[]
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

    schemaGroups[table.schema].items.push({
      id: `${table.schema}.${table.name}`,
      label: table.name,
      columns: table.columns.map((column: any) => ({
        name: column.name,
        description: column.description
      })),
      description: table.description
    })
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
  const projectId = route.params.id
  project.value = await fetchProjectById(projectId)
  await fetchDatabaseSchema()
}
</script>
