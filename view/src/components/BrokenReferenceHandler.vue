<template>
  <div>
    <!-- Try to render the content -->
    <slot v-if="!hasError" />

    <!-- Show error if content failed to load -->
    <div
      v-else
      class="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start justify-between gap-4"
    >
      <div class="flex items-start gap-2 flex-1">
        <AlertCircle class="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
        <div>
          <div class="font-medium text-red-900">
            {{ type === 'query' ? 'Query' : 'Chart' }} not found
          </div>
          <div class="text-sm text-red-700 mt-1">
            This {{ type }} may have been deleted or you don't have access to it.
          </div>
        </div>
      </div>
      <Button
        variant="ghost"
        size="sm"
        @click="$emit('remove')"
        class="text-red-600 hover:text-red-700"
      >
        Remove
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button'
import { AlertCircle } from 'lucide-vue-next'
import { onErrorCaptured, ref } from 'vue'

interface Props {
  type: 'query' | 'chart'
  referenceId: string
}

const props = defineProps<Props>()
defineEmits<{
  remove: []
}>()

const hasError = ref(false)

// Catch errors from child components (BaseEditorPreview or Chart)
onErrorCaptured((error) => {
  console.error(`Error rendering ${props.type}:`, error)
  hasError.value = true
  // Prevent error from propagating
  return false
})
</script>
