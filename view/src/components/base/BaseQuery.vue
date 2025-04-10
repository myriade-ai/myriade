<template>
  <BaseButton
    class="float-right mt-1 ml-1 disabled:bg-gray-300"
    @click="updateQuery"
    :disabled="!queryIsModified || !querySQL"
  >
    Save query</BaseButton
  >
  <BaseSelector
    class="float-right ml-auto"
    style="width: 200px"
    :options="databases"
    v-model="databaseSelected"
  ></BaseSelector>

  <input
    type="text"
    placeholder="Database used for X,Y and Z..."
    class="block w-full max-w-lg rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
    v-model="queryTitle"
  />

  <br />
  <BaseEditor v-model="querySQL" @run-query="runQuery"></BaseEditor>

  <div class="mt-2 flex justify-end">
    <button
      class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      @click="runQuery()"
      :disabled="queryLoading"
    >
      <ArrowPathIcon v-if="queryLoading" class="animate-reverse-spin h-5 w-5 text-white mr-2" />
      Run query
    </button>
  </div>
</template>

<script setup lang="ts">
import BaseButton from '@/components/base/BaseButton.vue'
import BaseEditor from '@/components/base/BaseEditor.vue'
import BaseSelector from '@/components/base/BaseSelector.vue'
import { useQueryStore } from '@/stores/query'
import { useDatabasesStore } from '@/stores/databases'
import { ArrowPathIcon } from '@heroicons/vue/24/outline'

const { queryIsModified, loading as queryLoading, querySQL, queryTitle, runQuery, updateQuery } =
  useQueryStore()
const { databaseSelected, databases, fetchDatabases } = useDatabasesStore()

fetchDatabases({ refresh: true })
</script>
