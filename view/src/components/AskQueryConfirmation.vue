<template>
  <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 my-3">
    <div class="flex items-start">
      <ExclamationTriangleIcon
        v-if="status === 'pending_confirmation'"
        class="w-5 h-5 text-yellow-400 mr-3 mt-0.5 flex-shrink-0"
      />
      <ClockIcon
        v-else-if="status === 'running'"
        class="w-5 h-5 text-blue-400 mr-3 mt-0.5 flex-shrink-0 animate-spin"
      />

      <div class="flex-1">
        <!-- Pending Confirmation State -->
        <template v-if="status === 'pending_confirmation' || !status">
          <h4 class="text-sm font-medium text-yellow-800 mb-2">
            {{ operationType }} Operation Confirmation Required
          </h4>
          <p class="text-sm text-yellow-700 mb-3">
            This query will modify your database. Please review it carefully before proceeding.
          </p>

          <div class="flex gap-2 mt-3">
            <Button
              variant="default"
              @click="handleConfirm"
              :disabled="isProcessing"
              :is-loading="isProcessing"
            >
              <template #loading>Executing...</template>
              Confirm & Execute
            </Button>
            <Button variant="outline" @click="handleReject()" :disabled="isProcessing">
              Reject
            </Button>
          </div>
        </template>

        <!-- Running State -->
        <template v-else-if="status === 'running'">
          <h4 class="text-sm font-medium text-blue-800 mb-2">
            Query is Running...
          </h4>
          <p class="text-sm text-blue-700 mb-3">
            Your query is currently executing. You can cancel it if needed.
          </p>

          <div class="flex gap-2 mt-3">
            <Button
              variant="destructive"
              @click="handleCancel"
              :disabled="isProcessing"
              :is-loading="isProcessing"
            >
              <template #loading>Cancelling...</template>
              Cancel Query
            </Button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Button from '@/components/ui/button/Button.vue'
import { socket } from '@/plugins/socket'
import { useQueriesStore } from '@/stores/queries'
import type { QueryData } from '@/stores/queries'
import { ClockIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

interface Props extends Omit<QueryData, 'id'> {
  queryId: string
}
const route = useRoute()
const conversationId = computed(() =>
  route.params.id === 'new' ? null : (route.params.id as string)
)
const props = defineProps<Props>()

const queriesStore = useQueriesStore()
const isProcessing = ref(false)

const handleConfirm = async () => {
  try {
    isProcessing.value = true
    socket.emit('confirmWriteOperation', conversationId.value, props.queryId)
  } catch (err: any) {
    console.error('Failed to confirm operation:', err)
  } finally {
    isProcessing.value = false
  }
}

const handleReject = async () => {
  try {
    socket.emit('rejectWriteOperation', conversationId.value, props.queryId)
  } catch (err: any) {
    console.error('Failed to reject operation:', err)
  }
}

const handleCancel = async () => {
  try {
    isProcessing.value = true
    // Use WebSocket for real-time cancellation
    queriesStore.cancelQueryViaSocket(props.queryId)
  } catch (err: any) {
    console.error('Failed to cancel query:', err)
  } finally {
    isProcessing.value = false
  }
}
</script>
