<template>
  <SidebarProvider>
    <AppSidebar />
    <SidebarInset class="min-w-0 w-full">
      <header class="flex h-16 shrink-0 items-center gap-2 border-b px-4">
        <SidebarTrigger class="-ml-1" />
        <h1 v-if="route.name === 'IssuesPage'" class="text-xl">Issues</h1>
        <div v-if="route.path.startsWith('/projects')" class="flex gap-2 items-baseline">
          <h1 class="text-xl">Projects</h1>
          <p class="hidden md:block text-sm text-gray-500">
            Manage your projects, so you can work on specific problems/topics.
          </p>
        </div>
        <div v-if="route.name === 'Editor'" class="flex gap-2 items-baseline">
          <h1 class="text-xl">Editor</h1>
          <p class="hidden md:block text-sm text-gray-500">
            Write and run SQL queries — save them and visualize the results.
          </p>
        </div>
        <div v-if="route.name === 'Favorites'" class="flex gap-2 items-baseline">
          <h1 class="text-xl">Favorites</h1>
          <p class="hidden md:block text-sm text-gray-500">Your saved queries and charts</p>
        </div>
        <div v-if="isDatabaseRoute" class="flex gap-2 items-baseline">
          <h1 class="text-xl">Database</h1>
          <p class="hidden md:block text-sm text-gray-500">
            Manage your database connections and options.
          </p>
        </div>
      </header>
      <div class="flex-1">
        <AnonymousUserBar />
        <div>
          <Suspense>
            <router-view />
          </Suspense>
        </div>
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AnonymousUserBar from '@/components/AnonymousUserBar.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import { SidebarProvider, SidebarTrigger, SidebarInset } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'

const route = useRoute()

const isDatabaseRoute = computed(() => {
  return ['DatabaseList', 'DatabaseEdit'].includes(String(route.name))
})
</script>
