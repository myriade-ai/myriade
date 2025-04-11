<template>
  <!-- Go back to OpenAnalyticsList -->
  <router-link to="/openanalytics">
    <button>Back</button>
  </router-link>
  <div class="w-full h-screen flex justify-center items-center px-2">
    <div class="flex flex-col h-screen w-full">
      <Chat :conversation-id="'new'" :context="contextsStore.contextSelected" />
    </div>
  </div>
</template>

<script setup lang="ts">
import Chat from '@/components/Chat.vue'
import { useContextsStore } from '@/stores/contexts'
import { useRoute } from 'vue-router'

const route = useRoute()
const slug = route.params.slug

const contextsStore = useContextsStore()
await contextsStore.initializeContexts()
const id = slug.split('-')[0] // Split the slug by '-' and take the first part
contextsStore.setSelectedContextById(`database-${id}`)
</script>
