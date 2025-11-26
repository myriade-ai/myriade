<template>
  <PageHeader title="Chat" subtitle="Ask questions about your data and get instant answers." sticky>
    <template #actions>
      <div v-if="conversationHasGithub" class="flex items-center gap-2">
        <Sheet v-model:open="showChangesPanel">
          <SheetTrigger as-child>
            <Button v-if="hasChanges && !githubPrUrl" variant="outline" size="sm">
              <FileTextIcon class="h-4 w-4 mr-2" />
              {{ changedFiles.length }} {{ changedFiles.length === 1 ? 'file' : 'files' }} changed
            </Button>
          </SheetTrigger>
          <SheetContent side="right" class="w-full sm:max-w-2xl overflow-y-auto p-6">
            <SheetHeader>
              <SheetTitle>Changed Files</SheetTitle>
              <SheetDescription>
                Review the changes before creating a pull request
              </SheetDescription>
            </SheetHeader>
            <div class="mt-6 space-y-4">
              <CodeDiffDisplay
                v-for="file in changedFiles"
                :key="file.path"
                :old-string="file.old_content"
                :new-string="file.new_content"
                :file-name="file.path"
                :default-expanded="true"
              />
            </div>
          </SheetContent>
        </Sheet>
        <Button
          v-if="githubPrUrl"
          as="a"
          variant="outline"
          size="sm"
          :href="githubPrUrl"
          target="_blank"
          rel="noopener"
        >
          View PR
        </Button>
        <Button
          v-else-if="hasChanges"
          variant="default"
          size="sm"
          @click="handleCreatePullRequest"
          :disabled="creatingPr || isAiRunning"
        >
          {{ creatingPr ? 'Creating…' : 'Create PR' }}
        </Button>
      </div>
    </template>
  </PageHeader>
  <div
    ref="scrollContainer"
    class="flex-1 overflow-auto flex justify-center px-2 sm:px-4 lg:px-0"
    v-touch:swipe.right="
      () => {
        if (isMobile) toggleSidebar()
      }
    "
  >
    <div class="flex flex-col w-full">
      <div class="flex flex-col flex-1 w-full max-w-3xl m-auto">
        <div class="w-full lg:pt-4">
          <ul class="list-none space-y-4">
            <template v-for="(group, index) in messageGroups" :key="index">
              <li
                v-for="message in group.publicMessages"
                :key="message.id"
                :class="message.role === 'user' ? 'flex justify-end' : ''"
              >
                <MessageDisplay
                  :message="message"
                  @editInlineClick="editInline"
                  @regenerateFromMessage="conversationsStore.regenerateFromMessage"
                  @rejected="focusInput"
                />
              </li>
              <li v-if="group.internalMessages.length > 0" class="flex justify-center">
                <button
                  @click="toggleInternalMessages(index)"
                  class="inline-flex items-center px-3 py-1 my-1 text-sm text-muted-foreground rounded-full hover:bg-muted"
                >
                  <EyeIcon v-if="!internalMessageGroups[index]" class="h-4 w-4 mr-2" />
                  <EyeSlashIcon v-else class="h-4 w-4 mr-2" />
                  <span>
                    {{ internalMessageGroups[index] ? 'Hide' : 'Show' }}
                    {{ group.internalMessages.length }} internal messages
                  </span>
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
                    @regenerateFromMessage="conversationsStore.regenerateFromMessage"
                    @rejected="focusInput"
                    class="border-l-4 border-gray-500 pl-3 bg-muted/50"
                  />
                </li>
              </transition-group>
            </template>
          </ul>
        </div>

        <div id="chat-status" class="w-full pb-4">
          <div class="w-full flex justify-center">
            <!-- Subscription Prompt -->
            <div
              v-if="showSubscriptionPrompt"
              class="flex flex-col items-center w-full"
              style="position: relative"
            >
              <SubscriptionPrompt />
            </div>

            <!-- Display error message if queryStatus is error -->
            <div v-else-if="queryStatus === 'error'" class="flex flex-col items-center">
              <div>
                <p class="text-error-500">{{ errorMessage }}</p>
              </div>
              <div>
                <Button
                  variant="default"
                  @click="conversationsStore.regenerateFromMessage(lastMessage.id)"
                >
                  Regenerate
                </Button>
              </div>
            </div>

            <div v-else-if="queryStatus === STATUS.RUNNING || queryStatus === STATUS.PENDING">
              <!-- Add loading icon, centered, displayed only if a query is running -->
              <LoaderIcon /><br />
              <!-- Add stop button, centered, displayed only if a query is running -->
              <button
                @click="stopQuery"
                class="w-full bg-muted-foreground text-background py-2 px-4 rounded-sm"
                type="submit"
              >
                Stop
              </button>
            </div>
          </div>
        </div>
      </div>

      <div
        id="chat-input"
        class="w-full max-w-4xl border-gray-300 bottom-0 sticky z-10 mx-auto lg:px-2 px-0 bg-background pb-4"
      >
        <transition
          enter-active-class="transition-all duration-300 ease-out"
          enter-from-class="opacity-0 transform translate-y-4"
          enter-to-class="opacity-100 transform translate-y-0"
          leave-active-class="transition-all duration-300 ease-in"
          leave-from-class="opacity-100 transform translate-y-0"
          leave-to-class="opacity-0 transform translate-y-4"
        >
          <!-- 3 suggestions generated by AI -->
          <div
            class="flex flex-col mb-2"
            v-if="aiSuggestions && aiSuggestions.length && messages.length === 0"
          >
            <SparklesIcon class="h-5 w-5 text-primary-500" />
            <span class="text-primary-700 text-sm font-bold mb-2">AI Suggestions</span>
            <div v-if="aiSuggestions && aiSuggestions.length" class="flex flex-col space-y-2">
              <div
                v-for="(suggestion, index) in aiSuggestions"
                :key="index"
                class="flex items-center space-x-2"
              >
                <button
                  class="rounded-md bg-card px-3.5 py-2 text-sm text-primary-500 shadow-xs ring-1 ring-inset ring-primary-300 hover:bg-primary-50 text-left"
                  @click="applySuggestion(suggestion)"
                >
                  {{ suggestion }}
                </button>
              </div>
            </div>
          </div>
        </transition>

        <!-- Credits Display - moved outside input container to prevent deformation -->
        <div
          class="flex justify-end mb-2 px-2"
          v-if="user?.credits !== undefined && user.credits < 50"
        >
          <div class="text-xs text-muted-foreground bg-muted px-2 py-1 rounded-md">
            {{ user.credits }} credits left
          </div>
        </div>

        <Card id="input-container" class="py-0 px-2">
          <div class="flex items-center">
            <div class="w-full flex py-1">
              <Textarea
                @input="resizeTextarea"
                @keydown.enter="handleEnter"
                ref="inputTextarea"
                rows="1"
                placeholder="Type your message"
                v-model="inputText"
                class="bg-transparent flex-1 resize-none border-none shadow-none focus:border-none focus:ring-0 focus:outline-none focus-visible:border-none focus-visible:ring-0 focus-visible:outline-none break-words overflow-wrap-anywhere"
                style="max-height: 400px"
                v-if="editMode === 'text'"
              />
              <BaseEditor
                v-model="inputSQL"
                @run-query="handleSendMessage"
                v-if="editMode === 'SQL'"
              />

              <div class="flex items-center space-x-4">
                <Button
                  @click="toggleEditMode"
                  variant="ghost"
                  size="sm"
                  class="text-xs px-2 py-1 ml-2"
                >
                  {{ editMode === 'text' ? 'SQL' : 'Text' }}
                </Button>

                <SendButtonWithStatus
                  :status="sendStatus"
                  :disabled="isSendDisabled"
                  @clicked="handleSendMessage"
                />
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>

    <!-- Connection status notification -->
    <div
      v-if="!isConnected"
      class="fixed top-3 bg-error-500 text-white px-4 py-2 rounded-md shadow-lg z-50"
    >
      Socket disconnected
    </div>
  </div>

  <!-- Document Panel -->
  <DocumentPanel />
