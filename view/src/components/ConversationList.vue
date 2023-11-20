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
        <div @click="selectConversation(conversation)" class="truncate flex-grow">
          <span v-if="!editName">{{ conversation.name || 'Unnamed...' }}</span>
          <input
            v-else
            :ref="setNameInputRef(conversation.id)"
            v-model="conversation.name"
            class="bg-transparent border-none focus:ring-0 focus:outline-none"
            style="width: 100vw"
            :placeholder="'Unnamed...'"
          />
        </div>
        <div class="flex-shrink-0 flex items-center">
          <button
            @click.stop="editConversationName(conversation.id)"
            class="text-grey-500 ml-2"
            v-if="currentConversation(conversation) && !editName"
          >
            <PencilIcon class="h-5 w-5" />
          </button>
          <button
            @click.stop="updateConversationName(conversation)"
            class="text-grey-500 ml-2"
            v-if="currentConversation(conversation) && editName"
          >
            <CheckCircleIcon class="h-5 w-5" />
          </button>
          <button
            @click.stop="deleteConversation(conversation.id)"
            class="text-grey-500 ml-2"
            v-if="currentConversation(conversation)"
          >
            <TrashIcon class="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, unref } from 'vue'
import type { Ref } from 'vue'
import BaseButton from '@/components/BaseButton.vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { TrashIcon, PencilIcon } from '@heroicons/vue/24/outline'
import { CheckCircleIcon } from '@heroicons/vue/24/outline'
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
const editName = ref(false)
const nameInputs = ref<{ [key: number]: HTMLInputElement }>({})

const setNameInputRef = (id: number) => (el: HTMLInputElement) => {
  nameInputs.value[id] = el
}

const fetchConversations = async () => {
  conversations.value = await axios
    .get('/api/conversations')
    .then((res) => res.data.sort((a: Conversation, b: Conversation) => b.id - a.id))
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

const editConversationName = (id: number) => {
  editName.value = true
  // Focus the input ref nameInput
  // TODO: fix
  nextTick(() => {
    const inputElement = nameInputs.value[id]
    if (inputElement) {
      inputElement.focus()
      inputElement.select()
    }
  })
}

const updateConversationName = async (conversation: Conversation) => {
  await axios.put(`/api/conversations/${conversation.id}`, { name: conversation.name })
  editName.value = false
}
</script>
<style>
.red {
  background-color: red;
}
</style>
