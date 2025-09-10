<script setup lang="ts">
import Chat from '@/components/Chat.vue'
import { ref } from 'vue'

const sidebarOpen = ref(false)

const onSwipe = () => {
  sidebarOpen.value = true
}
</script>

<template>
  <div>
    <Chat v-touch:swipe.right="onSwipe" />
  </div>
</template>
