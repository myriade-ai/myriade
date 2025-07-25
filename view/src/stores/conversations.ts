import axios from '@/plugins/axios'
import { isConnected, socket } from '@/plugins/socket'
import { useContextsStore } from '@/stores/contexts'
import type { AxiosResponse } from 'axios'
import { defineStore } from 'pinia'
import sqlPrettier from 'sql-prettier'
import { computed, ref, watch } from 'vue'

// Example "Status" constants
export const STATUS = {
  PENDING: 'pending',
  RUNNING: 'running',
  CLEAR: 'clear',
  TO_STOP: 'to_stop',
  ERROR: 'error'
} as const

// Define your conversation shape
export interface ConversationInfo {
  id: string
  name: string
  owner: string
  databaseId: string
  projectId: string
  createdAt: Date
  updatedAt: Date
}

// Define your message shape
export interface Message {
  id: string
  createdAt: Date
  role: 'user' | 'assistant' | 'function' | 'system'
  content: string
  isAnswer?: boolean
  functionCall?: {
    name: string
    arguments: any
  }
}

// A small type for tracking conversation status & errors
interface ConversationStatus {
  status: string
  error: string
}

export interface Conversation extends ConversationInfo {
  messages: Message[]
  // TODO: add conversation status
}

export const useConversationsStore = defineStore('conversations', () => {
  // ——————————————————————————————————————————————————
  // STATE
  // ——————————————————————————————————————————————————
  const conversations = ref<Record<string, Conversation>>({})
  const conversationStatuses = ref<Record<string, ConversationStatus>>({})
  const subscriptionRequired = ref(false)

  // Watch for context changes and fetch conversations
  const contextsStore = useContextsStore()
  watch(
    () => contextsStore.contextSelected,
    (newContext, oldContext) => {
      if (newContext && newContext.id && newContext.id !== oldContext?.id) {
        // clear the conversations store
        conversations.value = {}
        conversationStatuses.value = {}
        fetchConversations(newContext.id)
      }
    },
    { immediate: true, deep: true }
  )

  // ——————————————————————————————————————————————————
  // GETTERS
  // ——————————————————————————————————————————————————
  // E.g. Return a conversation by id
  function getConversationById(id: string) {
    if (!conversations.value[id]) {
      return null
    }
    return {
      ...conversations.value[id],
      // We add status and error to the conversation object
      status: conversationStatuses.value[id]?.status,
      error: conversationStatuses.value[id]?.error
    }
  }

  // If you want a sorted conversation list
  const sortedUserConversations = computed(() => {
    // TODO: filter by user
    return [...Object.values(conversations.value)].sort(
      (a, b) => b.updatedAt.getTime() - a.updatedAt.getTime()
    )
  })

  // ——————————————————————————————————————————————————
  // ACTIONS
  // ——————————————————————————————————————————————————

  // 1) Fetch the full list of conversations
  async function fetchConversations(contextId: string) {
    const res: AxiosResponse<ConversationInfo[]> = await axios.get('/api/conversations', {
      params: { contextId }
    })
    const fetchedConversations = res.data.map((conv) => ({
      ...conv,
      createdAt: new Date(conv.createdAt),
      updatedAt: new Date(conv.updatedAt)
    }))
    // Update the conversations store but don't overwrite existing field messages
    fetchedConversations.forEach((conv) => {
      conversations.value[conv.id] = {
        ...conv,
        messages: conversations.value[conv.id]?.messages || []
      }
    })
    // Remove conversations that are not in the fetched list
    Object.keys(conversations.value).forEach((id) => {
      if (!fetchedConversations.some((conv) => conv.id === id)) {
        delete conversations.value[id]
      }
    })
  }

  // 2) Fetch messages for a single conversation
  async function fetchMessages(conversationId: string) {
    try {
      const response = await axios.get(`/api/conversations/${conversationId}`)
      // Update the conversation in the store
      const newConv: Conversation = {
        ...response.data,
        createdAt: new Date(response.data.createdAt),
        updatedAt: new Date(response.data.updatedAt),
        messages: response.data.messages
      }
      conversations.value[conversationId] = newConv
    } catch (error: any) {
      // Mark this conversation as error
      conversationStatuses.value[conversationId] = {
        status: STATUS.ERROR,
        error: 'Error fetching messages'
      }
      // Optional: Clear messages if needed
      const conv = getConversationById(conversationId)
      if (conv) {
        conv.messages = []
      }
    }
  }

  // 3) Helper to set conversation status
  function setConversationStatus(conversationId: string, status: string, error: string = '') {
    conversationStatuses.value[conversationId] = { status, error }
  }

  // 4) Helper: set to 'pending' then revert if no response
  function setStatusToPending(conversationId: string) {
    setConversationStatus(conversationId, STATUS.PENDING, '')
    // If still pending after 5s, revert to CLEAR
    setTimeout(() => {
      if (conversationStatuses.value[conversationId]?.status === STATUS.PENDING) {
        setConversationStatus(conversationId, STATUS.CLEAR)
      }
    }, 5000)
  }

  // 5) Send message over Socket.IO
  async function sendMessage(conversationId: string, messageContent: string, type: 'text' | 'SQL') {
    const convStatus = conversationStatuses.value[conversationId]
    // If it's already running/pending, block
    if (convStatus && [STATUS.RUNNING, STATUS.PENDING].includes(convStatus.status)) {
      throw new Error('Conversation is already running')
    }
    if (!isConnected.value) {
      throw new Error('Socket is disconnected')
    }

    if (type === 'text') {
      socket.emit('ask', conversationId, messageContent)
    } else if (type === 'SQL') {
      socket.emit('query', conversationId, messageContent)
    }
    setStatusToPending(conversationId)
  }

  // 6) Receive an incoming message from the socket
  function receiveMessage(incomingMsg: any) {
    const convId = incomingMsg.conversationId
    const conversation = getConversationById(convId)
    if (!conversation) return

    // e.g. prettify any SQL in functionCall.arguments.query
    if (incomingMsg?.functionCall?.arguments?.query) {
      incomingMsg.functionCall.arguments.query = sqlPrettier.format(
        incomingMsg.functionCall.arguments.query
      )
    }

    // Check if message already in conversation
    const existing = conversation.messages.find((m) => m.id === incomingMsg.id)
    if (existing) {
      // Update that message
      existing.content = incomingMsg.content
      existing.functionCall = incomingMsg.functionCall
      existing.role = incomingMsg.role
      // If other fields exist, update them as well
    } else {
      conversation.messages.push(incomingMsg)
    }
    // Possibly update updatedAt
    conversation.updatedAt = new Date()
  }

  function regenerateFromMessage(messageId: string, messageContent?: string) {
    // Find conversationId from messageId
    const conversationId: string | undefined = Object.keys(conversations.value).find((id) =>
      conversations.value[id].messages.some((m) => m.id === messageId)
    )
    if (!conversationId) {
      throw new Error('Conversation not found')
    }

    if (messageContent) {
      // Update the message content
      const message = conversations.value[conversationId].messages.find((m) => m.id === messageId)
      if (message) {
        message.content = messageContent
      }
    }
    socket.emit('regenerateFromMessage', conversationId, messageId, messageContent)
  }

  async function deleteConversation(id: string) {
    await axios.delete(`/api/conversations/${id}`)
    delete conversations.value[id]
  }

  async function renameConversation(id: string, name: string) {
    await axios.put(`/api/conversations/${id}`, { name })
    if (conversations.value[id]) {
      conversations.value[id].name = name
      conversations.value[id].updatedAt = new Date()
    }
  }

  async function createConversation(contextId: string) {
    const newConversation: AxiosResponse<ConversationInfo> = await axios.post(
      '/api/conversations',
      { contextId }
    )
    const newConv: Conversation = {
      ...newConversation.data,
      createdAt: new Date(newConversation.data.createdAt),
      updatedAt: new Date(newConversation.data.updatedAt),
      messages: []
    }
    conversations.value[newConv.id] = newConv
    return newConv
  }

  // ——————————————————————————————————————————————————
  // SOCKET EVENT HANDLERS
  // ——————————————————————————————————————————————————
  socket.on('delete-message', (messageId: string) => {
    // Remove that message from whichever conversation it belongs to
    const conversationId: string | undefined = Object.keys(conversations.value).find((id) =>
      conversations.value[id].messages.some((m) => m.id === messageId)
    )
    if (!conversationId) {
      throw new Error('Conversation not found')
    }
    conversations.value[conversationId].messages = conversations.value[
      conversationId
    ].messages.filter((m) => m.id !== messageId)
  })

  socket.on('response', (payload: any) => {
    if (subscriptionRequired.value) {
      subscriptionRequired.value = false
    }
    receiveMessage(payload)
  })

  socket.on('status', (payload: any) => {
    const { conversation_id, status, error } = payload
    setConversationStatus(conversation_id, status, error)
  })

  socket.on('error', (error: any) => {
    if (error.message === 'SUBSCRIPTION_REQUIRED') {
      subscriptionRequired.value = true
      setConversationStatus(error.conversationId, STATUS.CLEAR)
    }
  })

  // 8) Return references to everything
  return {
    // state
    conversations,
    conversationStatuses,
    subscriptionRequired,
    // getters
    sortedUserConversations,
    getConversationById,
    // actions conversations
    fetchConversations,
    deleteConversation,
    renameConversation,
    // actions messages
    fetchMessages,
    sendMessage,
    regenerateFromMessage,
    // actions conversations
    createConversation
  }
})
