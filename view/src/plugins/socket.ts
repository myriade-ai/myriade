import { io } from 'socket.io-client'
import { ref } from 'vue'

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL

// Create reactive connection state
export const isConnected = ref(true)
export const reconnecting = ref(false)

// Configure socket with more aggressive reconnection settings
export const socket = io(SOCKET_URL, {
  reconnection: true,
  reconnectionAttempts: Infinity,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  timeout: 20000,
  autoConnect: true, // Ensure auto-connection is enabled
  transports: ['websocket', 'polling'], // Try WebSocket first, fallback to polling
  forceNew: true, // Force a new connection
  randomizationFactor: 0.5 // Add some randomization to the reconnection delay
})

// Add event listeners for connection status
socket.on('connect', () => {
  console.log('Socket connected')
  isConnected.value = true
  reconnecting.value = false
})

socket.on('disconnect', (reason) => {
  console.log('Socket disconnected:', reason)
  isConnected.value = false
  // Handle specific disconnect reasons
  if (reason === 'io server disconnect') {
    // If the server has dropped the connection, try to reconnect manually
    socket.connect()
  }
  // For all other reasons, socket.io will try to reconnect automatically
})

socket.on('reconnect', (attemptNumber) => {
  console.log('Socket reconnected after', attemptNumber, 'attempts')
  isConnected.value = true
  reconnecting.value = false
})

socket.on('reconnect_attempt', (attemptNumber) => {
  console.log('Socket reconnection attempt:', attemptNumber)
  reconnecting.value = true
})

socket.on('reconnect_error', (error) => {
  console.error('Socket reconnection error:', error)
  isConnected.value = false
  // Don't set reconnecting to false here, let it continue trying
})

socket.on('reconnect_failed', () => {
  console.error('Socket reconnection failed')
  isConnected.value = false
  reconnecting.value = false
  // Try to reconnect manually after a short delay
  setTimeout(() => {
    console.log('Attempting manual reconnection...')
    socket.connect()
  }, 2000)
})

// Add a ping mechanism to detect connection issues early
setInterval(() => {
  if (socket.connected) {
    socket.emit('ping')
  }
}, 25000)

socket.on('pong', () => {
  console.debug('Socket connection alive')
})

// Export a function to force reconnection if needed
export const forceReconnect = () => {
  socket.disconnect()
  setTimeout(() => {
    socket.connect()
  }, 1000)
}
