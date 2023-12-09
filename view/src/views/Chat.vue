<template>
  <div class="flex h-screen">
    <ConversationList />
    <Chat />
  </div>
</template>

<script setup lang="ts">
import ConversationList from '@/components/ConversationList.vue'
import Chat from '@/components/Chat.vue'
</script>
