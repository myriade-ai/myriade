import axios from '@/plugins/axios'
import { computed, ref } from 'vue'

export const user = ref({
  id: null,
  email: null,
  firstName: null,
  lastName: null,
  profilePictureUrl: null,
  isAdmin: false,
  inOrganization: false,
  credits: 0,
  hasActiveSubscription: false
})

export const isAuthenticated = computed(() => user.value.id !== null)

export const getLoginUrl = async () => {
  const response = await axios.get('/api/auth')
  const { authorization_url } = response.data
  return authorization_url
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
    user.value.inOrganization = response.data.organization_id !== null
    user.value.credits = response.data.credits || 0
    user.value.hasActiveSubscription = response.data.has_active_subscription || false
  } catch (error) {
    console.error('Failed to fetch user:', error)
  }
}

export const logout = async () => {
  try {
    // We get the logout url from the server
    const { data } = await axios.post('/api/logout')
    const { logout_url } = data
    window.location.href = logout_url
  } catch (error) {
    console.error('Logout failed, user is not logged in:', error)
    // If logout fails, we redirect to the login page
    const response = await axios.get('/api/auth')
    const { authorization_url } = response.data
    window.location.href = authorization_url
  }
}
