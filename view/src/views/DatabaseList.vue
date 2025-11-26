<template>
  <PageHeader title="Connections" subtitle="Manage your database connections and options." sticky>
    <template #actions>
      <Button @click="router.push('/setup')">
        <PlusIcon class="h-4 w-4" />
        Add Connection
      </Button>
    </template>
  </PageHeader>
  <div class="flex-1 overflow-auto">
    <div class="mx-auto px-4">
      <div class="mt-6 flow-root">
        <ul role="list" class="-my-5 divide-y divide-border">
          <li v-for="database in databasesStore.sortedDatabases" :key="database.id" class="py-4">
            <div class="flex items-center space-x-4">
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-medium text-foreground">
                  {{ database.name }}
                  <span
                    v-if="database.public"
                    class="ml-2 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-muted text-muted-foreground"
                  >
                    public
                  </span>
                  <span
                    v-if="database.organisationId"
                    class="ml-2 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300"
                  >
                    organisation
                  </span>
                </p>
                <p class="truncate text-sm text-muted-foreground">
                  {{ database.engine }}
                </p>
              </div>
              <div>
                <router-link
                  :to="'/databases/' + database.id"
                  v-if="!database.public"
                  class="inline-flex items-center rounded-full border border-border bg-card px-2.5 py-0.5 text-sm font-medium leading-5 text-card-foreground shadow-xs hover:bg-muted"
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
