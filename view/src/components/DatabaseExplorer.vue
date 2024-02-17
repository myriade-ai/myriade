<template>
  <div class="bg-white overflow-hidden sm:rounded-lg sm:shadow cursor-pointer select-none">
    <div class="bg-white px-4 py-5 border-b border-gray-200 sm:px-6">
      <h3 class="text-lg leading-6 font-medium text-gray-900">Database</h3>
    </div>
    <ul role="list" class="divide-y divide-gray-200">
      <div class="px-4 py-2" v-if="tables?.length === 0">
        No table available. <br />Please contact support.
      </div>
      <input
        type="text"
        placeholder="search table"
        class="block w-full max-w-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
        id="searchTables"
        v-model="searchTablesInput"
      />
      <li
        v-for="(table, ind) in filteredTables"
        @click="onClick(ind)"
        v-on:dblclick="onDblClick(ind)"
      >
        <div class="block hover:bg-gray-50">
          <div class="px-4 py-4 sm:px-6">
            <div class="flex items-center justify-between">
              <div
                class="text-sm font-medium truncate"
                :class="isTableUsed(table) ? 'text-blue-600' : 'text-gray-600'"
              >
                {{ table.schema }}.{{ table.name }}
              </div>
            </div>
            <div class="flex justify-between">
              <div class="sm:flex">
                <div class="flex items-center text-sm text-gray-500">
                  {{ table.description }}
                </div>
              </div>
            </div>
            <div v-for="column in table.columns" v-if="ind == showTableIndex">
              <div class="mt-2 flex justify-between">
                <div class="sm:flex">
                  <div class="flex items-center text-sm text-gray-500">
                    {{ column.name }}: {{ column.type }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </li>
      <div v-if="filteredTables.length == 0" class="block hover:bg-gray-50">
        <p class="px-4 py-4 sm:px-6">No tables</p>
      </div>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref, watchEffect, computed } from 'vue'
import { useDatabases } from '../stores/databases'
import { querySQL, runQuery } from '../stores/query'

const { databaseSelectedId, fetchDatabaseTables } = useDatabases()

interface Column {
  name: string
  type: string
}

interface Table {
  name: string
  schema: string
  description: string
  columns: Column[]
  used: Boolean // information if the table is used in the query
}

const showTableIndex = ref(null)
const searchTablesInput = ref('')
const tables = ref<Table[]>([])

function extractTables(sqlQuery) {
  // Regular expression to match table names following FROM, JOIN, and UPDATE keywords
  // This regex is basic and might need adjustments to cover all SQL syntax variations
  const regex = /\b(FROM|JOIN|UPDATE|INTO)\s+("?\w+"?\."?\w+"?|"\w+"|\w+)/gi

  let match
  const extables = []

  // Use a loop to find matches and push the table name to the tables array
  while ((match = regex.exec(sqlQuery)) !== null) {
    // This ensures the match was not empty or undefined
    if (match[2]) {
      extables.push(match[2].replaceAll('"', ''))
    }
  }

  // Remove duplicates by converting to a Set and back to an Array
  return [...new Set(extables)]
}

const extractedTables = computed(() => {
  return extractTables(querySQL.value)
})

const isTableUsed = (table: Table) => {
  for (const extractedTable of extractedTables.value) {
    if (extractedTable.includes('.')) {
      const [schema, name] = extractedTable.split('.')
      if (table.schema === schema && table.name === name) {
        return true
      }
    } else if (table.name === extractedTable) {
      return true
    }
  }
  return false
}

const sortedTables = computed(() => {
  // make a copy of the tables array and sort it by the used property
  return [...tables.value].sort((a, b) => {
    if (isTableUsed(a) && !isTableUsed(b)) {
      return -1
    }
    if (!isTableUsed(a) && isTableUsed(b)) {
      return 1
    }
    return 0
  })
})

const filteredTables = computed(() => {
  return sortedTables.value.filter((table: Table) => {
    return table.name.includes(searchTablesInput.value)
  })
})

const onClick = (tableInd: number) => {
  if (showTableIndex.value == tableInd) {
    showTableIndex.value = null
  } else {
    showTableIndex.value = tableInd
  }
}

const onDblClick = (tableInd: number) => {
  const tableSelected = tables.value[tableInd]
  querySQL.value = `SELECT * FROM "${tableSelected.schema}"."${tableSelected.name}";`
  runQuery()
}

watchEffect(async () => {
  const selectedDatabaseId = databaseSelectedId.value
  if (selectedDatabaseId) {
    tables.value = await fetchDatabaseTables(selectedDatabaseId)
  }
})
</script>
