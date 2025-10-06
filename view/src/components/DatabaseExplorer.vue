<template>
  <Card class="bg-white rounded-lg gap-0 py-2 flex flex-col h-full">
    <CardHeader class="border-b-1">
      <CardTitle class="text-xl"> Database </CardTitle>
    </CardHeader>
    <CardContent class="px-0 flex-1 overflow-hidden">
      <ul role="list" class="divide-y divide-gray-200 h-full overflow-y-auto">
        <div class="px-4 py-2" v-if="tables?.length === 0">
          No table available. <br />Please contact support.
        </div>
        <DatabaseExplorerItems
          v-for="(table, ind) in usedTables"
          :key="ind"
          :table="table"
          :showColumns="table.name == showTableKey"
          @click="onClick(table.name)"
          @search="onSearch"
          :isUsed="true"
        />
        <div class="px-4 py-2 bg-gray-50">
          <Input
            type="text"
            placeholder="Search table"
            id="searchTables"
            v-model="searchTablesInput"
          />
        </div>
        <DatabaseExplorerItems
          v-for="(table, ind) in filteredTables"
          :key="ind"
          :table="table"
          :showColumns="table.name == showTableKey"
          @click="onClick(table.name)"
          @search="onSearch"
        />
        <div v-if="filteredTables.length == 0" class="block bg-white hover:bg-gray-50">
          <p class="px-4 py-4 sm:px-6">No tables</p>
        </div>
      </ul>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardTitle } from '@/components/ui/card'
import DatabaseExplorerItems from '@/components/DatabaseExplorerItems.vue'
import { useQueryEditor } from '@/composables/useQueryEditor'
import { useDatabasesStore } from '@/stores/databases'
import type { Table } from '@/stores/tables'
import { useSelectedDatabaseFromContext } from '@/useSelectedDatabaseFromContext'
import { computed, ref, watchEffect } from 'vue'
import CardContent from './ui/card/CardContent.vue'

const databasesStore = useDatabasesStore()
const editor = useQueryEditor()
const tables = ref<Table[]>([])
const showTableKey = ref<string | null>(null)
const { selectedDatabase } = useSelectedDatabaseFromContext()

watchEffect(async () => {
  const db = selectedDatabase.value
  if (db) {
    tables.value = await databasesStore.fetchDatabaseTables(db.id)
  } else {
    tables.value = []
  }
})

const searchTablesInput = ref('')

function extractTables(sqlQuery: string) {
  // Regular expression to match table names following FROM, JOIN, and UPDATE keywords
  // This regex is basic and might need adjustments to cover all SQL syntax variations
  const regex = /\b(FROM|JOIN|UPDATE|INTO)\s+("?\w+"?\."?\w+"?|"\w+"|\w+)/gi

  let match
  const extables = []

  // Use a loop to find matches and push the table name to the tables array
  while ((match = regex.exec(sqlQuery)) !== null) {
    // This ensures the match was not empty or undefined
    // Note: replaceAll requires ES2021 or later
    if (match[2]) {
      // Use split/join as a fallback for replaceAll
      extables.push(match[2].split('"').join(''))
    }
  }

  // Remove duplicates by converting to a Set and back to an Array
  return [...new Set(extables)]
}

const extractedTables = computed(() => {
  return extractTables(editor.query.sql)
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

const onSearch = (table: Table) => {
  editor.query.sql = `SELECT * FROM "${table.schema}"."${table.name}";`
  searchTablesInput.value = '' // reset input
  editor.runQuery()
}
</script>
