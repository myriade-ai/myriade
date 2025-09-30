<template>
  <div>
    <PageHeader
      title="Editor"
      subtitle="Write and run SQL queries — save them and visualize the results."
    />
    <div class="grid grid-cols-12 gap-4 px-4 mx-auto py-4 h-screen overflow-y-scroll">
      <div class="col-span-3 hidden md:block h-full overflow-y-auto">
        <DatabaseExplorer />
      </div>
      <div class="col-span-12 md:col-span-9">
        <BaseQuery :editor="editor" />
        <BaseAlert v-if="editor.error.value">
          <template #title> There is an error in the SQL execution 😔 </template>
          {{ editor.error.value }}
        </BaseAlert>
        <DataTable
          v-if="editor.results.value !== null"
          :data="editor.results.value"
          :count="editor.count.value ?? 0"
          class="mt-4"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BaseAlert from '@/components/base/BaseAlert.vue'
import PageHeader from '@/components/PageHeader.vue'
import BaseQuery from '@/components/base/BaseQuery.vue'
import DataTable from '@/components/DataTable.vue'
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
