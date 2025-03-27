import { fetchUser, isAuthenticated } from '@/stores/auth'

export const authGuard = async (to, from, next) => {
  if (to.path === '/logged') {
    // Wait for 3 seconds before redirecting
    // To avoid a bug where the token is not yet valid (iat)
    await new Promise((resolve) => setTimeout(resolve, 3000))
    next('/')
  } else if (to.meta.requiresGuest) {
    next()
  } else if (!isAuthenticated.value) {
    try {
      await fetchUser()
    } catch (error) {
      console.error('Auth check failed:', error)
    }
    next()
  } else {
    next()
  }
}
