import { fetchUser, isAuthenticated } from '@/stores/auth'
import { useDatabasesStore } from '@/stores/databases'

export const authGuard = async (to: any, from: any, next: any) => {
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
      const databasesStore = useDatabasesStore()
      await databasesStore.fetchDatabases({ refresh: true })
      if (databasesStore.databases.length === 0 && to.path !== '/setup') {
        next('/setup')
      } else {
        next()
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      next('/login') // Redirect to login on error
    }
  } else {
    // User is already authenticated, allow navigation
    next()
  }
}
