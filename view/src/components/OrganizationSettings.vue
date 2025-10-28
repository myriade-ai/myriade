<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <h2 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
      <svg
        class="w-5 h-5 mr-2 text-gray-600 flex-shrink-0"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
        />
      </svg>
      Organization Settings
    </h2>

    <div v-if="loading" class="text-gray-600">Loading...</div>
    <div v-else-if="error" class="text-error-600">{{ error }}</div>
    <div v-else class="space-y-6">
      <!-- Organization Name -->
      <div class="space-y-2">
        <label class="text-sm font-medium text-gray-700">Organization Name</label>
        <div class="p-3 bg-gray-100 rounded-md border border-gray-200">
          <p class="text-gray-900">{{ organization.name || 'Not provided' }}</p>
        </div>
      </div>

      <!-- Language Setting -->
      <div class="space-y-2">
        <label class="text-sm font-medium text-gray-700">
          Organization Language
          <span v-if="!isAdmin" class="text-gray-500 text-xs ml-2">(Admin only)</span>
        </label>
        <p class="text-xs text-gray-500 mb-2">
          This language will be used by the AI for documentation, catalog entries, and quality
          reports.
        </p>

        <div v-if="isAdmin">
          <select
            v-model="selectedLanguage"
            @change="updateLanguage"
            class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            :disabled="updating"
          >
            <option value="">User's language (default)</option>
            <option value="English">English</option>
            <option value="French">French</option>
            <option value="Spanish">Spanish</option>
            <option value="German">German</option>
            <option value="Italian">Italian</option>
            <option value="Portuguese">Portuguese</option>
            <option value="Dutch">Dutch</option>
            <option value="Japanese">Japanese</option>
            <option value="Chinese">Chinese</option>
            <option value="Korean">Korean</option>
          </select>
          <p v-if="updateSuccess" class="mt-2 text-sm text-success-600">
            Language updated successfully
          </p>
          <p v-if="updateError" class="mt-2 text-sm text-error-600">{{ updateError }}</p>
        </div>
        <div v-else class="p-3 bg-gray-100 rounded-md border border-gray-200">
          <p class="text-gray-900">
            {{ organization.language || "User's language (default)" }}
          </p>
        </div>
      </div>

      <!-- GitHub Integration -->
      <div class="space-y-3 pt-4 border-t border-gray-100">
        <label class="text-sm font-medium text-gray-700">
          GitHub Integration
          <span v-if="!isAdmin" class="text-gray-500 text-xs ml-2">(Admin only)</span>
        </label>
        <p class="text-xs text-gray-500">
          Connect a GitHub repository so conversations use dedicated branches and pull requests for code changes.
        </p>

        <div v-if="githubLoading" class="text-sm text-gray-600">Loading GitHub settings...</div>
        <div v-else-if="githubError" class="text-sm text-error-600">{{ githubError }}</div>
        <div v-else class="space-y-4">
          <div class="p-3 bg-gray-50 border border-gray-200 rounded-md">
            <p class="text-sm text-gray-700">
              <span v-if="githubSettings.repoFullName">
                Repository:
                <span class="font-medium">{{ githubSettings.repoFullName }}</span>
              </span>
              <span v-else>No repository selected yet.</span>
            </p>
            <p v-if="githubSettings.defaultBranch" class="text-xs text-gray-500">
              Default branch: {{ githubSettings.defaultBranch }}
            </p>
            <p v-if="!githubSettings.hasToken" class="text-xs text-gray-500">
              GitHub token not configured.
            </p>
          </div>

          <div v-if="isAdmin" class="space-y-4">
            <div class="space-y-2">
              <label class="text-xs font-medium text-gray-600">Personal access token</label>
              <p class="text-xs text-gray-500">
                Provide a GitHub token with <span class="font-mono">repo</span> scope so Myriade can list repositories and push branches.
              </p>
              <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
                <Input
                  v-model="tokenInput"
                  :disabled="savingToken"
                  type="password"
                  placeholder="ghp_..."
                  class="sm:flex-1"
                />
                <Button @click="saveGithubToken" :disabled="savingToken">
                  {{ githubSettings.hasToken ? 'Update token' : 'Save token' }}
                </Button>
              </div>
              <p v-if="tokenSuccess" class="text-sm text-success-600">{{ tokenSuccess }}</p>
              <p v-if="tokenError" class="text-sm text-error-600">{{ tokenError }}</p>
            </div>

            <div class="space-y-2">
              <div class="flex items-center gap-2">
                <label class="text-xs font-medium text-gray-600 mb-0">Repository selection</label>
                <Button
                  variant="outline"
                  size="sm"
                  @click="fetchGithubRepos"
                  :disabled="loadingRepos || !githubSettings.hasToken"
                >
                  {{ loadingRepos ? 'Loading…' : 'Refresh list' }}
                </Button>
              </div>
              <p v-if="!githubSettings.hasToken" class="text-xs text-gray-500">
                Save a token to enable repository selection.
              </p>
              <p v-if="repoError" class="text-sm text-error-600">{{ repoError }}</p>

              <div v-if="githubSettings.hasToken" class="space-y-2">
                <select
                  v-model="selectedRepoFullName"
                  class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="" disabled>Select a repository</option>
                  <option
                    v-for="repo in repositories"
                    :key="repo.full_name"
                    :value="repo.full_name"
                  >
                    {{ repo.full_name }} (default: {{ repo.default_branch || 'main' }})
                  </option>
                </select>

                <div v-if="selectedRepoFullName" class="space-y-2">
                  <label class="text-xs font-medium text-gray-600">Default branch</label>
                  <Input v-model="selectedDefaultBranch" placeholder="main" />
                  <div class="flex items-center gap-2">
                    <Button size="sm" @click="applySelectedRepo" :disabled="selectingRepo">
                      Save repository
                    </Button>
                    <span v-if="repoSuccess" class="text-sm text-success-600">{{ repoSuccess }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import axios from '@/plugins/axios'
import { user } from '@/stores/auth'
import { computed, onMounted, ref, watch } from 'vue'

const organization = ref<{ name: string; language: string | null }>({
  name: '',
  language: null
})
const loading = ref(true)
const error = ref<string | null>(null)
const updating = ref(false)
const updateSuccess = ref(false)
const updateError = ref<string | null>(null)

const selectedLanguage = ref<string>('')

const isAdmin = computed(() => user.value.isAdmin)

const githubSettings = ref<{
  connected: boolean
  hasToken: boolean
  repoOwner: string | null
  repoName: string | null
  repoFullName: string | null
  defaultBranch: string | null
}>({
  connected: false,
  hasToken: false,
  repoOwner: null,
  repoName: null,
  repoFullName: null,
  defaultBranch: null
})
const githubLoading = ref(false)
const githubError = ref<string | null>(null)

const tokenInput = ref('')
const savingToken = ref(false)
const tokenSuccess = ref<string | null>(null)
const tokenError = ref<string | null>(null)

const repositories = ref<Array<{ full_name: string; default_branch: string }>>([])
const loadingRepos = ref(false)
const repoError = ref<string | null>(null)
const repoSuccess = ref<string | null>(null)
const selectingRepo = ref(false)
const selectedRepoFullName = ref<string | null>(null)
const selectedDefaultBranch = ref('main')

watch(selectedRepoFullName, (fullName) => {
  if (!fullName) {
    return
  }
  const repo = repositories.value.find((item) => item.full_name === fullName)
  if (repo?.default_branch) {
    selectedDefaultBranch.value = repo.default_branch
  }
})

const fetchOrganization = async () => {
  try {
    loading.value = true
    error.value = null
    const response = await axios.get('/api/organisation')
    organization.value = response.data
    selectedLanguage.value = organization.value.language || ''
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to load organization settings'
    console.error('Failed to fetch organization:', err)
  } finally {
    loading.value = false
  }
}

const fetchGithubSettings = async () => {
  if (!isAdmin.value) return
  try {
    githubLoading.value = true
    githubError.value = null
    const response = await axios.get('/api/github/settings')
    githubSettings.value = {
      connected: response.data.connected ?? false,
      hasToken: response.data.hasToken ?? false,
      repoOwner: response.data.repoOwner ?? null,
      repoName: response.data.repoName ?? null,
      repoFullName: response.data.repoFullName ?? null,
      defaultBranch: response.data.defaultBranch ?? null
    }
    selectedRepoFullName.value = response.data.repoFullName || null
    selectedDefaultBranch.value = response.data.defaultBranch || 'main'
  } catch (err: any) {
    githubError.value = err.response?.data?.error || 'Failed to load GitHub settings'
    console.error('Failed to fetch GitHub settings:', err)
  } finally {
    githubLoading.value = false
  }
}

const updateLanguage = async () => {
  try {
    updating.value = true
    updateSuccess.value = false
    updateError.value = null

    await axios.patch('/api/organisation', {
      language: selectedLanguage.value || null
    })

    organization.value.language = selectedLanguage.value || null
    updateSuccess.value = true

    // Clear success message after 3 seconds
    setTimeout(() => {
      updateSuccess.value = false
    }, 3000)
  } catch (err: any) {
    updateError.value = err.response?.data?.error || 'Failed to update language'
    console.error('Failed to update language:', err)
  } finally {
    updating.value = false
  }
}

const saveGithubToken = async () => {
  try {
    savingToken.value = true
    tokenSuccess.value = null
    tokenError.value = null

    await axios.put('/api/github/settings', {
      access_token: tokenInput.value.trim() || null
    })

    githubSettings.value.hasToken = tokenInput.value.trim().length > 0
    await fetchGithubSettings()
    tokenSuccess.value = tokenInput.value.trim().length
      ? 'GitHub token saved successfully'
      : 'GitHub token removed'
    tokenInput.value = ''
    setTimeout(() => {
      tokenSuccess.value = null
    }, 3000)
  } catch (err: any) {
    tokenError.value = err.response?.data?.error || 'Failed to save GitHub token'
    console.error('Failed to save GitHub token:', err)
  } finally {
    savingToken.value = false
  }
}

const fetchGithubRepos = async () => {
  if (!githubSettings.value.hasToken) {
    repoError.value = 'Add a GitHub token before listing repositories'
    return
  }
  try {
    loadingRepos.value = true
    repoError.value = null
    const response = await axios.get('/api/github/repos')
    repositories.value = response.data.repositories || []
    if (!repositories.value.length) {
      repoError.value = 'No repositories found for this token'
    }
  } catch (err: any) {
    repoError.value = err.response?.data?.error || 'Failed to load repositories'
    console.error('Failed to fetch repositories:', err)
  } finally {
    loadingRepos.value = false
  }
}

const applySelectedRepo = async () => {
  if (!selectedRepoFullName.value) {
    repoError.value = 'Select a repository to continue'
    return
  }
  const [owner, name] = selectedRepoFullName.value.split('/')
  try {
    selectingRepo.value = true
    repoError.value = null
    repoSuccess.value = null

    await axios.put('/api/github/settings', {
      repo_owner: owner,
      repo_name: name,
      default_branch: selectedDefaultBranch.value || null
    })

    githubSettings.value.repoOwner = owner
    githubSettings.value.repoName = name
    githubSettings.value.repoFullName = selectedRepoFullName.value
    githubSettings.value.defaultBranch = selectedDefaultBranch.value || null
    githubSettings.value.connected = true
    await fetchGithubSettings()
    repoSuccess.value = 'Repository saved successfully'
    setTimeout(() => {
      repoSuccess.value = null
    }, 3000)
  } catch (err: any) {
    repoError.value = err.response?.data?.error || 'Failed to save repository'
    console.error('Failed to save GitHub repository:', err)
  } finally {
    selectingRepo.value = false
  }
}

onMounted(async () => {
  await fetchOrganization()
  if (isAdmin.value) {
    await fetchGithubSettings()
  }
})
</script>
