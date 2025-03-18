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
    v-model="queryText"
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
import BaseEditor from '@/components/BaseEditor.vue'
import BaseButton from '@/components/BaseButton.vue'
import {
  queryText,
  querySQL,
  runQuery,
  updateQuery,
  queryIsModified,
  loading as queryLoading
} from '../stores/query'

import { useDatabases } from '../stores/databases'
import BaseSelector from './BaseSelector.vue'
import { ArrowPathIcon } from '@heroicons/vue/24/outline'

const { databaseSelected, databases, fetchDatabases } = useDatabases()

fetchDatabases({ refresh: true })
</script>
