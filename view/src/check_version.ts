import axios from 'axios'
import { ref } from 'vue'

const currentVersion = ref(null)

const checkVersion = async () => {
  try {
    const response = await axios.get('/api/version')
    if (!currentVersion.value) {
      currentVersion.value = response.data.version
    } else if (response.data.version !== currentVersion.value) {
      console.log('New version detected, refreshing...')
      window.location.reload() // Force reload from server
    }
  } catch (error) {
    console.error('Version check failed:', error)
  }
}

checkVersion()
setInterval(checkVersion, 10 * 60 * 1000) // Check every 10 mins
