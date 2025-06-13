<template>
  <div
    class="min-h-screen flex items-center justify-center bg-background py-12 px-4 sm:px-6 lg:px-8"
  >
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-primary-800">
          Sign in to your account
        </h2>
      </div>
      <div class="mt-8 space-y-6">
        <button
          @click="handleLogin"
          class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-500 hover:bg-primary-600 focus:outline-hidden focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          Sign in with WorkOS
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { login } from '@/stores/auth'

const handleLogin = async () => {
  await login()
}
</script>
