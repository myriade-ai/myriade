<template>
  <div class="p-4 bg-gray-50 rounded-lg space-y-4">
    <div>
      <h3 class="text-sm font-medium text-gray-900">GitHub Repository</h3>
      <p class="text-xs text-gray-500">
        Connect this datasource to a GitHub repository so conversations can edit files on a
        dedicated branch and open pull requests.
      </p>
    </div>

    <div v-if="loading" class="text-sm text-gray-600">Loading GitHub settings…</div>
    <div v-else-if="error" class="text-sm text-error-600">{{ error }}</div>
    <div v-else class="space-y-4">
      <div class="text-sm text-gray-700">
        <p v-if="githubSettings.repoFullName">
          Connected to
          <span class="font-medium">{{ githubSettings.repoFullName }}</span>
          <span v-if="githubSettings.defaultBranch">
            (default branch {{ githubSettings.defaultBranch }})
          </span>
        </p>
        <p v-else>No repository selected.</p>
        <p v-if="githubSettings.tokenExpiresAt" class="text-xs text-gray-500">
          Access token renews automatically and expires on {{ formattedExpiry }}.
        </p>
      </div>

      <p v-if="oauthMessage" class="text-sm text-success-600">{{ oauthMessage }}</p>
      <p v-if="oauthError" class="text-sm text-error-600">{{ oauthError }}</p>

      <div v-if="!githubSettings.hasToken" class="space-y-2">
        <p class="text-xs text-gray-500">
          Authorise Myriade with GitHub to list repositories and push branches for this datasource.
        </p>
        <Button @click="startOAuth" :is-loading="oauthStarting">
          <template #loading>Opening GitHub…</template>
          Connect GitHub
        </Button>
      </div>

      <div v-else class="space-y-3">
        <div class="space-y-2">
          <label class="text-xs font-medium text-gray-600">Repository</label>
          <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
            <select
              v-model="selectedRepoFullName"
              class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Select a repository</option>
              <option v-for="repo in repositories" :key="repo.full_name" :value="repo.full_name">
                {{ repo.full_name }} (default: {{ repo.default_branch || 'main' }})
              </option>
            </select>
            <Button
              variant="outline"
              size="sm"
              @click="fetchRepositories"
              :is-loading="loadingRepos"
            >
              <template #loading>Refreshing…</template>
              Refresh list
            </Button>
          </div>
          <p class="text-xs text-gray-500">
            Only repositories that the authorised GitHub account can access will appear here.
          </p>
        </div>

        <div v-if="selectedRepoFullName" class="space-y-2">
          <label class="text-xs font-medium text-gray-600">Default branch</label>
          <Input v-model="selectedDefaultBranch" placeholder="main" />
        </div>

        <div class="flex flex-wrap gap-2">
          <Button
            size="sm"
            @click="saveRepository"
            :disabled="!selectedRepoFullName"
            :is-loading="savingRepo"
          >
            <template #loading>Saving…</template>
            Save repository
          </Button>
          <Button
            size="sm"
            variant="outline"
            @click="disconnectRepository"
            :disabled="!githubSettings.repoFullName"
            :is-loading="disconnecting"
          >
            <template #loading>Disconnecting…</template>
            Disconnect
          </Button>
        </div>

        <p v-if="repoError" class="text-sm text-error-600">{{ repoError }}</p>
        <p v-if="repoSuccess" class="text-sm text-success-600">{{ repoSuccess }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import axios from '@/plugins/axios'
import { onMounted, ref, computed } from 'vue'

interface GithubSettingsPayload {
  connected: boolean
  hasToken: boolean
  repoOwner: string | null
  repoName: string | null
  repoFullName: string | null
  defaultBranch: string | null
  tokenExpiresAt: string | null
}

interface Props {
  databaseId: string
}

const props = defineProps<Props>()

const loading = ref(true)
const error = ref<string | null>(null)
const githubSettings = ref<GithubSettingsPayload>({
  connected: false,
  hasToken: false,
  repoOwner: null,
  repoName: null,
  repoFullName: null,
  defaultBranch: null,
  tokenExpiresAt: null
})
const repositories = ref<Array<{ full_name: string; default_branch: string }>>([])
const selectedRepoFullName = ref<string>('')
const selectedDefaultBranch = ref('main')
const loadingRepos = ref(false)
const savingRepo = ref(false)
const disconnecting = ref(false)
const repoError = ref<string | null>(null)
const repoSuccess = ref<string | null>(null)
const oauthStarting = ref(false)
const oauthError = ref<string | null>(null)
const oauthMessage = ref<string | null>(null)

const formattedExpiry = computed(() => {
  if (!githubSettings.value.tokenExpiresAt) return 'N/A'
  return new Date(githubSettings.value.tokenExpiresAt).toLocaleString()
})

const githubResultKey = computed(() => `github_oauth_result:${props.databaseId}`)

const fetchSettings = async () => {
  try {
    loading.value = true
    error.value = null
    const response = await axios.get(`/api/databases/${props.databaseId}/github/settings`)
    githubSettings.value = {
      connected: response.data.connected ?? false,
      hasToken: response.data.hasToken ?? false,
      repoOwner: response.data.repoOwner ?? null,
      repoName: response.data.repoName ?? null,
      repoFullName: response.data.repoFullName ?? null,
      defaultBranch: response.data.defaultBranch ?? null,
      tokenExpiresAt: response.data.tokenExpiresAt ?? null
    }
    selectedRepoFullName.value = response.data.repoFullName || ''
    selectedDefaultBranch.value = response.data.defaultBranch || 'main'
    if (
      githubSettings.value.repoFullName &&
      !repositories.value.some((repo) => repo.full_name === githubSettings.value.repoFullName)
    ) {
      repositories.value.unshift({
        full_name: githubSettings.value.repoFullName,
        default_branch: githubSettings.value.defaultBranch || 'main'
      })
    }
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to load GitHub settings'
  } finally {
    loading.value = false
  }
}

const fetchRepositories = async () => {
  repoError.value = null
  repoSuccess.value = null
  try {
    loadingRepos.value = true
    const response = await axios.get(`/api/databases/${props.databaseId}/github/repos`)
    repositories.value = response.data.repositories || []
    if (!repositories.value.length) {
      repoError.value = 'No repositories available for this account.'
    }
  } catch (err: any) {
    repoError.value = err.response?.data?.error || 'Failed to load repositories'
  } finally {
    loadingRepos.value = false
  }
}

const saveRepository = async () => {
  if (!selectedRepoFullName.value) {
    repoError.value = 'Select a repository to continue'
    return
  }
  const [owner, name] = selectedRepoFullName.value.split('/')
  try {
    savingRepo.value = true
    repoError.value = null
    repoSuccess.value = null
    await axios.put(`/api/databases/${props.databaseId}/github/settings`, {
      repo_owner: owner,
      repo_name: name,
      default_branch: selectedDefaultBranch.value || null
    })
    repoSuccess.value = 'Repository saved successfully'
    await fetchSettings()
  } catch (err: any) {
    repoError.value = err.response?.data?.error || 'Failed to save repository'
  } finally {
    savingRepo.value = false
  }
}

const disconnectRepository = async () => {
  try {
    disconnecting.value = true
    repoError.value = null
    repoSuccess.value = null
    await axios.put(`/api/databases/${props.databaseId}/github/settings`, {
      repo_owner: null,
      repo_name: null
    })
    repoSuccess.value = 'GitHub repository disconnected'
    selectedRepoFullName.value = ''
    await fetchSettings()
  } catch (err: any) {
    repoError.value = err.response?.data?.error || 'Failed to disconnect repository'
  } finally {
    disconnecting.value = false
  }
}

const startOAuth = async () => {
  try {
    oauthStarting.value = true
    oauthError.value = null
    const redirectUri = `${window.location.origin}/github/callback`
    const response = await axios.post(`/api/databases/${props.databaseId}/github/oauth/start`, {
      redirectUri
    })
    const state = response.data.state
    if (!state || !response.data.authorize_url) {
      throw new Error('Invalid OAuth response from server')
    }
    localStorage.setItem(
      `github_oauth_state:${state}`,
      JSON.stringify({ databaseId: props.databaseId, redirectUri })
    )
    window.location.assign(response.data.authorize_url)
  } catch (err: any) {
    oauthError.value = err.response?.data?.error || err.message || 'Failed to start GitHub OAuth'
  } finally {
    oauthStarting.value = false
  }
}

onMounted(async () => {
  const storedResult = localStorage.getItem(githubResultKey.value)
  if (storedResult) {
    try {
      const parsed = JSON.parse(storedResult)
      oauthMessage.value = parsed.success
        ? 'GitHub authorisation completed successfully.'
        : parsed.error || 'GitHub authorisation failed.'
    } catch {
      oauthMessage.value = 'GitHub authorisation completed.'
    }
    localStorage.removeItem(githubResultKey.value)
  }
  await fetchSettings()
  if (githubSettings.value.hasToken) {
    await fetchRepositories()
  }
})
</script>
