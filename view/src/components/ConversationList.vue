<template>
  <div class="w-72 h-screen bg-gray-100 flex flex-col text-sm">
    <div class="px-4 py-2">
      <BaseButton class="w-full" @click="selectNewConversation">New Conversation</BaseButton>
    </div>
    <div class="overflow-y-auto">
      <!-- Iterate through conversation items -->
      <div
        class="p-4 border-b border-gray-300 cursor-pointer hover:bg-gray-200 flex justify-between items-center"
        v-for="conversation in conversations"
        :key="conversation.id"
        :class="currentConversation(conversation) ? 'bg-gray-300' : ''"
        @click.stop="selectConversation(conversation)"
      >
        <div @click="selectConversation(conversation)" class="truncate">
          {{ conversation.name || 'Unnamed...' }}
        </div>
        <button
          @click.stop="deleteConversation(conversation.id)"
          class="text-grey-500"
          v-if="currentConversation(conversation)"
        >
          <TrashIcon class="h-5 w-5" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Ref } from 'vue'
import BaseButton from '@/components/BaseButton.vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { TrashIcon } from '@heroicons/vue/24/outline'
import { useRoute } from 'vue-router'

// Output the conversations types
type Conversation = {
  id: number
  name: string
}

const router = useRouter()
const route = useRoute()
const currentPath = computed(() => route.path)
const conversations: Ref<Conversation[]> = ref([])

const fetchConversations = async () => {
  conversations.value = await axios
    .get('/api/conversations')
    .then((res) => res.data.sort((a, b) => b.id - a.id))
}

await fetchConversations()

const selectNewConversation = () => {
  router.push({ path: '/' })
}

const selectConversation = (conversation: Conversation) => {
  router.push({ path: `/chat/${conversation.id}` })
}

const currentConversation = (conversation: Conversation) => {
  return currentPath.value.endsWith('/' + conversation.id.toString())
}

// On route change, fetch the conversation data
router.afterEach(async () => {
  await fetchConversations()
})

const deleteConversation = async (id: number) => {
  await axios.delete(`/api/conversations/${id}`)
  conversations.value = conversations.value.filter((conversation) => conversation.id !== id)
  // Redirect to home if the deleted conversation is the current conversation
  if (router.currentRoute.value.params.id === id.toString()) {
    router.push({ path: '/' })
  }
}
</script>
<style>
.red {
  background-color: red;
}
</style>
