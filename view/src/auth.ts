import { fetchUser, getLoginUrl, isAuthenticated } from '@/stores/auth'
import { useDatabasesStore } from '@/stores/databases'

export const authGuard = async (to: any, from: any, next: any) => {
  if (to.path === '/logged') {
    next('/')
  } else if (to.meta.requiresGuest) {
    next()
  } else if (!isAuthenticated.value) {
    try {
      await fetchUser()
    } catch (error) {
      console.error('Auth check failed:', error)
      const loginUrl = await getLoginUrl()
      window.location.href = loginUrl
    }
    const databasesStore = useDatabasesStore()
    await databasesStore.fetchDatabases({ refresh: true })
    next()
  } else {
    // User is already authenticated, allow navigation
    next()
  }
}
