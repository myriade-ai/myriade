// Example of a simple reactive store
import { socket } from '@/plugins/socket'
import { ref } from 'vue'

export const conversationStatuses = ref<Record<string, { status: string; error: string }>>({})

socket.on('status', (payload) => {
  const { conversation_id, status, error } = payload
  conversationStatuses.value[conversation_id] = { status, error }
})

