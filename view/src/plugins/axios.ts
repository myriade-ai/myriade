import { isAnonymous, logout, redirectToSignUp } from '@/stores/auth'
import axios from 'axios'

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.log('ERROR: Unauthorized', error.response)
      logout()
    } else if (error.response?.status === 402) {
      // Payment Required - no credits remaining
      if (isAnonymous.value) {
        // Redirect anonymous users to sign up when they run out of credits
        redirectToSignUp()
      } else {
        // For regular users, you might want to show a subscription modal
        // For now, we'll just log the error and let the component handle it
        console.log('Regular user has insufficient credits')
      }
    }
    return Promise.reject(error)
  }
)

export default axios
