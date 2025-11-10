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
        <p v-if="!githubSettings.isGithubOAuthConfigured" class="text-xs text-amber-600 bg-amber-50 p-2 rounded border border-amber-200">
          GitHub integration is not configured on this server. Please contact your administrator to set up the required GitHub OAuth credentials (GITHUB_OAUTH_CLIENT_ID and GITHUB_OAUTH_CLIENT_SECRET).
        </p>
        <p v-else class="text-xs text-gray-500">
          Authorise Myriade with GitHub to list repositories and push branches for this datasource.
          You will be redirected to GitHub and then returned to this page.
        </p>
        <Button 
          type="button" 
          @click="startOAuth" 
          :is-loading="oauthStarting"
          :disabled="!githubSettings.isGithubOAuthConfigured"
        >
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
              type="button"
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
            type="button"
            size="sm"
            @click="saveRepository"
            :disabled="!selectedRepoFullName"
            :is-loading="savingRepo"
          >
            <template #loading>Saving…</template>
            Save repository
          </Button>
          <Button
            type="button"
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

      <!-- DBT Documentation Sync Section -->
      <div v-if="githubSettings.repoFullName" class="mt-6 pt-6 border-t border-gray-200">
        <h4 class="text-sm font-medium text-gray-900 mb-2">DBT Documentation</h4>
        <p class="text-xs text-gray-500 mb-3">
          DBT documentation is automatically synced every hour. You can also manually trigger a
          sync.
        </p>

        <div class="space-y-2">
          <div v-if="dbtSyncStatus" class="text-xs text-gray-600">
            <span class="font-medium">Status:</span>
            <span
              :class="{
                'text-blue-600': dbtSyncStatus.status === 'generating',
                'text-green-600': dbtSyncStatus.status === 'completed',
                'text-error-600': dbtSyncStatus.status === 'failed',
                'text-gray-600': dbtSyncStatus.status === 'idle'
              }"
            >
              {{ dbtSyncStatus.status === 'generating' ? 'Syncing...' : dbtSyncStatus.status }}
            </span>
          </div>

          <div v-if="dbtSyncStatus?.last_synced_at" class="text-xs text-gray-600">
            <span class="font-medium">Last synced:</span>
            {{ formatDate(dbtSyncStatus.last_synced_at) }}
          </div>

          <div v-if="dbtSyncStatus?.commit_hash" class="text-xs text-gray-600 font-mono">
            <span class="font-medium font-sans">Commit:</span>
            {{ dbtSyncStatus.commit_hash.substring(0, 8) }}
          </div>

          <div v-if="dbtSyncStatus?.error" class="text-xs text-error-600">
            {{ dbtSyncStatus.error }}
          </div>

          <Button
            type="button"
            size="sm"
            variant="outline"
            @click="syncDbtDocs"
            :disabled="syncingDbt || dbtSyncStatus?.status === 'generating'"
          >
            <template #loading>Syncing...</template>
            {{ syncingDbt ? 'Syncing...' : 'Sync DBT Docs' }}
          </Button>

          <p v-if="dbtSyncError" class="text-sm text-error-600">{{ dbtSyncError }}</p>
          <p v-if="dbtSyncSuccess" class="text-sm text-success-600">{{ dbtSyncSuccess }}</p>
        </div>
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
  isGithubOAuthConfigured: boolean
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
  tokenExpiresAt: null,
  isGithubOAuthConfigured: true
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

// DBT sync state
const dbtSyncStatus = ref<{
  status: string
  last_synced_at: string | null
  generation_started_at: string | null
  commit_hash: string | null
  error: string | null
} | null>(null)
const syncingDbt = ref(false)
const dbtSyncError = ref<string | null>(null)
const dbtSyncSuccess = ref<string | null>(null)

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
      tokenExpiresAt: response.data.tokenExpiresAt ?? null,
      isGithubOAuthConfigured: response.data.isGithubOAuthConfigured ?? true
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

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

const fetchDbtSyncStatus = async () => {
  try {
    const response = await axios.get(`/api/databases/${props.databaseId}/github/dbt-sync-status`)
    dbtSyncStatus.value = response.data
  } catch (err: any) {
    console.error('Failed to fetch DBT sync status:', err)
  }
}

const syncDbtDocs = async () => {
  dbtSyncError.value = null
  dbtSyncSuccess.value = null
  try {
    syncingDbt.value = true
    await axios.post(`/api/databases/${props.databaseId}/github/sync-dbt-docs`)
    dbtSyncSuccess.value = 'DBT documentation sync started in background'
    // Refresh status after a short delay
    setTimeout(fetchDbtSyncStatus, 2000)
  } catch (err: any) {
    dbtSyncError.value = err.response?.data?.error || 'Failed to sync DBT documentation'
  } finally {
    syncingDbt.value = false
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
    await fetchDbtSyncStatus()
  }
})
</script>
