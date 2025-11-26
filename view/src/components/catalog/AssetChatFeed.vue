<template>
  <Sheet v-model:open="isOpen">
    <SheetContent side="right" class="w-full sm:max-w-2xl flex flex-col p-0 gap-0">
      <SheetHeader class="px-6 pt-6 pb-4 border-b">
        <SheetTitle class="flex items-center gap-2">
          <SparklesIcon class="size-5 text-purple-600" />
          Agent Conversation
        </SheetTitle>
        <SheetDescription>
          <button
            @click="openInChat"
            class="text-primary hover:underline cursor-pointer inline-flex items-center gap-1"
          >
            Open in Chat
            <ExternalLinkIcon class="size-3" />
          </button>
        </SheetDescription>
      </SheetHeader>

      <!-- Scrollable messages area -->
      <div ref="scrollContainer" class="flex-1 overflow-y-auto px-6 py-4">
        <!-- Loading State -->
        <div v-if="isLoading" class="flex justify-center py-8">
          <LoaderIcon class="size-6 text-muted-foreground" />
        </div>

        <!-- Empty State -->
        <div
          v-else-if="displayedMessages.length === 0"
          class="text-center py-8 text-muted-foreground"
        >
          <p class="text-sm">No messages in this conversation</p>
        </div>

        <!-- Messages using MessageDisplay -->
        <ul v-else class="list-none space-y-4">
          <template v-for="(group, index) in messageGroups" :key="index">
            <li
              v-for="message in group.publicMessages"
              :key="message.id"
              :class="message.role === 'user' ? 'flex justify-end' : ''"
            >
              <MessageDisplay
                :message="message"
                @editInlineClick="editInline"
                @regenerateFromMessage="handleRegenerateFromMessage"
                @rejected="focusInput"
              />
            </li>
            <li v-if="group.internalMessages.length > 0" class="flex justify-center">
              <button
                @click="toggleInternalMessages(index)"
                class="inline-flex items-center px-3 py-1 my-1 text-sm text-gray-500 rounded-full hover:bg-gray-200"
              >
                <component
                  :is="internalMessageGroups[index] ? EyeSlashIcon : EyeIcon"
                  class="w-4 h-4 mr-1"
                />
                {{ group.internalMessages.length }} internal
                {{ group.internalMessages.length === 1 ? 'message' : 'messages' }}
              </button>
            </li>
            <transition-group
              name="internal-messages"
              enter-active-class="transition-all duration-300 ease-out"
              enter-from-class="opacity-0 max-h-0"
              enter-to-class="opacity-100 max-h-[1000px]"
              leave-active-class="transition-all duration-300 ease-in"
              leave-from-class="opacity-100 max-h-[1000px]"
              leave-to-class="opacity-0 max-h-0"
              v-if="internalMessageGroups[index]"
            >
              <li
                v-for="message in group.internalMessages"
                :key="message.id"
                class="overflow-hidden"
                :class="message.role === 'user' ? 'flex justify-end' : ''"
              >
                <MessageDisplay
                  :message="message"
                  @editInlineClick="editInline"
                  @regenerateFromMessage="handleRegenerateFromMessage"
                  @rejected="focusInput"
                  class="border-l-4 border-gray-500 pl-3 bg-gray-50"
                />
              </li>
            </transition-group>
          </template>
        </ul>

        <!-- Status area -->
        <div id="chat-status" class="w-full py-4">
          <div class="w-full flex justify-center">
            <!-- Display error message if queryStatus is error -->
            <div v-if="queryStatus === 'error'" class="flex flex-col items-center">
              <div>
                <p class="text-error-500">{{ errorMessage }}</p>
              </div>
              <div>
                <Button
                  variant="outline"
                  size="sm"
                  @click="handleRegenerateFromMessage(lastMessage?.id)"
                >
                  <RotateCcw class="h-4 w-4 mr-2" />
                  Retry
                </Button>
              </div>
            </div>

            <div v-else-if="queryStatus === STATUS.RUNNING || queryStatus === STATUS.PENDING">
              <LoaderIcon /><br />
              <button
                @click="stopQuery"
                class="w-full bg-gray-500 text-white py-2 px-4 rounded-sm"
                type="submit"
              >
                Stop
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Chat Input - Fixed at bottom -->
      <div class="border-t bg-white px-4 py-4">
        <Card class="py-0 px-2">
          <div class="flex items-center">
            <div class="w-full flex py-1">
              <Textarea
                ref="inputTextarea"
                v-model="inputText"
                :placeholder="'Ask a follow-up question...'"
                class="flex-1 min-h-8 border-none shadow-none outline-none focus-visible:ring-0 py-2 px-3 resize-none max-h-36"
                @keydown.enter="handleEnter"
                @input="resizeTextarea"
                rows="1"
                v-if="editMode === 'text'"
              />
              <BaseEditor
                v-model="inputSQL"
                :read-only="false"
                class="flex-1 min-h-[100px]"
                v-if="editMode === 'SQL'"
              />

              <div class="flex items-center space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  @click="toggleEditMode"
                  :title="editMode === 'text' ? 'Switch to SQL' : 'Switch to text'"
                  class="p-2"
                >
                  <CodeIcon v-if="editMode === 'text'" class="h-4 w-4" />
                  <TypeIcon v-else class="h-4 w-4" />
                </Button>
                <SendButtonWithStatus
                  :status="sendStatus"
                  :disabled="isSendDisabled"
                  @click="handleSendMessage"
                />
              </div>
            </div>
          </div>
        </Card>
      </div>
    </SheetContent>
  </Sheet>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted, nextTick, type ComponentPublicInstance } from 'vue'
