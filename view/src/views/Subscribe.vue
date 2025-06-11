<template>
  <div class="min-h-screen bg-gray-50 pt-8">
    <!-- Pricing Section -->
    <div class="max-w-4xl mx-auto px-4 pb-8">
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div class="space-y-6">
          <div class="text-center">
            <h2 class="text-2xl font-bold text-gray-900 mb-2">Activate AI</h2>
            <p class="text-gray-600">
              Subscribe to get access to latest AI models and enjoy AI-powered database analytics.
            </p>
          </div>

          <!-- Professional Plan Card -->
          <div class="max-w-md mx-auto mt-8">
            <div
              class="bg-white border border-blue-500 rounded-lg p-6 shadow-lg ring-2 ring-blue-200 cursor-pointer hover:shadow-xl transition-shadow"
              @click="processPayment"
            >
              <div class="text-center">
                <h3 class="text-lg font-semibold text-gray-900 mb-2">Standard Plan</h3>
                <div class="mb-4">
                  <span class="text-3xl font-bold text-gray-900">$49</span>
                  <span class="text-gray-600">/month</span>
                </div>
                <ul class="text-sm text-gray-600 space-y-2 mb-6 text-left">
                  <li class="flex items-center">
                    <CheckIcon class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                    Unlimited guest users
                  </li>
                  <li class="flex items-center">
                    <CheckIcon class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                    Includes 300 AI requests
                  </li>
                  <li class="flex items-center">
                    <CheckIcon class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                    Unlimited databases
                  </li>
                  <li class="flex items-center">
                    <CheckIcon class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                    No commitment, cancel anytime
                  </li>
                </ul>
                <button
                  @click.stop="processPayment"
                  :disabled="isProcessingPayment"
                  class="w-full inline-flex justify-center items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span v-if="!isProcessingPayment">Subscribe Now</span>
                  <span v-else class="flex items-center">
                    <svg
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
                    Processing...
                  </span>
                </button>
              </div>
            </div>
          </div>

          <!-- FAQ Section -->
          <div class="mt-12">
            <h3 class="text-lg font-medium text-gray-900 mb-4">Frequently Asked Questions</h3>
            <div class="space-y-4">
              <div class="border-b border-gray-200 pb-4">
                <h4 class="font-medium text-gray-900">Can I cancel anytime?</h4>
                <p class="text-gray-600 mt-1">
                  Yes, you can cancel your subscription at any time. Your access will continue until
                  the end of your billing period.
                </p>
              </div>
              <div class="border-b border-gray-200 pb-4">
                <h4 class="font-medium text-gray-900">
                  What happens if I exceed my AI request limit?
                </h4>
                <p class="text-gray-600 mt-1">
                  You can purchase additional AI request bundles or upgrade to a higher plan with
                  more included requests.
                </p>
              </div>
              <div class="border-b border-gray-200 pb-4">
                <h4 class="font-medium text-gray-900">Is my data secure?</h4>
                <p class="text-gray-600 mt-1">
                  Yes, we use industry-standard encryption and security measures to protect your
                  data. We never store your database credentials permanently.
                </p>
              </div>
            </div>
          </div>

          <!-- Back to Setup Link -->
          <div class="text-center mt-8">
            <div class="space-x-4">
              <router-link
                to="/chat/new"
                class="text-gray-600 hover:text-gray-800 text-sm font-medium"
              >
                Continue without subscription
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from '@/plugins/axios'
import { CheckIcon } from '@heroicons/vue/24/outline'
import { ref } from 'vue'

// State
const isProcessingPayment = ref(false)

// Methods
const processPayment = async () => {
  isProcessingPayment.value = true

  try {
    const { data } = await axios.post('/api/create-checkout-session')
    window.location.href = data.url // Redirect to Stripe Checkout
  } catch (error) {
    console.error('Payment processing error:', error)
    alert('Payment processing failed. Please try again.')
  } finally {
    isProcessingPayment.value = false
  }
}
</script>
