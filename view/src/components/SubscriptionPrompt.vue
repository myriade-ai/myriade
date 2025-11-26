<template>
  <div class="bg-card border border-border rounded-lg p-6 shadow-sm w-full">
    <div class="flex items-start space-x-4">
      <!-- Icon -->
      <div class="flex-shrink-0">
        <div class="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
          <SparklesIcon class="w-5 h-5 text-primary-600" />
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <h3 class="text-sm font-medium text-foreground mb-1">AI Connection Required</h3>
        <p class="text-sm text-muted-foreground mb-4">
          You need an active subscription to ask AI questions.
        </p>

        <!-- Action Buttons -->
        <div class="flex items-center space-x-3">
          <button
            @click="processPayment"
            class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-500 hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <SparklesIcon class="w-4 h-4 mr-2" />
            Set Up AI Connection
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from '@/plugins/axios'
import { SparklesIcon } from '@heroicons/vue/24/outline'
import { ref } from 'vue'

// State
const isProcessingPayment = ref(false)

// Methods
const processPayment = async () => {
  isProcessingPayment.value = true

  try {
    const { data } = await axios.post('/api/billing/create-checkout-session')
    window.location.href = data.url // Redirect to Stripe Checkout
  } catch (error) {
    console.error('Payment processing error:', error)
    alert('Payment processing failed. Please try again.')
  } finally {
    isProcessingPayment.value = false
  }
}
</script>
