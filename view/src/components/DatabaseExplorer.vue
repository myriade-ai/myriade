<template>
  <div class="bg-white overflow-hidden sm:rounded-lg sm:shadow cursor-pointer select-none">
    <div class="bg-white px-4 py-5 border-b border-gray-200 sm:px-6">
      <h3 class="text-lg leading-6 font-medium text-gray-900">Database</h3>
    </div>
    <ul role="list" class="divide-y divide-gray-200">
      <div class="px-4 py-2" v-if="tables?.length === 0">
        No table available. <br />Please contact support.
      </div>
      <DatabaseExplorerItems
        v-for="(table, ind) in usedTables"
        :key="ind"
        :table="table"
        :showColumns="table.name == showTableKey"
        @click="onClick(table.name)"
        @dblclick="onDblClick(table)"
      />
      <input
        type="text"
        placeholder="search table"
        class="block w-full max-w-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
        id="searchTables"
        v-model="searchTablesInput"
      />
      <DatabaseExplorerItems
        v-for="(table, ind) in filteredTables"
        :key="ind"
        :table="table"
        :showColumns="table.name == showTableKey"
        @click="onClick(table.name)"
        @dblclick="onDblClick(table)"
      />
      <div v-if="filteredTables.length == 0" class="block hover:bg-gray-50">
        <p class="px-4 py-4 sm:px-6">No tables</p>
      </div>
    </ul>
  </div>
</template>

<script setup lang="ts">
import DatabaseExplorerItems from '@/components/DatabaseExplorerItems.vue'
import { useDatabasesStore } from '@/stores/databases'
import { useQueryStore } from '@/stores/query'
import type { Table } from '@/stores/tables'
import { computed, ref, watchEffect } from 'vue'

const databasesStore = useDatabasesStore()
const queryStore = useQueryStore()
const tables = ref<Table[]>([])
const showTableKey = ref<string | null>(null)

watchEffect(async () => {
  const selectedDatabaseId = databasesStore.databaseSelectedId
  if (selectedDatabaseId) {
    tables.value = await databasesStore.fetchDatabaseTables(selectedDatabaseId)
  }
})

const searchTablesInput = ref('')

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
  return extractTables(queryStore.querySQL)
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
    return (
      table.name.toLocaleLowerCase().includes(searchTablesInput.value.toLocaleLowerCase()) &&
      !isTableUsed(table)
    )
  })
})

const usedTables = computed(() => {
  return tables.value.filter((table: Table) => {
    return isTableUsed(table)
  })
})

const onClick = (key: string) => {
  if (showTableKey.value == key) {
    showTableKey.value = null
  } else {
    showTableKey.value = key
  }
}

const onDblClick = (table: Table) => {
  queryStore.querySQL = `SELECT * FROM "${table.schema}"."${table.name}";`
  searchTablesInput.value = '' // reset input
  queryStore.runQuery()
}
</script>
