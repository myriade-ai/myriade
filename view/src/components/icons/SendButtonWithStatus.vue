<template>
  <div class="h-6 w-6 absolute right-2 top-1/2 transform -translate-y-1/2">
    <ArrowPathIcon v-if="status === 'running'" class="h-5 w-5 animate-spin" />
    <XMarkIcon v-else-if="status === 'error'" class="h-5 w-5 text-error-500" />
    <button v-else @click="onClick">
      <PaperAirplaneIcon class="h-5 w-5" />
    </button>
  </div>
</template>

<script setup>
import { ArrowPathIcon, PaperAirplaneIcon, XMarkIcon } from '@heroicons/vue/24/solid'

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
