<template>
  <div class="grid grid-cols-12 gap-4 px-4 mx-auto py-4 bg-gray-100">
    <div class="col-span-3 hidden md:block">
      <DatabaseExplorer></DatabaseExplorer>
    </div>
    <div class="col-span-12 md:col-span-9">
      <BaseQuery :editor="editor" />
      <BaseAlert v-if="editor.error.value">
        <template #title> There is an error in the SQL execution 😔 </template>
        {{ editor.error.value }}
      </BaseAlert>
      <BaseTable
        v-if="editor.results.value !== null"
        :data="editor.results.value"
        :count="editor.count.value ?? 0"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import BaseAlert from '@/components/base/BaseAlert.vue'
import BaseQuery from '@/components/base/BaseQuery.vue'
import BaseTable from '@/components/base/BaseTable.vue'
import DatabaseExplorer from '@/components/DatabaseExplorer.vue'
import { useQueryEditor } from '@/composables/useQueryEditor'
import { useDatabasesStore } from '@/stores/databases'
import { useSelectedDatabaseFromContext } from '@/useSelectedDatabaseFromContext'
import { watchEffect } from 'vue'

const databasesStore = useDatabasesStore()

const { selectedDatabase } = useSelectedDatabaseFromContext()

databasesStore.fetchDatabases({ refresh: true })

const editor = useQueryEditor()

watchEffect(() => {
  if (selectedDatabase.value?.id && editor.databaseId.value !== selectedDatabase.value.id) {
    editor.databaseId.value = selectedDatabase.value.id
  }
})
</script>
