<template>
  <div class="max-w-7xl mx-auto px-4">
    <div class="mt-6 flow-root">
      <ul role="list" class="-my-5 divide-y divide-gray-200">
        <li v-for="database in databasesStore.sortedDatabases" :key="database.id" class="py-4">
          <div class="flex items-center space-x-4">
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-gray-900">
                {{ database.name }}
              </p>
              <p class="truncate text-sm text-gray-500">
                {{ database.engine }}
              </p>
            </div>
            <div>
              <router-link
                :to="'/databases/' + database.id"
                class="inline-flex items-center rounded-full border border-gray-300 bg-white px-2.5 py-0.5 text-sm font-medium leading-5 text-gray-700 shadow-xs hover:bg-gray-50"
              >
                Edit
              </router-link>
            </div>
          </div>
        </li>
      </ul>
    </div>
    <hr class="my-4" />
    <div class="mt-6 mb-6">
      <router-link
        to="/databases/new"
        href="#"
        class="flex w-full items-center justify-center rounded-md border border-gray-300 bg-gray-50 px-4 py-2 mb-4 text-sm font-medium text-gray-700 shadow-xs hover:bg-gray-50"
        >Add new
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDatabasesStore } from '@/stores/databases'

const databasesStore = useDatabasesStore()

databasesStore.fetchDatabases({ refresh: true })
</script>
