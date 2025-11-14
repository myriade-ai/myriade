<template>
  <div v-if="status">
    <div v-if="status === 'success'" class="bg-green-50 border border-green-200 rounded-md p-4">
      <div class="flex">
        <CheckCircleIcon class="h-5 w-5 text-green-400" aria-hidden="true" />
        <div class="ml-3">
          <h3 class="text-sm font-medium text-green-800">Connection Successful</h3>
          <div class="mt-2 text-sm text-green-700">
            <p>{{ message }}</p>
          </div>
        </div>
      </div>
    </div>

    <Alert v-else class="mt-2" variant="destructive">
      <CircleAlert class="h-5 w-5" />
      <AlertTitle> There is an error 😔</AlertTitle>
      <AlertDescription>
        <p>> {{ message }}</p>
        <hr />
        <p>
          The server was unable to establish a connection to your database.
          <b>Verify that your connection details are correct.</b>
          <br />
          If the connection details are correct, it's often due to firewall rules or network
          restrictions that prevent our server from accessing your database.
          <b
            >Please ensure that you have whitelisted the IP address of this server ({{ serverIp }})
            in your database</b
          >
        </p>
      </AlertDescription>
    </Alert>
  </div>
</template>

<script setup lang="ts">
import { useServerInfo } from '@/composables/useServerInfo'
import { CheckCircleIcon } from '@heroicons/vue/24/outline'
import { CircleAlert } from 'lucide-vue-next'
import { Alert, AlertDescription, AlertTitle } from '../ui/alert'

interface Props {
  status: 'success' | 'error' | null
  message: string
}

defineProps<Props>()

const { serverIp } = useServerInfo()
</script>
