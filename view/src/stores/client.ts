import { createClient } from '@propelauth/javascript'
import type { AuthenticationInfo, IAuthClient } from '@propelauth/javascript'
import { ref } from 'vue'
import axios from 'axios'

export const user = ref({
  isAdmin: false,
  email: null,
  id: null
})

// If VITE_PROPELAUTH_URL is undefined, then have a mockup auth server
// Otherwise, use the real auth server
export let client: Partial<IAuthClient>

if (import.meta.env.VITE_PROPELAUTH_URL === undefined) {
  client = {
    // @ts-ignore
    getAuthenticationInfoOrNull(
      forceRefresh?: boolean
    ): Promise<Partial<AuthenticationInfo> | null> {
      return Promise.resolve({
        accessToken: 'admin',
        user: {
          userId: 'local',
          email: 'admin@localhost',
          enabled: true,
          emailConfirmed: true,
          locked: false,
          mfaEnabled: false
        }
      })
    },
    logout(redirectAfterLogout: boolean): Promise<void> {
      return Promise.resolve()
    },
    redirectToLoginPage(): void {},
    redirectToAccountPage(): void {},
    redirectToOrgPage(orgId?: string): void {}
  }
} else {
  client = createClient({
    authUrl: import.meta.env.VITE_PROPELAUTH_URL,
    enableBackgroundTokenRefresh: false
  })
}

export const authenticate = async () => {
  const authInfo = await client.getAuthenticationInfoOrNull()
  if (!authInfo) {
    client.redirectToLoginPage()
  }

  user.value = {
    isAdmin: authInfo.user.email === 'admin@localhost', // Temporary solution until backend is updated
    email: authInfo.user.email,
    id: authInfo.user.userId
  }
  axios.defaults.headers.common['Authorization'] = `Bearer ${authInfo.accessToken}`
}

export const logout = () => {
  client.logout(false)
  client.redirectToLoginPage()
}
