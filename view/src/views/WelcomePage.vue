<template>
  <div class="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50">
    <div class="flex flex-col items-center justify-center min-h-screen px-4 py-12">
      <div class="max-w-4xl w-full space-y-8 text-center">
        <!-- Logo/Brand -->
        <div>
          <h1 class="text-4xl font-bold text-gray-900 mb-2">Welcome to Myriade</h1>
          <p class="text-lg text-gray-600">Choose a playground dataset to explore</p>
        </div>

        <!-- Dataset Selection -->
        <div class="space-y-4">
          <div v-if="isLoadingDatasets" class="text-center py-8">
            <svg
              class="animate-spin h-8 w-8 text-indigo-600 mx-auto"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <p class="text-sm text-gray-600 mt-2">Loading datasets...</p>
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div
              v-for="dataset in publicDatasets"
              :key="dataset.id"
              @click="selectDataset(dataset)"
              :class="[
                'bg-white/50 backdrop-blur-sm rounded-lg p-4 border-2 cursor-pointer transition-all duration-200 hover:bg-white/70 hover:shadow-md',
                selectedDataset?.id === dataset.id
                  ? 'border-indigo-500 bg-indigo-50/50'
                  : 'border-gray-200 hover:border-gray-300'
              ]"
            >
              <div class="text-center">
                <div class="w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <img
                    :src="getDatabaseIcon(dataset.engine)"
                    alt="Database icon"
                    class="w-12 h-12"
                  />
                </div>
                <h3 class="text-lg font-semibold text-gray-900 mb-1">{{ dataset.name }}</h3>
                <p class="text-sm text-gray-600 mb-2">
                  {{ dataset.description || 'Playground dataset' }}
                </p>
              </div>
            </div>
          </div>

          <div v-if="!isLoadingDatasets && publicDatasets.length === 0" class="text-center py-8">
            <p class="text-sm text-gray-600">No public datasets available</p>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex justify-center">
          <div class="max-w-md w-full space-y-4">
            <!-- Start Exploring Button -->
            <button
              @click="handleAnonymousLogin"
              :disabled="isLoading || !selectedDataset"
              class="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              <svg
                v-if="isLoading"
                class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                ></circle>
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              {{
                isLoading
                  ? 'Starting...'
                  : selectedDataset
                    ? `Explore ${selectedDataset.name}`
                    : 'Select a dataset first'
              }}
            </button>
            <p class="text-xs text-gray-500">No account required • Free playground mode</p>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="bg-red-50 border border-red-200 rounded-md p-3">
          <p class="text-sm text-red-800">{{ errorMessage }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useContextsStore } from '@/stores/contexts'
import axios from 'axios'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

interface Dataset {
  id: string
  name: string
  description?: string
  engine: string
  public: boolean
}

const router = useRouter()
const contextsStore = useContextsStore()

const isLoading = ref(false)
const isLoadingDatasets = ref(true)
const errorMessage = ref('')
const selectedDataset = ref<Dataset | null>(null)
const publicDatasets = ref<Dataset[]>([])

const selectDataset = (dataset: Dataset) => {
  selectedDataset.value = dataset
  errorMessage.value = ''
}

const fetchPublicDatasets = async () => {
  isLoadingDatasets.value = true
  const response = await axios.get('/api/databases')
  isLoadingDatasets.value = false
  const datasets = response.data.filter((db: Dataset) => db.public)

  publicDatasets.value = datasets.slice(0, 3) // Limit to 3 datasets
}

const handleAnonymousLogin = async () => {
  if (!selectedDataset.value) {
    errorMessage.value = 'Please select a dataset first.'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    // Set the selected dataset as the context
    const contextId = `database-${selectedDataset.value.id}`
    contextsStore.setSelectedContext(contextId)

    // Navigate to the main app
    router.push('/')
  } catch (error) {
    console.error('Failed to set context:', error)
    errorMessage.value = 'Failed to start session. Please try again.'
  } finally {
    isLoading.value = false
  }
}

const getDatabaseIcon = (dbType: string): string => {
  const type = dbType.toLowerCase()

  if (type.includes('postgres') || type.includes('postgresql')) {
    return '/datasources/postgres.svg'
  } else if (type.includes('bigquery')) {
    return '/datasources/bigquery.svg'
  } else if (type.includes('snowflake')) {
    return '/datasources/snowflake.svg'
  }

  // Default database icon - we'll use a generic database icon
  // You can create a default.svg file or use one of the existing ones
  return '/datasources/postgres.svg' // Using postgres as default for now
}

onMounted(() => {
  fetchPublicDatasets()
})
</script>