import { useRouter } from 'vue-router'
import { isConnected, socket } from '@/plugins/socket'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle
} from '@/components/ui/sheet'
import { Card } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import LoaderIcon from '@/components/icons/LoaderIcon.vue'
import SendButtonWithStatus from '@/components/icons/SendButtonWithStatus.vue'
import MessageDisplay from '@/components/MessageDisplay.vue'
import BaseEditor from '@/components/base/BaseEditor.vue'
import { SparklesIcon, ExternalLinkIcon, CodeIcon, TypeIcon, RotateCcw } from 'lucide-vue-next'
import { EyeIcon, EyeSlashIcon } from '@heroicons/vue/24/outline'
import { STATUS, useConversationsStore, type Message } from '@/stores/conversations'
import { useQueriesStore } from '@/stores/queries'

// Props
const props = defineProps<{
  conversationId: string | null
}>()

// Model for sheet open state
const isOpen = defineModel<boolean>('open', { default: false })

const router = useRouter()
const conversationsStore = useConversationsStore()
const queriesStore = useQueriesStore()

// State
const messages = ref<Message[]>([])
const isLoading = ref(false)
const inputText = ref('')
const inputSQL = ref('')
const editMode = ref<'text' | 'SQL'>('text')
const scrollContainer = ref<HTMLDivElement | null>(null)
const internalMessageGroups = ref<{ [key: number]: boolean }>({})

// Refs for input
type TextareaComponentInstance = ComponentPublicInstance & { $el: HTMLElement }
const inputTextarea = ref<TextareaComponentInstance | HTMLTextAreaElement | null>(null)
const inputEditor = ref<any>(null)

// Computed
const conversation = computed(() => {
  if (!props.conversationId) return null
  return conversationsStore.getConversationById(props.conversationId)
})

const queryStatus = computed(() => conversation.value?.status ?? 'clear')
const errorMessage = computed(() => conversation.value?.error ?? '')
const lastMessage = computed(() => messages.value[messages.value.length - 1])

const sendStatus = computed(() => {
  if (!isConnected.value) return 'error'
  if (!props.conversationId) return 'clear'
  return conversation.value?.status ?? 'clear'
})

