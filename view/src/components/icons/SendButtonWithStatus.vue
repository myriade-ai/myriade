<template>
  <button
    :class="
      cn('inline-flex items-center justify-center rounded-full p-2', {
        'bg-gray-300 cursor-not-allowed': disabled,
        'bg-black hover:bg-gray-800 cursor-pointer': !disabled
      })
    "
    @click="onClick"
    :disabled="disabled"
  >
    <div class="h-6 w-6">
      <RefreshCw v-if="status === 'running'" class="h-6 w-6 animate-spin text-white" />
      <X v-else-if="status === 'error'" class="h-6 w-6 text-error-200" />
      <ArrowUp v-else class="h-6 w-6 text-white" />
    </div>
  </button>
</template>

<script setup>
import { cn } from '@/lib/utils'
import { ArrowUp, RefreshCw, X } from 'lucide-vue-next'

defineProps({
  status: {
    type: String,
    default: 'clear',
    validator: (value) => ['running', 'error', 'clear'].includes(value)
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['clicked'])

const onClick = () => {
  emit('clicked')
}
</script>

<style scoped>
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
