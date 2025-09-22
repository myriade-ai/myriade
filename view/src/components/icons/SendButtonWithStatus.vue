<template>
  <div class="h-6 w-6">
    <RefreshCcw v-if="status === 'running'" class="h-6 w-6 animate-spin" />
    <X v-else-if="status === 'error'" class="h-6 w-6 text-error-500" />
    <button v-else @click="onClick">
      <ArrowUp class="h-6 w-6 text-white" />
    </button>
  </div>
</template>

<script setup>
import { ArrowUp, RefreshCcw, X } from 'lucide-vue-next'

defineProps({
  status: {
    type: String,
    default: 'clear',
    validator: (value) => ['running', 'error', 'clear'].includes(value)
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
