import axios from '@/plugins/axios'
import { isConnected, socket } from '@/plugins/socket'
import type { AxiosResponse } from 'axios'
import { ref } from 'vue'

// CONVERSATIONS

export type Conversation = {
  id: string
  name: string
  createdAt: Date
  updatedAt: Date
}

export const conversations = ref<Conversation[]>([])

export const fetchConversations = async () => {
  conversations.value = await axios
    .get('/api/conversations')
    // Parse the date string to a number
    .then((res: AxiosResponse<Conversation[]>) =>
      res.data.map((conversation: Conversation) => ({
        ...conversation,
        updatedAt: new Date(conversation.updatedAt)
      }))
    )
    .then((data: Conversation[]) =>
      data.sort((a: Conversation, b: Conversation) => b.updatedAt.getTime() - a.updatedAt.getTime())
    )
}

// STATUSES

export const STATUS = {
  PENDING: 'pending', // waiting for server response
  RUNNING: 'running',
  CLEAR: 'clear',
  TO_STOP: 'to_stop',
  ERROR: 'error'
}

export const conversationStatuses = ref<Record<string, { status: string; error: string }>>({})

socket.on('status', (payload) => {
  const { conversation_id, status, error } = payload
  conversationStatuses.value[conversation_id] = { status, error }
})

export const setStatusToPending = (conversationId?: string) => {
  // Update status to running
  conversationStatuses.value[conversationId] = {
    status: STATUS.PENDING,
    error: ''
  }
  // If the status is still pending after 5s, set to CLEAR
  setTimeout(() => {
    if (conversationStatuses.value[conversationId]?.status === STATUS.PENDING) {
      conversationStatuses.value[conversationId] = { status: STATUS.CLEAR, error: '' }
    }
  }, 5000)
}

export const sendMessage = async (
  type: 'text' | 'SQL',
  message: string,
  conversationId?: string,
  contextId?: string
) => {
  const conversationStatus = conversationStatuses.value[conversationId]
  // If conversation is already running, do nothing.
  if (
    conversationStatus?.status === STATUS.RUNNING ||
    conversationStatus?.status === STATUS.PENDING
  ) {
    throw new Error('Conversation is already running')
  }
  if (!isConnected.value) {
    throw new Error('Socket connection is lost')
  }
  if (type === 'text') {
    socket.emit('ask', message, conversationId, contextId)
  } else if (type === 'SQL') {
    socket.emit('query', message, conversationId, contextId)
  }
  setStatusToPending(conversationId)
}
