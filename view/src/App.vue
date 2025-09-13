<template>
  <div v-if="appReady">
    <metainfo>
      <template v-slot:title="{ content }">{{ content }}</template>
    </metainfo>
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset class="min-w-0 w-full">
        <header class="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger class="-ml-1" />
          <Separator orientation="vertical" class="mr-2 h-4" />
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
          <component :is="layout"> </component>
        </div>
      </SidebarInset>
    </SidebarProvider>
  </div>
  <div v-else class="initial-loading" />
  <NotificationGroup>
    <div class="fixed inset-0 flex items-start justify-end p-6 px-4 py-6 pointer-events-none">
      <div class="w-full max-w-sm">
        <Notification
          v-slot="{ notifications }"
          enter="transform ease-out duration-300 transition"
          enter-from="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-4"
          enter-to="translate-y-0 opacity-100 sm:translate-x-0"
          leave="transition ease-in duration-500"
          leave-from="opacity-100"
          leave-to="opacity-0"
          move="transition duration-500"
          move-delay="delay-300"
        >
          <div
            class="flex w-full max-w-sm mx-auto mt-4 overflow-hidden bg-white rounded-lg shadow-md"
            v-for="notification in notifications"
            :key="notification.id"
          >
            <BaseNotification
              :color="notification.type === 'error' ? 'red' : 'green'"
              :title="String(notification.title)"
              :message="String(notification.text)"
            />
          </div>
        </Notification>
      </div>
    </div>
  </NotificationGroup>
</template>

<script lang="ts" setup>
import BaseNotification from '@/components/base/BaseNotification.vue'
import { Notification, NotificationGroup } from 'notiwind'
import { computed, defineAsyncComponent, onMounted, ref } from 'vue'

import { useMeta } from 'vue-meta'
import { useRoute } from 'vue-router'
import AppSidebar from './components/AppSidebar.vue'
import { SidebarProvider, SidebarTrigger } from './components/ui/sidebar'

useMeta({
  title: 'Myriade',
  description: 'Explore your data with Myriade!',
  htmlAttrs: { lang: 'en' }
})

const route = useRoute()
const appReady = ref(false)

const defaultLayout = defineAsyncComponent(() => import(`./layouts/default.vue`))
const emptyLayout = defineAsyncComponent(() => import(`./layouts/empty.vue`))

onMounted(() => {
  // This ensures the app shows nothing until it's fully ready
  requestAnimationFrame(() => {
    appReady.value = true
  })
})

const isDatabaseRoute = computed(() => {
  return ['DatabaseList', 'DatabaseEdit'].includes(String(route.name))
})

const layout = computed(() => {
  if (route.name === undefined) {
    return '' // Empty so we don't have flickering
  }

  return route.meta.layout === 'empty' ? emptyLayout : defaultLayout
})
</script>