</template>

<script setup lang="ts">
import BaseEditor from '@/components/base/BaseEditor.vue'
import CodeDiffDisplay from '@/components/CodeDiffDisplay.vue'
import DocumentPanel from '@/components/DocumentPanel.vue'
import SendButtonWithStatus from '@/components/icons/SendButtonWithStatus.vue'
import MessageDisplay from '@/components/MessageDisplay.vue'
import SubscriptionPrompt from '@/components/SubscriptionPrompt.vue'
import axios from '@/plugins/axios'
import { user } from '@/stores/auth'
import { useContextsStore } from '@/stores/contexts'
import type { ComponentPublicInstance } from 'vue'
import { computed, nextTick, onMounted, ref, watch } from 'vue'

import LoaderIcon from '@/components/icons/LoaderIcon.vue'
import { useRoute, useRouter } from 'vue-router'

// Import sparkles from heroicons
import { isConnected, socket } from '@/plugins/socket'
import { STATUS, useConversationsStore, type Message } from '@/stores/conversations'
import { useQueriesStore } from '@/stores/queries'
import { EyeIcon, EyeSlashIcon } from '@heroicons/vue/24/outline'
import { SparklesIcon } from '@heroicons/vue/24/solid'
import PageHeader from './PageHeader.vue'
import { Button } from './ui/button'
import { Card } from './ui/card'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger
} from './ui/sheet'
import { useSidebar } from './ui/sidebar'
import { Textarea } from './ui/textarea'
import { FileTextIcon } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const { toggleSidebar, isMobile } = useSidebar()

