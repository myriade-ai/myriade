<template>
  <BaseButton
    class="float-right mt-1 ml-1 disabled:bg-gray-300"
    @click="queryStore.updateQuery(selectedDatabase?.id)"
    :disabled="!queryStore.queryIsModified || !queryStore.querySQL"
  >
    Save query</BaseButton
  >

  <input
    type="text"
    placeholder="Database used for X,Y and Z..."
    class="block w-full max-w-lg rounded-md border-gray-300 shadow-xs focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
    v-model="queryStore.queryTitle"
  />

  <br />
  <div class="relative">
    <BaseEditor
      v-model="queryStore.querySQL"
      @run-query="() => queryStore.runQuery(selectedDatabase?.id)"
    />
    <button
      class="absolute bottom-2 right-2 bg-primary-500 hover:bg-primary-600 text-white rounded-full p-3 shadow-lg focus:outline-none focus:ring-2 focus:ring-primary-500 flex items-center justify-center disabled:bg-primary-800"
      @click="queryStore.runQuery(selectedDatabase?.id)"
      :disabled="queryStore.loading"
      aria-label="Run query"
      type="button"
    >
      <ArrowPathIcon v-if="queryStore.loading" class="animate-reverse-spin h-6 w-6 text-white" />
      <PlayIcon v-else class="h-6 w-6" />
    </button>
  </div>
</template>

<script setup lang="ts">
import BaseButton from '@/components/base/BaseButton.vue'
import BaseEditor from '@/components/base/BaseEditor.vue'
import { useDatabasesStore } from '@/stores/databases'
import { useQueryStore } from '@/stores/query'
import { useSelectedDatabaseFromContext } from '@/useSelectedDatabaseFromContext'
import { ArrowPathIcon } from '@heroicons/vue/24/outline'
import { PlayIcon } from '@heroicons/vue/24/solid'

const queryStore = useQueryStore()
const databasesStore = useDatabasesStore()

const { selectedDatabase } = useSelectedDatabaseFromContext()

databasesStore.fetchDatabases({ refresh: true })
</script>
