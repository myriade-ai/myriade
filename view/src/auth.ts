import { isAuthenticated, fetchUser } from '@/stores/auth'

export const authGuard = async (to, from, next) => {
  if (to.meta.requiresGuest) {
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
