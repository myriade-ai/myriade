import {
  fetchUser,
  getLoginUrl,
  isAnonymous,
  isAuthenticated,
  redirectToSignUp
} from '@/stores/auth'
import { useContextsStore } from '@/stores/contexts'
import { useDatabasesStore } from '@/stores/databases'

// HTTP 451: Unavailable For Legal Reasons - used for organization restriction
const ORGANIZATION_RESTRICTED_STATUS = 451

export const authGuard = async (to: any, _from: any, next: any) => {
  if (to.path === '/logged') {
    next('/')
  } else if (to.meta.requiresGuest) {
    next()
  } else if (!isAuthenticated.value) {
    try {
      await fetchUser()
      const databasesStore = useDatabasesStore()
      await databasesStore.fetchDatabases({ refresh: true })
      next()
    } catch (error) {
      console.error('Auth check failed:', error)
      if ((error as any)?.response?.status === ORGANIZATION_RESTRICTED_STATUS) {
        next('/organization-restricted')
        return
      }
      const loginUrl = await getLoginUrl()
      window.location.href = loginUrl
    }
  } else {
    // User is already authenticated, allow navigation
    next()
  }
}

export const redirectToWelcome = async (to: any, _from: any, next: any) => {
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
