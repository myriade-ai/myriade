import { createClient } from '@propelauth/javascript'
import type { AuthenticationInfo, IAuthClient } from '@propelauth/javascript'
import { ref } from 'vue'
import axios from 'axios'

export const user = ref(null)

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
  // Seems a bug that this call the api multiple times...
  const authInfo = await client.getAuthenticationInfoOrNull()
  if (!authInfo) {
    client.redirectToLoginPage()
  }

  console.log('You are logged in as ' + authInfo.user.email) //
  user.value = authInfo.user
  axios.defaults.headers.common['Authorization'] = `Bearer ${authInfo.accessToken}`
}

export const logout = () => {
  client.logout(false)
  client.redirectToLoginPage()
}
