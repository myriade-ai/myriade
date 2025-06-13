<template>
  <div class="bg-white border border-gray-200 rounded-lg p-6 shadow-sm w-full">
    <div class="flex items-start space-x-4">
      <!-- Icon -->
      <div class="flex-shrink-0">
        <div class="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
          <SparklesIcon class="w-5 h-5 text-primary-600" />
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <h3 class="text-sm font-medium text-gray-900 mb-1">AI Connection Required</h3>
        <p class="text-sm text-gray-600 mb-4">
          You need an active subscription to ask AI questions.
        </p>

        <!-- Action Buttons -->
        <div class="flex items-center space-x-3">
          <router-link
            to="/subscribe"
            class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-500 hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <SparklesIcon class="w-4 h-4 mr-2" />
            Set Up AI Connection
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { SparklesIcon } from '@heroicons/vue/24/outline'
</script>
