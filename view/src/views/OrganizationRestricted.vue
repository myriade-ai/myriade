<script setup lang="ts">
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import Button from '@/components/ui/button/Button.vue'
import { logout } from '@/stores/auth'
import { AlertTriangle, LogOut } from 'lucide-vue-next'
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Organization Access Required
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          This deployment is restricted to specific organizations
        </p>
      </div>

      <Alert variant="destructive">
        <AlertTriangle class="h-5 w-5" />
        <AlertTitle>Access Denied</AlertTitle>
        <AlertDescription>
          This deployment is locked to a specific organisation. Please contact your administrator to
          be added to the organisation or use the correct organisation account.
        </AlertDescription>
      </Alert>

      <div class="flex justify-center">
        <Button @click="logout" variant="destructive" class="gap-2">
          Sign out
          <LogOut class="h-4 w-4" />
        </Button>
      </div>
    </div>
  </div>
</template>
