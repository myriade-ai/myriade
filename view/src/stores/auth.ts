import axios from '@/plugins/axios'
import { computed, ref } from 'vue'

export const user = ref({
  id: null,
  email: null,
  firstName: null,
  lastName: null,
  profilePictureUrl: null,
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
    user.value.profilePictureUrl = response.data.profile_picture_url
    user.value.isAdmin = response.data.role === 'admin'
  } catch (error) {
    console.error('Failed to fetch user:', error)
  }
}

export const logout = async () => {
  try {
    const { data } = await axios.post('/api/logout')
    const { logout_url } = data
    window.location.href = logout_url
  } catch (error) {
    console.error('Logout failed, user is not logged in:', error)
    window.location.href = '/login'
  }
}
