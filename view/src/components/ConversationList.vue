<template>
  <div class="w-72 bg-gray-100 flex flex-col text-sm">
    <div class="px-4 py-2">
      <BaseButton class="w-full" @click="selectNewConversation">New Conversation</BaseButton>
    </div>

    <div class="overflow-y-auto">
      <!-- Example grouping by date, or display sorted list directly -->
      <div v-for="conversation in sortedGroup" :key="conversation.id">
        <div
          class="p-4 border-b border-gray-300 cursor-pointer hover:bg-gray-200 flex justify-between items-center"
          :class="currentConversation(conversation) ? 'bg-gray-300' : ''"
          @click="selectConversation(conversation)"
        >
          <div class="truncate grow">
            <span v-if="!editName">{{ conversation.name || 'Unnamed...' }}</span>
            <input
              v-else
              :ref="setNameInputRef(conversation.id)"
              v-model="conversation.name"
              class="bg-transparent border-none focus:outline-hidden focus:ring-0"
              placeholder="Unnamed..."
            />
          </div>
          <div class="shrink-0 flex items-center">
            <!-- Example: Show edit/trash icons if it's the active conversation, etc. -->
            <button
              @click.stop="editConversationName(conversation.id)"
              v-if="currentConversation(conversation) && !editName"
              class="text-gray-500 ml-2"
            >
              <PencilIcon class="h-5 w-5" />
            </button>
            <button
              @click.stop="handleRenameConversation(conversation)"
              v-if="currentConversation(conversation) && editName"
              class="text-gray-500 ml-2"
            >
              <CheckCircleIcon class="h-5 w-5" />
            </button>
            <button
              @click.stop="handleDeleteConversation(conversation)"
              v-if="currentConversation(conversation)"
              class="text-gray-500 ml-2"
            >
              <TrashIcon class="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ConversationInfo } from '@/stores/conversations'
import { useConversationsStore } from '@/stores/conversations'
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

// UI components
import BaseButton from '@/components/base/BaseButton.vue'
import { CheckCircleIcon, PencilIcon, TrashIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const router = useRouter()
const store = useConversationsStore()

// Local state to handle editing conversation name
const editName = ref(false)
const nameInputs = ref<{ [convId: string]: HTMLInputElement }>({})

function setNameInputRef(id: string) {
  return (el: HTMLInputElement) => {
    if (el) {
      nameInputs.value[id] = el
    }
  }
}

// On mount, fetch the conversation list
onMounted(async () => {
  await store.fetchConversations()
})

const sortedGroup = computed(() => {
  // e.g. simply use store.sortedConversations,
  // or do your “group by date” logic
  return store.sortedUserConversations
})

// Routing
function selectNewConversation() {
  router.push({ path: '/chat/new' })
}
function selectConversation(conversation: ConversationInfo) {
  router.push({ path: `/chat/${conversation.id}` })
}
function currentConversation(conversation: ConversationInfo) {
  return Number(route.params.id) === conversation.id
}

// Example: rename logic
function editConversationName(id: string) {
  editName.value = true
  nextTick(() => {
    const el = nameInputs.value[id]
    if (el) {
      el.focus()
      el.select()
    }
  })
}

async function handleDeleteConversation(conversation: ConversationInfo) {
  await store.deleteConversation(conversation.id)
  // If that conversation was active, redirect away
  if (currentConversation(conversation)) router.push({ path: '/' })
}

async function handleRenameConversation(conversation: ConversationInfo) {
  await store.renameConversation(conversation.id, conversation.name)
  editName.value = false
}
</script>
