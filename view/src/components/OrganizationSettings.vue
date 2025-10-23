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
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from '@/plugins/axios'
import { user } from '@/stores/auth'
import { computed, onMounted, ref } from 'vue'

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

onMounted(async () => {
  await fetchOrganization()
})
</script>
