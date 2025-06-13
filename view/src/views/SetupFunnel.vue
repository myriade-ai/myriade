<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="max-w-4xl mx-auto px-4 py-8 relative">
      <!-- Close button - only shown when there are existing databases -->
      <button
        v-if="hasExistingDatabases"
        @click="closeFunnel"
        class="absolute top-8 right-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors duration-200"
        aria-label="Close setup"
      >
        <XMarkIcon class="w-6 h-6" />
      </button>

      <div class="text-center">
        <h1 class="text-3xl font-bold text-gray-900 mb-4">Database Setup</h1>
        <p class="text-lg text-gray-600">
          Connect your database to start using Myriade's AI-powered analytics.
        </p>
      </div>
    </div>

    <!-- Progress Steps -->
    <div class="pt-8 pb-6">
      <div class="max-w-4xl mx-auto px-4">
        <nav aria-label="Setup progress">
          <ol class="flex items-center justify-center space-x-8">
            <li
              v-for="(step, index) in steps"
              :key="index"
              class="flex items-center"
              :class="getStepClasses(index)"
            >
              <div class="flex items-center">
                <div
                  class="flex items-center justify-center w-8 h-8 rounded-full border-2"
                  :class="getStepIconClasses(index)"
                >
                  <CheckIcon
                    v-if="index < currentStep"
                    class="w-5 h-5 text-white"
                    aria-hidden="true"
                  />
                  <span
                    v-else
                    class="text-sm font-medium"
                    :class="index === currentStep ? 'text-white' : 'text-gray-500'"
                  >
                    {{ index + 1 }}
                  </span>
                </div>
                <span
                  class="ml-3 text-sm font-medium"
                  :class="index <= currentStep ? 'text-gray-900' : 'text-gray-500'"
                >
                  {{ step.title }}
                </span>
              </div>
              <div
                v-if="index < steps.length - 1"
                class="ml-8 w-16 h-0.5"
                :class="index < currentStep ? 'bg-primary-600' : 'bg-gray-300'"
              ></div>
            </li>
          </ol>
        </nav>
      </div>
    </div>

    <!-- Setup Form -->
    <div class="max-w-4xl mx-auto px-4 pb-8">
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <DatabaseSetupForm
          ref="setupFormRef"
          save-button-text="Complete Setup"
          @database-saved="onDatabaseSaved"
          @save-error="onSaveError"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import DatabaseSetupForm from '@/components/database/DatabaseSetupForm.vue'
import router from '@/router'
import { useDatabasesStore } from '@/stores/databases'
import { CheckIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import { computed, onMounted, ref } from 'vue'

// Steps configuration
const steps = [
  { title: 'Database Type', completed: false },
  { title: 'Connection Details', completed: false }
]

const setupFormRef = ref<InstanceType<typeof DatabaseSetupForm> | null>(null)
const databasesStore = useDatabasesStore()

// Load databases on mount to check if there are existing ones
onMounted(async () => {
  await databasesStore.fetchDatabases({ refresh: true })
})

// Check if there are existing databases
const hasExistingDatabases = computed(() => {
  return databasesStore.databases.length > 0
})

// Watch the form's currentStep to update our local state
const currentStep = computed(() => {
  return setupFormRef.value?.currentStep || 0
})

// Methods for step styling
const getStepClasses = (index: number) => {
  if (index < currentStep.value) return 'text-primary-600'
  if (index === currentStep.value) return 'text-primary-600'
  return 'text-gray-500'
}

const getStepIconClasses = (index: number) => {
  if (index < currentStep.value) return 'bg-primary-600 border-primary-600'
  if (index === currentStep.value) return 'bg-primary-600 border-primary-600'
  return 'bg-white border-gray-300'
}

const closeFunnel = () => {
  router.push({ name: 'DatabaseList' })
}

const onDatabaseSaved = () => {
  router.push('/')
}

const onSaveError = (error: any) => {
  console.error('Database save error:', error)
}
</script>
