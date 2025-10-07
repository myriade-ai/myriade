<template>
  <div>
    <PageHeader title="Connections" subtitle="Manage your database connections and options.">
      <template #actions>
        <Button @click="router.push('/setup')">
          <PlusIcon class="h-4 w-4" />
          Add Connection
        </Button>
      </template>
    </PageHeader>
    <div class="mx-auto px-4">
      <div class="mt-6 flow-root">
        <ul role="list" class="-my-5 divide-y divide-gray-200">
          <li v-for="database in databasesStore.sortedDatabases" :key="database.id" class="py-4">
            <div class="flex items-center space-x-4">
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-medium text-gray-900">
                  {{ database.name }}
                  <span
                    v-if="database.public"
                    class="ml-2 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-800"
                  >
                    public
                  </span>
                </p>
                <p class="truncate text-sm text-gray-500">
                  {{ database.engine }}
                </p>
              </div>
              <div>
                <router-link
                  :to="'/databases/' + database.id"
                  v-if="!database.public"
                  class="inline-flex items-center rounded-full border border-gray-300 bg-white px-2.5 py-0.5 text-sm font-medium leading-5 text-gray-700 shadow-xs hover:bg-gray-50"
                >
                  Edit
                </router-link>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import PageHeader from '@/components/PageHeader.vue'
import { Button } from '@/components/ui/button'
import { useDatabasesStore } from '@/stores/databases'
import { PlusIcon } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const databasesStore = useDatabasesStore()
const router = useRouter()

databasesStore.fetchDatabases({ refresh: true })
</script>