const contextsStore = useContextsStore()
const queriesStore = useQueriesStore()

/** CONVERSATION LOGIC **/
const conversationsStore = useConversationsStore()
const conversationId = computed(() =>
  route.params.id === 'new' ? null : (route.params.id as string)
)
const queryStatus = computed(() => conversation.value?.status ?? 'clear')
const errorMessage = computed(() => conversation.value?.error ?? '')
const lastMessage = computed(() => messages.value[messages.value.length - 1])
const sendStatus = computed(() => {
  // if socket is not connected, return error
  if (!isConnected.value) {
    return 'error'
  }

  // if conversationId is not set, return clear
  if (conversationId.value === null) {
    return 'clear'
  }
  // if conversationId is set, return status
  return conversation.value?.status ?? 'clear'
})

const isSendDisabled = computed(() => {
  const currentInput = editMode.value === 'text' ? inputText.value : inputSQL.value
  return currentInput.trim().length === 0
})

/** The current conversation object from the store. */
const conversation = computed(() => {
  if (!conversationId.value) return null
  return conversationsStore.getConversationById(conversationId.value)
})
const messages = computed(() => {
  return conversation.value?.messages ?? []
})
const displayedMessages = computed(() => {
  return messages.value.filter(shouldDisplayMessage)
})
/** END CONVERSATION LOGIC **/

/** MESSAGE DISPLAY LOGIC **/
const internalMessageGroups = ref<{ [key: number]: boolean }>({})

const toggleInternalMessages = (index: number) => {
  internalMessageGroups.value[index] = !internalMessageGroups.value[index]
}

const toggleEditMode = () => {
  editMode.value = editMode.value === 'text' ? 'SQL' : 'text'
}

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

const githubPrUrl = computed(() => conversation.value?.githubPrUrl ?? null)
const conversationHasGithub = computed(() => conversation.value?.workspacePath !== null)
const isAiRunning = computed(
  () => queryStatus.value === STATUS.RUNNING || queryStatus.value === STATUS.PENDING
)