const isSendDisabled = computed(() => {
  const currentInput = editMode.value === 'text' ? inputText.value : inputSQL.value
  return currentInput.trim().length === 0
})

const displayedMessages = computed(() => {
  return messages.value.filter(shouldDisplayMessage)
})

const messageGroups = computed(() => {
  type MessageGroup = {
    publicMessages: Message[]
    internalMessages: Message[]
  }
  const groups: MessageGroup[] = []
  let currentGroup: MessageGroup = { publicMessages: [], internalMessages: [] }

  displayedMessages.value.forEach((message, index) => {
    const isPublic = isPublicMessage(message, index)

    if (isPublic) {
      if (currentGroup.internalMessages.length > 0 || currentGroup.publicMessages.length > 0) {
        groups.push({ ...currentGroup })
        currentGroup = { publicMessages: [], internalMessages: [] }
      }
      currentGroup.publicMessages.push(message)
    } else {
      currentGroup.internalMessages.push(message)
    }
  })

  if (currentGroup.publicMessages.length > 0 || currentGroup.internalMessages.length > 0) {
    groups.push(currentGroup)
  }

  return groups
})

// Helper functions
function shouldDisplayMessage(message: Message) {
  const isEmptyFunctionResponse =
    message.role === 'function' && message.content === '' && message.image === null

  const isUpdateAssetReturn =
    message.role === 'function' && message.name === 'CatalogTool-catalog__update_asset'
  return !isEmptyFunctionResponse && !isUpdateAssetReturn
}

function isPublicMessage(message: Message, index: number): boolean {
  const prevMessage = index > 0 ? displayedMessages.value[index - 1] : null
  const isUser = message.role === 'user'
  const isFunction = message.role === 'function'
  const isFunctionAfterUser = isFunction && prevMessage?.role === 'user'
  const isFunctionAfterAnswer = isFunction && !!prevMessage?.isAnswer
  const isAnswer = !!message.isAnswer
  const hasCatalogProposal =
    !!message.functionCall?.name?.includes('update_asset') ||
    !!message.functionCall?.name?.includes('upsert_term')

  const hasWriteOperation = message.queryId
    ? !!queriesStore.getQuery(message.queryId)?.operationType
    : false

  return (
    isUser ||
    isFunctionAfterUser ||
    isAnswer ||
    isFunctionAfterAnswer ||
    hasWriteOperation ||
    hasCatalogProposal
  )
}

function toggleInternalMessages(index: number) {
  internalMessageGroups.value[index] = !internalMessageGroups.value[index]
}

function toggleEditMode() {
  editMode.value = editMode.value === 'text' ? 'SQL' : 'text'
}

const resolveTextareaElement = (): HTMLTextAreaElement | null => {
  const refValue = inputTextarea.value
  if (!refValue) return null
  if (refValue instanceof HTMLTextAreaElement) return refValue
  const el = refValue.$el
  if (el instanceof HTMLTextAreaElement) return el
  return null
}

// Input handling
const handleEnter = (event: KeyboardEvent) => {
  if (isSendDisabled.value) {
    event.preventDefault()
    return
  }
  if (!event.shiftKey) {
    event.preventDefault()
    handleSendMessage()
  }
}

const handleSendMessage = async () => {
  if (!props.conversationId) return

  try {
    await conversationsStore.sendMessage(
      props.conversationId,
      editMode.value === 'text' ? inputText.value : inputSQL.value,
      editMode.value
    )
    setTimeout(() => {
      clearInput()
      scrollToBottom()
    }, 100)
  } catch (error) {
    console.error('Error sending message:', error)
  }
}

const clearInput = () => {
  inputText.value = ''
  inputSQL.value = ''
  resizeTextarea()
}

