import { socket } from '@/plugins/socket';
import { ref } from 'vue';

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


export const setStatusToPending = (conversationId: string) => {
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