const creatingPr = ref(false)
const hasChanges = ref(false)
const changedFiles = ref<Array<{ path: string; old_content: string; new_content: string }>>([])
const showChangesPanel = ref(false)

const checkForChanges = async () => {
  if (!conversationId.value || !conversationHasGithub.value || githubPrUrl.value) {
    hasChanges.value = false
    changedFiles.value = []
    return
  }

  try {
    const response = await axios.get(`/api/conversations/${conversationId.value}/github/changes`)
    hasChanges.value = response.data.has_changes ?? false
    changedFiles.value = response.data.files ?? []
  } catch (err: any) {
    console.error('Failed to check for changes:', err)
    hasChanges.value = false
    changedFiles.value = []
  }
}

const handleCreatePullRequest = async () => {
  if (!conversationId.value) return

  try {
    creatingPr.value = true
    await conversationsStore.createGithubPullRequest(conversationId.value)
  } catch (err: any) {
    console.error('Failed to create pull request:', err)
    // Error will be shown through the store or a toast notification
  } finally {
    creatingPr.value = false
  }
}

const shouldDisplayMessage = (message: Message) => {
  const isEmptyFunctionResponse =
    message.role === 'function' && message.content === '' && message.image === null

  const isUpdateAssetReturn =
    message.role === 'function' && message.name === 'CatalogTool-catalog__update_asset'
  return !isEmptyFunctionResponse && !isUpdateAssetReturn
}

const isPublicMessage = (message: Message, index: number) => {
  const prevMessage = index > 0 ? displayedMessages.value[index - 1] : null
  const isUser = message.role === 'user'
  const isFunction = message.role === 'function'
  const isFunctionAfterUser = isFunction && prevMessage?.role === 'user'
  const isFunctionAfterAnswer = isFunction && prevMessage?.isAnswer
  const isAnwser = message.isAnswer
  const hasCatalogProposal =
    message.functionCall?.name.includes('update_asset') ||
    message.functionCall?.name.includes('upsert_term')

  const hasWriteOperation = message.queryId
    ? !!queriesStore.getQuery(message.queryId)?.operationType
    : false

  return (
    isUser ||
    isFunctionAfterUser ||
    isAnwser ||
    isFunctionAfterAnswer ||
    hasWriteOperation ||
    hasCatalogProposal
  )
}

/** END MESSAGE DISPLAY LOGIC **/

/** HANDLE EVENTS **/
type TextareaComponentInstance = ComponentPublicInstance & { $el: HTMLElement }

const inputTextarea = ref<TextareaComponentInstance | HTMLTextAreaElement | null>(null)
const inputEditor = ref<any>(null)
const inputText = ref('')
const inputSQL = ref('')

const editMode = ref<'text' | 'SQL'>('text')

const resolveTextareaElement = (): HTMLTextAreaElement | null => {
  const refValue = inputTextarea.value
  if (!refValue) {
    return null
  }

  if (refValue instanceof HTMLTextAreaElement) {
    return refValue
  }

  const el = refValue.$el
  if (el instanceof HTMLTextAreaElement) {
    return el
  }

  return null
}

