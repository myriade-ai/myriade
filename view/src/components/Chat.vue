<template>
  <div class="w-full h-screen flex justify-center items-center px-4">
    <div class="flex flex-col w-full max-w-2xl h-full">
      <div class="flex flex-col flex-grow h-full overflow-y-auto">
        <div class="w-full pt-4">
          <!-- Dropdown to select the dabase to query -->
          <label class="block text-gray-700 text-sm font-bold mb-2" for="database">
            Database
          </label>
          <BaseSelector
            :options="databases"
            v-model="databaseSelected"
            class="w-full"
            placeholder="Select a database"
            :disabled="conversationId"
          />
          <br />
          <div class="flex items-center justify-between mb-4 pl-2" v-if="hasHiddenMessages">
            <BaseSwitch
              :modelValue="config.showHiddenMessages"
              @update:modelValue="config.updateShowHiddenMessages"
              class="float-right"
            >
              <span class="text-gray-700">Show hidden messages</span>
            </BaseSwitch>
          </div>
          <ul class="list-none">
            <li v-for="(message, id) in messagesWithDisplay" :key="id">
              <MessageDisplay
                :key="id"
                :message="message"
                @editInlineClick="editInline"
                v-if="message?.display !== false || config.showHiddenMessages"
              />
            </li>
          </ul>
        </div>

        <div class="w-full py-4">
          <div class="w-full flex justify-center">
            <!-- Display error message if queryStatus is error -->
            <div v-if="queryStatus === 'error'" class="flex flex-col items-center">
              <div>
                <p class="text-red-500">{{ errorMessage }}</p>
              </div>
              <div>
                <BaseButton class="my-4" @click="regenerate">Regenerate</BaseButton>
              </div>
            </div>

            <!-- Display Regenerating button if query is not running and last message is not a query -->
            <div v-else-if="queryStatus != STATUS.RUNNING && lastMessage">
              <BaseButton @click="regenerate">Regenerate</BaseButton>
            </div>

            <div v-if="queryStatus === STATUS.RUNNING">
              <!-- Add loading icon, centered, displayed only if a query is running -->
              <LoaderIcon /><br />
              <!-- Add stop button, centered, displayed only if a query is running -->
              <button
                @click="stopQuery"
                :disabled="queryStatus === 'to_stop'"
                class="w-full bg-gray-500 text-white py-2 px-4 rounded"
                type="submit"
              >
                Stop
              </button>
            </div>
          </div>
        </div>
      </div>
      <div class="w-full py-8">
        <button
          class="inline-flex items-center rounded-md border border-gray-300 bg-white px-2.5 py-0.5 text-sm font-medium leading-5 text-gray-700 shadow-sm hover:bg-gray-50"
          :style="editMode == 'TEXT' ? 'background-color: #e5e7eb' : ''"
          @click="editMode = 'TEXT'"
        >
          Text
        </button>
        <button
          class="inline-flex items-center rounded-md border border-gray-300 bg-white px-2.5 py-0.5 mx-0.5 text-sm font-medium leading-5 text-gray-700 shadow-sm hover:bg-gray-50"
          :style="editMode == 'SQL' ? 'background-color: #e5e7eb' : ''"
          @click="editMode = 'SQL'"
        >
          Editor
        </button>
        <div class="w-full flex py-1" v-if="editMode == 'SQL'">
          <BaseEditor v-model="inputSQL" @run-query="sendMessage" />
        </div>
        <div class="w-full flex py-1" v-else>
          <textarea
            @input="resizeTextarea"
            @keydown.enter="handleEnter"
            ref="inputTextarea"
            class="flex-grow py-2 px-3 rounded border border-gray-300"
            rows="1"
            placeholder="Type your message"
            v-model="inputText"
          ></textarea>
          <BaseButton class="w-24 ml-2" @click="sendMessage">Send</BaseButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import MessageDisplay from '@/components/MessageDisplay.vue'
import BaseSwitch from '@/components/BaseSwitch.vue'
import BaseSelector from '@/components/BaseSelector.vue'
import BaseButton from '@/components/BaseButton.vue'
import BaseEditor from '@/components/BaseEditor.vue'
import { ref, watch, onMounted, onUnmounted, computed, nextTick } from 'vue'
import axios from 'axios'
import io from 'socket.io-client'
import { useDatabases } from '@/stores/databases'
import { useRoute } from 'vue-router'
import { useRouter } from 'vue-router'
import { useConfigStore } from '@/stores/config'
import LoaderIcon from '@/components/icons/LoaderIcon.vue'
import sqlPrettier from 'sql-prettier'

const config = useConfigStore()

