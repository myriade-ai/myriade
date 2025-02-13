<template>
  <base-input
    :type="inputType"
    :model-value="props.modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    v-bind="$attrs"
  >
    <button
      type="button"
      class="eye-button"
      @click="togglePassword"
      :aria-label="showPassword ? 'Hide password' : 'Show password'"
    >
      <EyeIcon v-if="!showPassword" class="h-5 w-5 text-gray-400" />
      <EyeSlashIcon v-else class="h-5 w-5 text-gray-400" />
    </button>
  </base-input>
</template>

<script setup lang="ts">
import BaseInput from './BaseInput.vue'
import { EyeIcon, EyeSlashIcon } from '@heroicons/vue/24/outline'
import { ref, computed } from 'vue'

const showPassword = ref(false)

const emit = defineEmits(['update:modelValue'])

const props = defineProps<{
  modelValue: string,
  type?: string
}>()

const inputType = computed(() => {
  if (props.type) return props.type
  return showPassword.value ? 'text' : 'password'
})

const togglePassword = () => {
  showPassword.value = !showPassword.value
} 

</script>

<style scoped>
.eye-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: #666;
  display: flex;
  align-items: center;
  margin-right: -8px;
  z-index: 1000;
}

.eye-button:hover {
  color: #333;
}

:deep(input) {
  padding-right: 40px !important;
}
</style> 