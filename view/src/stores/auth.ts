import { computed, ref } from 'vue'
import axios from '@/plugins/axios'

export const user = ref({
  id: null,
  email: null,
  firstName: null,
  lastName: null,
  imageUrl: null,
  isAdmin: false
})

export const isAuthenticated = computed(() => user.value.id !== null)

export const login = async () => {
  try {
    const response = await axios.get('/api/auth')
    window.location.href = response.data.authorization_url
  } catch (error) {
    console.error('Login failed:', error)
  }
}

export const fetchUser = async () => {
  try {
    const response = await axios.get('/api/user')
    user.value.id = response.data.id
    user.value.email = response.data.email
    user.value.firstName = response.data.first_name
    user.value.lastName = response.data.last_name
    user.value.imageUrl = response.data.image_url
    user.value.isAdmin = response.data.role === 'admin'
  } catch (error) {
    console.error('Failed to fetch user:', error)
  }
}

export const logout = async () => {
  try {
    // First, make a request to the server to clear the cookie
    await axios.post('/api/logout')

    // Then clear the local user state
    user.value = {
      id: null,
      email: null,
      firstName: null,
      lastName: null,
      imageUrl: null,
      isAdmin: false
    }

    window.location.href = '/login'
  } catch (error) {
    console.error('Logout failed:', error)
  }
}
