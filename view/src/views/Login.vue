<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <div class="mx-auto h-12 w-auto flex justify-center">
          <img src="/logo.svg?v=3" class="h-12 w-auto" alt="Myriade" />
        </div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Authentication Required
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Please sign in to continue using Myriade
        </p>
      </div>
      <div>
        <button
          @click="handleSignIn"
          :disabled="isSigningIn"
          class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="isSigningIn" class="absolute left-0 inset-y-0 flex items-center pl-3">
            <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </span>
          {{ isSigningIn ? 'Signing in...' : 'Sign in to Myriade' }}
        </button>
        
        <div v-if="error" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="ml-3">
              <p class="text-sm text-red-700">
                {{ error }}
              </p>
              <button
                @click="handleSignIn"
                class="mt-2 text-sm text-primary-600 underline hover:text-primary-800"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import axios from '@/plugins/axios'

const isSigningIn = ref(false)
const error = ref('')

const handleSignIn = async () => {
  isSigningIn.value = true
  error.value = ''
  
  try {
    // Get the login URL from the server
    const response = await axios.get('/api/auth')
    const { authorization_url } = response.data
    
    if (authorization_url) {
      // Redirect to the auth provider
      window.location.href = authorization_url
    } else {
      throw new Error('No authorization URL received from server')
    }
  } catch (err: any) {
    console.error('Sign-in failed:', err)
    
    // Show user-friendly error message
    if (err.response?.status === 500) {
      error.value = 'Authentication service is temporarily unavailable. Please try again in a few moments.'
    } else if (err.response?.data?.error) {
      error.value = err.response.data.error
    } else {
      error.value = 'Unable to connect to authentication service. Please check your internet connection and try again.'
    }
    
    isSigningIn.value = false
  }
}
</script>