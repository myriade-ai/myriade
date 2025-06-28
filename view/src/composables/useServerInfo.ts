import { readonly, ref } from 'vue'

const serverIp = ref<string>('')
let isLoading = false
let hasLoaded = false

export const useServerInfo = () => {
  const fetchServerIp = async () => {
    if (isLoading || hasLoaded) return

    isLoading = true
    try {
      const response = await fetch('/api/server-info')
      const data = await response.json()
      serverIp.value = data.ip
      hasLoaded = true
    } catch (error) {
      console.error('Error fetching server IP:', error)
    } finally {
      isLoading = false
    }
  }

  // Auto-fetch on first use
  if (!hasLoaded && !isLoading) {
    fetchServerIp()
  }

  return {
    serverIp: readonly(serverIp),
    fetchServerIp
  }
}
