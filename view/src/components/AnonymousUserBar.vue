<template>
  <div
    ref="barElement"
    v-if="shouldShow"
    class="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/30 border-b border-amber-200 dark:border-amber-800 px-4 py-2 sm:py-3"
  >
    <div class="mx-auto">
      <!-- Desktop Layout -->
      <div class="hidden sm:flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <!-- Message -->
          <div class="flex-1">
            <div class="flex items-center space-x-2">
              <span class="text-sm font-medium text-amber-800 dark:text-amber-200">
                🧪 You are in sandbox mode
              </span>
              <span class="text-sm text-amber-700 dark:text-amber-300">
                • Limited to {{ user.credits }} free credits
              </span>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex items-center">
          <!-- Sign Up Button -->
          <button
            @click="handleSignUp"
            class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-amber-600 hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 transition-colors duration-200"
          >
            <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path
                fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.293l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z"
                clip-rule="evenodd"
              />
            </svg>
            Sign up for free credits
          </button>
        </div>
      </div>

      <!-- Mobile Layout -->
      <div class="sm:hidden flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="text-sm font-medium text-amber-800 dark:text-amber-200">
            🧪 Sandbox mode
          </span>
          <span
            class="text-xs font-medium text-amber-700 dark:text-amber-300 bg-amber-100 dark:bg-amber-800/50 px-2 py-0.5 rounded-full"
          >
            {{ user.credits }} credits
          </span>
        </div>

        <!-- Sign Up Button -->
        <button
          @click="handleSignUp"
          class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-amber-600 hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 transition-colors duration-200"
        >
          <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.293l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z"
              clip-rule="evenodd"
            />
          </svg>
          Sign up free
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { isAnonymous, redirectToSignUp, user } from '@/stores/auth'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const barElement = ref<HTMLElement>()

const handleSignUp = async () => {
  try {
    await redirectToSignUp()
  } catch (error) {
    console.error('Failed to redirect to sign up:', error)
  }
}

// Show if anonymous (no dismiss functionality)
const shouldShow = computed(() => isAnonymous.value)

// Update CSS variable when visibility changes
const updateHeightVariable = async () => {
  if (shouldShow.value && barElement.value) {
    await nextTick() // Ensure DOM is updated
    const height = barElement.value.getBoundingClientRect().height
    document.documentElement.style.setProperty('--anonymous-bar-height', `${height}px`)
  } else {
    document.documentElement.style.setProperty('--anonymous-bar-height', '0px')
  }
}

onMounted(() => {
  updateHeightVariable()
  // Handle window resize for responsive changes
  window.addEventListener('resize', updateHeightVariable)
})

onUnmounted(() => {
  document.documentElement.style.setProperty('--anonymous-bar-height', '0px')
  window.removeEventListener('resize', updateHeightVariable)
})

watch(shouldShow, () => {
  updateHeightVariable()
})
</script>
