<template>
  <div class="min-h-screen bg-gray-100 py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header Section -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div class="flex items-center space-x-4">
          <!-- Avatar placeholder -->
          <div
            class="w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center"
          >
            <span class="text-2xl font-bold text-white">
              {{ (user.firstName?.[0] || '') + (user.lastName?.[0] || '') }}
            </span>
          </div>

          <!-- User info -->
          <div class="flex-1">
            <h1 class="text-3xl font-bold text-gray-900 mb-1">
              {{ user.firstName }} {{ user.lastName }}
            </h1>
            <p class="text-gray-600 flex items-center">
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"
                />
              </svg>
              {{ user.email }}
            </p>

            <!-- Admin badge -->
            <div class="mt-2" v-if="user.isAdmin">
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
              >
                <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Administrator
              </span>
            </div>
          </div>

          <!-- Logout button -->
          <button
            @click="logout"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-error-500 hover:bg-error-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-error-500 transition-colors duration-200 cursor-pointer"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
              />
            </svg>
            Logout
          </button>
        </div>
      </div>

      <!-- Profile Details Card -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <svg
            class="w-5 h-5 mr-2 text-gray-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
          Profile Information
        </h2>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- First Name -->
          <div class="space-y-2">
            <label class="text-sm font-medium text-gray-700">First Name</label>
            <div class="p-3 bg-gray-100 rounded-md border border-gray-200">
              <p class="text-gray-900">{{ user.firstName || 'Not provided' }}</p>
            </div>
          </div>

          <!-- Last Name -->
          <div class="space-y-2">
            <label class="text-sm font-medium text-gray-700">Last Name</label>
            <div class="p-3 bg-gray-100 rounded-md border border-gray-200">
              <p class="text-gray-900">{{ user.lastName || 'Not provided' }}</p>
            </div>
          </div>

          <!-- Email -->
          <div class="space-y-2 md:col-span-2">
            <label class="text-sm font-medium text-gray-700">Email Address</label>
            <div class="p-3 bg-gray-100 rounded-md border border-gray-200">
              <p class="text-gray-900">{{ user.email || 'Not provided' }}</p>
            </div>
          </div>

          <!-- Account Type -->
          <div class="space-y-2 md:col-span-2">
            <label class="text-sm font-medium text-gray-700">Account Type</label>
            <div class="p-3 bg-gray-100 rounded-md border border-gray-200">
              <div class="flex items-center">
                <span class="text-gray-900 mr-2">
                  {{ user.isAdmin ? 'Administrator' : 'Standard User' }}
                </span>
                <span
                  class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                  :class="
                    user.isAdmin
                      ? 'bg-primary-100 text-primary-800'
                      : 'bg-primary-100 text-primary-800'
                  "
                >
                  {{ user.isAdmin ? 'Admin' : 'User' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { fetchUser, logout, user } from '@/stores/auth'
import { onMounted } from 'vue'

onMounted(async () => {
  await fetchUser()
})
</script>
