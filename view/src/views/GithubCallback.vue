<template>
  <div class="min-h-screen flex items-center justify-center bg-background">
    <div class="bg-card shadow-sm rounded-lg p-8 max-w-md w-full text-center space-y-4">
      <h1 class="text-lg font-semibold text-foreground">{{ title }}</h1>
      <p class="text-sm text-muted-foreground">{{ description }}</p>
      <div v-if="status === 'error'" class="text-sm text-error-600">{{ errorMessage }}</div>
      <div v-if="status === 'pending'" class="text-sm text-muted-foreground">
        You will be redirected shortly…
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from '@/plugins/axios'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const status = ref<'pending' | 'success' | 'error'>('pending')
const errorMessage = ref('')

const title = computed(() => {
  switch (status.value) {
    case 'success':
      return 'GitHub authorisation complete'
    case 'error':
      return 'GitHub authorisation failed'
    default:
      return 'Completing GitHub authorisation'
  }
})

const description = computed(() => {
  switch (status.value) {
    case 'success':
      return 'Returning you to the database configuration page.'
    case 'error':
      return 'We could not connect your GitHub account. You will be redirected back to try again.'
    default:
      return 'Please wait while we finalise the GitHub connection.'
  }
})

const route = useRoute()
const router = useRouter()

onMounted(async () => {
  const code = typeof route.query.code === 'string' ? route.query.code : null
  const state = typeof route.query.state === 'string' ? route.query.state : null
  const oauthError = typeof route.query.error === 'string' ? route.query.error : null

  if (oauthError) {
    status.value = 'error'
    errorMessage.value = oauthError
    await router.replace({ name: 'DatabaseList' })
    return
  }

  if (!code || !state) {
    status.value = 'error'
    errorMessage.value = 'Missing GitHub OAuth parameters.'
    await router.replace({ name: 'DatabaseList' })
    return
  }

  const storedState = localStorage.getItem(`github_oauth_state:${state}`)
  if (!storedState) {
    status.value = 'error'
    errorMessage.value = 'OAuth session expired. Please start the connection again.'
    await router.replace({ name: 'DatabaseList' })
    return
  }

  try {
    const parsed = JSON.parse(storedState) as { databaseId: string; redirectUri: string }
    await axios.post(`/api/databases/${parsed.databaseId}/github/oauth/exchange`, {
      code,
      state,
      redirectUri: parsed.redirectUri
    })
    localStorage.setItem(
      `github_oauth_result:${parsed.databaseId}`,
      JSON.stringify({ success: true })
    )
    status.value = 'success'
    await router.replace({ name: 'DatabaseEdit', params: { id: parsed.databaseId } })
  } catch (err: any) {
    try {
      const parsed = JSON.parse(storedState) as { databaseId: string }
      const message = err.response?.data?.error || err.message || 'GitHub OAuth exchange failed.'
      localStorage.setItem(
        `github_oauth_result:${parsed.databaseId}`,
        JSON.stringify({ success: false, error: message })
      )
      errorMessage.value = message
      status.value = 'error'
      await router.replace({ name: 'DatabaseEdit', params: { id: parsed.databaseId } })
    } catch {
      status.value = 'error'
      errorMessage.value = 'GitHub OAuth exchange failed.'
      await router.replace({ name: 'DatabaseList' })
    }
  } finally {
    localStorage.removeItem(`github_oauth_state:${state}`)
  }
})
</script>
