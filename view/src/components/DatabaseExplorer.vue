<template>
  <div class="bg-white overflow-hidden sm:rounded-lg sm:shadow cursor-pointer select-none">
    <div class="bg-white px-4 py-5 border-b border-gray-200 sm:px-6">
      <h3 class="text-lg leading-6 font-medium text-gray-900">Database</h3>
    </div>
    <ul role="list" class="divide-y divide-gray-200">
      <div class="px-4 py-2" v-if="tables?.length === 0">
        No table available. <br />Please contact support.
      </div>
      <li v-for="(table, ind) in tables" @click="onClick(ind)" v-on:dblclick="onDblClick(ind)">
        <div href="#" class="block hover:bg-gray-50">
          <div class="px-4 py-4 sm:px-6">
            <div class="flex items-center justify-between">
              <div class="text-sm font-medium text-blue-600 truncate">
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
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref, watchEffect } from 'vue'
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
}

const showTableIndex = ref(0)
const tables = ref<Table[]>([])

const onClick = (tableInd: number) => {
  showTableIndex.value = tableInd
}

const onDblClick = (tableInd: number) => {
  console.log(databaseSelectedId)
  const tableSelected = tables.value[tableInd]
  console.log(tableSelected)

  querySQL.value = `SELECT * FROM "${tableSelected.schema}"."${tableSelected.name}";`
  runQuery()
}

watchEffect(async () => {
  console.log('databaseSelected', databaseSelectedId.value)
  const selectedDatabaseId = databaseSelectedId.value
  if (selectedDatabaseId) {
    tables.value = await fetchDatabaseTables(selectedDatabaseId)
    console.log('tables', tables.value)
  }
})
</script>
