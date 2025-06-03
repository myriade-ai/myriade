<template>
  <div class="bg-white border border-gray-200 rounded-lg p-6 shadow-sm w-full">
    <div class="flex items-start space-x-4">
      <!-- Icon -->
      <div class="flex-shrink-0">
        <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
          <SparklesIcon class="w-5 h-5 text-blue-600" />
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
<<<<<<< HEAD
=======
            @click="clearSubscriptionRequired"
>>>>>>> c54ca84 (base for test)
            class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <SparklesIcon class="w-4 h-4 mr-2" />
            Set Up AI Connection
          </router-link>
<<<<<<< HEAD
        </div>
      </div>
=======

          <button @click="$emit('dismiss')" class="text-sm text-gray-500 hover:text-gray-700">
            Dismiss
          </button>
        </div>
      </div>

      <!-- Close button -->
      <div class="flex-shrink-0">
        <button
          @click="$emit('dismiss')"
          class="bg-white rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <span class="sr-only">Close</span>
          <XMarkIcon class="h-5 w-5" />
        </button>
      </div>
>>>>>>> c54ca84 (base for test)
    </div>
  </div>
</template>

<script setup lang="ts">
<<<<<<< HEAD
import { SparklesIcon } from '@heroicons/vue/24/outline'
=======
import { useConversationsStore } from '@/stores/conversations'
import { SparklesIcon, XMarkIcon } from '@heroicons/vue/24/outline'

const { clearSubscriptionRequired } = useConversationsStore()

defineEmits<{
  dismiss: []
}>()
>>>>>>> c54ca84 (base for test)
</script>
