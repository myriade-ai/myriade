import {
  fetchUser,
  getLoginUrl,
  isAnonymous,
  isAuthenticated,
  redirectToSignUp
} from '@/stores/auth'
import { useContextsStore } from '@/stores/contexts'
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

export const redirectToWelcome = async (to: any, from: any, next: any) => {
  const contextsStore = useContextsStore()
  if (!isAnonymous.value) {
    next()
    return
  }

  // Redirect anonymous users without context to welcome page
  if (!contextsStore.contextSelected && to.path !== '/welcome') {
    next('/welcome')
    return
  }

  // Redirect anonymous users with context away from welcome page
  if (contextsStore.contextSelected && to.path === '/welcome') {
    next('/')
    return
  }

  // Re-route anonymous users if they try to access restricted pages
  if (to.path === '/setup') {
    await redirectToSignUp()
    return
  }

  next()
}
