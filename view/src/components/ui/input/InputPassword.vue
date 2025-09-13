<script setup lang="ts">
import { EyeIcon, EyeSlashIcon } from '@heroicons/vue/24/outline'
import type { HTMLAttributes } from 'vue'
import { ref } from 'vue'
import Button from '../button/Button.vue'
import Label from '../label/Label.vue'
import Input from './Input.vue'

defineProps<{
  defaultValue?: string
  modelValue?: string
  class?: HTMLAttributes['class']
  name?: string
  rules?: string
  placeholder?: string
  id?: string
}>()

const emits = defineEmits<{
  (e: 'update:modelValue', payload: string): void
}>()

const showPassword = ref(false)

const togglePassword = () => {
  showPassword.value = !showPassword.value
}

const handleUpdateModelValue = (value: string | number) => {
  emits('update:modelValue', value as string)
}
</script>

<template>
  <div class="space-y-2 relative">
    <Label htmlFor="password">Password</Label>
    <div class="relative">
      <Input
        :type="showPassword ? 'text' : 'password'"
        :model-value="modelValue"
        @update:model-value="handleUpdateModelValue"
        :default-value="defaultValue"
        :name="name"
        :rules="rules"
        :placeholder="placeholder"
        :id="id"
      />
      <Button
        type="button"
        size="sm"
        variant="ghost"
        class="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
        @click="togglePassword"
        :aria-label="showPassword ? 'Hide password' : 'Show password'"
      >
        <EyeIcon v-if="!showPassword" class="h-4 w-4" aria-hidden="true" />
        <EyeSlashIcon
          v-else
          class="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors"
          aria-hidden="true"
        />
        <span className="sr-only">{showPassword ? 'Hide password' : 'Show password'}</span>
      </Button>
    </div>
  </div>
</template>
