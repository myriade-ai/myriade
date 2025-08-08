import axios from '@/plugins/axios'
import { computed, ref } from 'vue'

export const defaultUser = {
  id: null,
  email: null,
  firstName: null,
  lastName: null,
  profilePictureUrl: null,
  isAdmin: false,
  inOrganization: false,
  credits: 0,
  role: null
}

export const user = ref(defaultUser)

export const isAuthenticated = computed(() => user.value.id !== null)

export const isAnonymous = computed(() => {
  return user.value?.role === 'anonymous'
})

export const redirectToSignUp = async () => {
  window.location.href = 'https://sign.myriade.ai/sign-up'
}

export const getLoginUrl = async () => {
  const response = await axios.get('/api/auth')
  const { authorization_url } = response.data
  return authorization_url
}

export const fetchCredits = async () => {
  try {
    // Fetch credits from proxy
    const response = await axios.get('/api/user/credits')
    user.value.credits = response.data.credits_remaining || 0
    return user.value.credits
  } catch (error) {
    console.error('Failed to fetch credits:', error)
    user.value.credits = 0
    return 0
  }
}

export const updateCredits = (newCredits: number) => {
  user.value.credits = newCredits
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
    user.value.role = response.data.role

    // Fetch credits from proxy
    await fetchCredits()
  } catch (error) {
    console.error('Failed to fetch user:', error)
  }
}

export const logout = async () => {
  // Clear user state immediately
  user.value = defaultUser

  // Always try proper logout first, handle failures gracefully
  try {
    const { data } = await axios.post('/api/auth/logout')
    const { logout_url } = data
    if (logout_url) {
      window.location.href = logout_url
      return
    }
  } catch (error) {
    console.error('Logout failed:', error)
  }

  // If logout failed or no logout_url, get fresh auth URL
  try {
    const response = await axios.get('/api/auth')
    const { authorization_url } = response.data
    if (authorization_url) {
      window.location.href = authorization_url
    } else {
      window.location.href = '/login'
    }
  } catch (error) {
    console.error('Failed to get auth URL:', error)
    window.location.href = '/login'
  }
}
