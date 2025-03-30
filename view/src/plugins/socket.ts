import { io } from 'socket.io-client'
import { ref } from 'vue'

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL

// Configure socket with more aggressive reconnection settings
export const socket = io(SOCKET_URL, {
  transports: ['polling']
})
export const isConnected = ref(socket.connected)

// Update the reactive reference when connection status changes
const updateConnectionStatus = () => {
  isConnected.value = socket.connected
}

const forceReconnect = () => {
  console.log('manually reconnecting...')
  socket.connect()
}
socket.on('connect_error', updateConnectionStatus)
socket.on('connect_timeout', updateConnectionStatus)
socket.on('connect', updateConnectionStatus)
socket.on('disconnect', updateConnectionStatus)
socket.on('reconnect', updateConnectionStatus)
socket.on('reconnect_error', updateConnectionStatus)
socket.on('reconnect_failed', updateConnectionStatus)

// Add a ping mechanism to detect connection issues early
setInterval(() => {
  if (socket.connected) {
    socket.emit('ping')
  } else if (socket.io.skipReconnect) {
    forceReconnect()
  }
}, 15000)

socket.on('pong', () => {
  console.debug('Socket connection alive')
})

// Add event listeners for connection status
socket.on('connect', () => {
  console.log('Socket connected')
})

socket.on('disconnect', (reason) => {
  console.log('Socket disconnected:', reason)
  // Handle specific disconnect reasons
  if (reason === 'io server disconnect') {
    // If the server has dropped the connection, try to reconnect manually
    socket.connect()
  }
  // For all other reasons, socket.io will try to reconnect automatically
})

socket.on('reconnect', (attemptNumber) => {
  console.log('Socket reconnected after', attemptNumber, 'attempts')
})

socket.on('reconnect_attempt', (attemptNumber) => {
  console.log('Socket reconnection attempt:', attemptNumber)
})

socket.on('reconnect_error', (error) => {
  console.error('Socket reconnection error:', error)
  // Don't set reconnecting to false here, let it continue trying
})

socket.on('reconnect_failed', () => {
  console.error('Socket reconnection failed')
})

socket.on('error', (error) => {
  console.error('Socket error:', error)
})