const resizeTextarea = () => {
  nextTick(() => {
    const textarea = resolveTextareaElement()
    if (!textarea) return
    textarea.style.height = 'auto'
    const maxHeight = 400
    const scrollHeight = textarea.scrollHeight

    if (scrollHeight > maxHeight) {
      textarea.style.height = maxHeight + 'px'
      textarea.style.setProperty('overflow-y', 'auto', 'important')
    } else {
      textarea.style.height = scrollHeight + 'px'
      textarea.style.setProperty('overflow-y', 'hidden', 'important')
    }
  })
}

const editInline = (query: string) => {
  inputSQL.value = query
  editMode.value = 'SQL'
}

const focusInput = () => {
  nextTick(() => {
    if (editMode.value === 'text') {
      resolveTextareaElement()?.focus()
    } else if (editMode.value === 'SQL' && inputEditor.value) {
      try {
        const aceEditor = inputEditor.value.$refs?.aceEditor?.editor || inputEditor.value.editor
        if (aceEditor && aceEditor.focus) {
          aceEditor.focus()
        }
      } catch (error) {
        console.warn('Could not focus SQL editor:', error)
      }
    }
  })
}

const handleRegenerateFromMessage = (messageId: string | undefined, newContent?: string) => {
  if (!props.conversationId || !messageId) return
  conversationsStore.regenerateFromMessage(messageId, newContent)
}

const stopQuery = async () => {
  if (props.conversationId) {
    socket.emit('stop', props.conversationId)
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
    }
  })
}

// Fetch conversation messages using the store (so regenerateFromMessage works)
async function fetchConversation() {
  if (!props.conversationId) return

  isLoading.value = true
  messages.value = []

  try {
    // Use the store's fetchMessages to ensure conversation is in the store
    await conversationsStore.fetchMessages(props.conversationId)
    // Get messages from the store
    const conv = conversationsStore.getConversationById(props.conversationId)
    messages.value = conv?.messages || []
    scrollToBottom()
  } catch (err) {
    console.error('Failed to load conversation:', err)
  } finally {
    isLoading.value = false
  }
}

function openInChat() {
  if (props.conversationId) {
    router.push(`/chat/${props.conversationId}`)
    isOpen.value = false
  }
}

// Real-time updates
function handleConversationResponse(data: Message) {
  if (!props.conversationId) return

  // Avoid duplicates in local messages
  if (!messages.value.some((m) => m.id === data.id)) {
    messages.value = [...messages.value, data]
    scrollToBottom()
  }

  // Also sync from store in case it was updated there
  const conv = conversationsStore.getConversationById(props.conversationId)
  if (conv?.messages) {
    messages.value = conv.messages
  }
}

// Watch for sheet open to fetch data and join socket room
watch(isOpen, (open) => {
  if (open && props.conversationId) {
    fetchConversation()
    socket.emit('join', props.conversationId)
    socket.on('response', handleConversationResponse)
    nextTick(() => focusInput())
  } else {
    if (props.conversationId) {
      socket.emit('leave', props.conversationId)
    }
    socket.off('response', handleConversationResponse)
  }
})

// Watch for conversationId changes when sheet is open
watch(
  () => props.conversationId,
  (newId, oldId) => {
    if (isOpen.value) {
      // Leave old room
      if (oldId) {
        socket.emit('leave', oldId)
      }
      // Join new room and fetch
      if (newId) {
        fetchConversation()
        socket.emit('join', newId)
      }
    }
  }
)

onUnmounted(() => {
  socket.off('response', handleConversationResponse)
  if (props.conversationId) {
    socket.emit('leave', props.conversationId)
  }
})
</script>

<style scoped>
textarea {
  height: auto;
}

.internal-messages-enter-active,
.internal-messages-leave-active {
  transition: all 0.3s ease-in-out;
  overflow: hidden;
}

.internal-messages-enter-from,
.internal-messages-leave-to {
  opacity: 0;
  max-height: 0;
}

.internal-messages-enter-to,
.internal-messages-leave-from {
  opacity: 1;
  max-height: 1000px;
}
</style>
