import axios from '@/plugins/axios'
import { ref } from 'vue'

const currentVersion = ref<string | null>(null)
const latestVersion = ref<string | null>(null)

const checkVersion = async () => {
  try {
    const response = await axios.get('/api/version')

    // Initialize current version on first run
    if (!currentVersion.value) {
      currentVersion.value = response.data.version
      latestVersion.value = response.data.latest
    }

    // Check if the app version has changed (hot reload/update)
    if (response.data.version !== currentVersion.value) {
      console.log('App version changed, refreshing...')
      window.location.reload() // Force reload from server
      return
    }

    // Check for new version available
    if (response.data.hasUpdate && response.data.latest) {
      console.log(
        `Myriade: new version available: ${response.data.latest} (current: ${response.data.version})`
      )
    }
  } catch (error) {
    console.error('Version check failed:', error)
  }
}

checkVersion()
setInterval(checkVersion, 10 * 60 * 1000) // Check every 10 mins
