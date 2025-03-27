import { logout } from '@/stores/auth'
import axios from 'axios'

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.log('ERROR: Unauthorized', error.response)
      logout()
    }
    return Promise.reject(error)
  }
)

export default axios