// Subscription prompt state
const showSubscriptionPrompt = computed(() => conversationsStore.subscriptionRequired)

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
  try {
    // If we are on the /new page and the response is for a new conversation, redirect to the new conversation
    if (conversationId.value === null && contextsStore.contextSelected) {
      const newConversation = await conversationsStore.createConversation(
        contextsStore.contextSelected.id
      )
      await conversationsStore.sendMessage(
        newConversation.id,
        editMode.value === 'text' ? inputText.value : inputSQL.value,
        editMode.value
      )
      // After 100ms, clear the input.
      setTimeout(() => {
        clearInput()
        router.push({ path: `/chat/${newConversation.id}` })
      }, 100)
    } else if (conversationId.value) {
      await conversationsStore.sendMessage(
        conversationId.value,
        editMode.value === 'text' ? inputText.value : inputSQL.value,
        editMode.value
      )
      // After 100ms, clear the input and scroll to bottom.
      setTimeout(() => {
        clearInput()
        scrollToBottom()
      }, 100)
    } else {
      console.error('No conversation selected')
    }
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
  // Wait for next tick to get the updated DOM.
  nextTick(() => {
    const textarea = resolveTextareaElement()
    if (!textarea) return
    textarea.style.height = 'auto'

    // Set maximum height to prevent unlimited growth (approximately 16 lines)
    const maxHeight = 400 // pixels
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
  // Focus the input textarea after a short delay to ensure the UI has updated
  nextTick(() => {
    if (editMode.value === 'text') {
      resolveTextareaElement()?.focus()
    } else if (editMode.value === 'SQL' && inputEditor.value) {
      // For Ace editor, we need to access the editor instance
      try {
        // The v-ace-editor component exposes the editor instance
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

/** END HANDLE EVENTS */

onMounted(async () => {
  // Access the underlying textarea element for focus and select
  nextTick(() => {
    resolveTextareaElement()?.focus()
  })

  // Check if there's a prompt query parameter and pre-fill the input
  if (route.query.prompt) {
    inputText.value = String(route.query.prompt)
    editMode.value = 'text'
    // Remove the query parameter from the URL to clean it up
    router.replace({ path: route.path, query: {} })
  }

  if (!conversationId.value) {
    // New conversation
    await fetchAISuggestions()
  } else {
    // Existing conversation
    conversationsStore.fetchMessages(conversationId.value)
    // Mark conversation as viewed
    conversationsStore.markConversationAsViewed(conversationId.value)
  }

  checkForChanges()
  scrollToBottom()
})

// If route changes (user navigates to a different ID)
watch(
  () => conversationId.value,
  (newVal) => {
    if (newVal !== null && newVal !== undefined && newVal !== '') {
      conversationsStore.fetchMessages(newVal)
      // Mark conversation as viewed
      conversationsStore.markConversationAsViewed(newVal)
      checkForChanges()
    }
  }
)

// Also check when AI finishes running
watch(isAiRunning, (newVal, oldVal) => {
  if (oldVal && !newVal && conversationHasGithub.value) {
    checkForChanges()
  }
})

/** AI SUGGESTIONS **/
const aiSuggestions = ref([])

watch(
  () => contextsStore.contextSelected,
  async (newVal, oldVal) => {
    if (newVal?.id === oldVal?.id) return
    aiSuggestions.value = []

    // If user is on an existing conversation (not /chat/new), redirect to /chat/new
    if (conversationId.value && conversationId.value !== 'new') {
      router.push({ path: '/chat/new' })
      return
    }

    if (!conversationId.value) {
      await fetchAISuggestions()
    }
  }
)

const fetchAISuggestions = async () => {
  try {
    if (!contextsStore.contextSelected) return
    const response = await axios.get(`/api/contexts/${contextsStore.contextSelected?.id}/questions`)
    aiSuggestions.value = response.data
  } catch (error: any) {
    console.error('Error fetching AI suggestions:', error)
    if (
      error.response?.status === 402 &&
      error.response?.data?.message?.includes('SUBSCRIPTION_REQUIRED')
    ) {
      conversationsStore.subscriptionRequired = true
    }
    aiSuggestions.value = [] // Reset suggestions in case of error
  }
}

const applySuggestion = (suggestion: string) => {
  inputText.value = suggestion
  handleSendMessage()
  // Empty the suggestions
  aiSuggestions.value = []
}
/** END AI SUGGESTIONS **/

const stopQuery = async () => {
  socket.emit('stop', conversationId.value)
}

// Reference to the scroll container to allow scrolling to bottom
const scrollContainer = ref<HTMLDivElement | null>(null)

const scrollToBottom = () => {
  nextTick(() => {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
    }
  })
}
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