const route = useRoute()
const router = useRouter()
// Environment variable to set the dbt API endpoint.
const SOCKET_URL = import.meta.env.VITE_SOCKET_URL
const socket = io(SOCKET_URL)
const inputTextarea = ref(null)

const { databaseSelected, databases, selectDatabaseById } = useDatabases()

const STATUS = {
  RUNNING: 'running',
  CLEAR: 'clear',
  TO_STOP: 'to_stop',
  ERROR: 'error'
}

const inputText = ref('')
const inputSQL = ref('')
const messages = ref([])
const conversationId = computed(() => route.params.id)
const queryStatus = ref(STATUS.CLEAR)
const errorMessage = ref('')
const lastMessage = computed(() => messages.value[messages.value.length - 1])
const editMode = ref('TEXT')

const fetchMessages = async () => {
  // Replace with your dbt API endpoint to fetch messages.
  axios.get(`/api/conversations/${conversationId.value}`).then((response) => {
    const conversation = response.data
    // pretty parse
    messages.value = conversation.messages.map((message) => {
      let query = message?.functionCall?.arguments?.query
      if (query) {
        message.functionCall.arguments.query = sqlPrettier.format(query)
      }
      return message
    })
    selectDatabaseById(conversation.databaseId)
  })
}

watch(
  () => route.params.id,
  (newValue) => {
    inputText.value = ''
    if (newValue) {
      fetchMessages()
    } else {
      messages.value = []
    }
  }
)

const editInline = (query) => {
  inputSQL.value = query
  editMode.value = 'SQL'
}

const hasHiddenMessages = computed(() => {
  return messagesWithDisplay.value.some((message) => message.display === false)
})

const regenerate = async () => {
  // Replace with your dbt API endpoint to regenerate the conversation.
  socket.emit('regenerate', null, conversationId.value, databaseSelected.value.id)
}

const sendMessage = async () => {
  // If query is already running, do nothing.
  if (queryStatus.value === STATUS.RUNNING) {
    return
  }
  // Post in json format to your back-end API endpoint to get the response.
  if (editMode.value == 'SQL') {
    // Emit query and messages.length to the server.
    socket.emit('query', inputSQL.value, conversationId.value, databaseSelected.value.id)
  } else {
    // Emit ask question and messages.length to the server.
    socket.emit('ask', inputText.value, conversationId.value, databaseSelected.value.id)
  }

  // After 100ms, clear the input.
  setTimeout(() => {
    clearInput()
  }, 100)
}

const receiveMessage = async (message) => {
  let existing = messages.value.find((m) => m.id === message.id)
  if (existing) {
    existing.queryId = message.queryId
  } else {
    let query = message?.functionCall?.arguments?.query
    if (query) {
      message.functionCall.arguments.query = sqlPrettier.format(query)
    }
    messages.value.push(message)
  }
}

/* Modify Message display according to the following rules:
- if user message; display=true
- if last message from assistant (before an user message) and functionCall is null; display=true
else display=false
*/
const messagesWithDisplay = computed(() => {
  return messages.value.map((message) => {
    message.display =
      message.role === 'user' ||
      (message.role === 'assistant' &&
        (!message.functionCall || ['SUBMIT', 'PLOT_WIDGET'].includes(message.functionCall.name)))
    return message
  })
})

const stopQuery = async () => {
  socket.emit('stop', conversationId.value)
}

const handleEnter = (event) => {
  if (!event.shiftKey) {
    sendMessage()
  }
}
const clearInput = () => {
  inputText.value = ''
  inputSQL.value = ''
  resizeTextarea()
}

const handleConversationChange = (message) => {
  // If message has conversationId, it is a new conversation.
  if (message.conversationId !== 'new' && message.conversationId !== conversationId.value) {
    router.push({ path: `/chat/${message.conversationId}` })
  }
}

const updateStatus = (status, error) => {
  if (status === STATUS.ERROR) {
    errorMessage.value = error
  } else {
    errorMessage.value = ''
  }
  queryStatus.value = status
}

onMounted(async () => {
  inputTextarea.value.focus()
  inputTextarea.value.select()

  if (conversationId.value) {
    await fetchMessages()
  }

  socket.on('delete-message', (id) => {
    messages.value = messages.value.filter((message) => message.id !== id)
  })

  socket.on('response', (response) => {
    handleConversationChange(response)
    receiveMessage(response)
  })

  socket.on('status', (response) => {
    updateStatus(response.status, response?.error)
  })
})

onUnmounted(() => {
  socket.disconnect()
})

const resizeTextarea = () => {
  // Wait for next tick to get the updated DOM.
  nextTick(() => {
    inputTextarea.value.style.height = 'auto'
    inputTextarea.value.style.height = inputTextarea.value.scrollHeight + 'px'
  })
}
</script>

<style scoped>
textarea {
  height: auto;
}
</style>
