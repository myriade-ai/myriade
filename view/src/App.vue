<template>
  <div v-if="appReady">
    <metainfo>
      <template v-slot:title="{ content }">{{ content }}</template>
    </metainfo>
    <component :is="layout"> </component>
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
            class="flex w-full max-w-sm mx-auto mt-4 overflow-hidden bg-popover border border-border rounded-lg shadow-md"
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

const layout = computed(() => {
  if (route.name === undefined) {
    return defaultLayout
  }

  return route.meta.layout === 'empty' ? emptyLayout : defaultLayout
})
</script>
