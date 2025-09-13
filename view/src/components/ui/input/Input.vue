<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { computed } from 'vue'

const props = defineProps<{
  defaultValue?: string | number
  modelValue?: string | number
  class?: HTMLAttributes['class']
  name?: string
  rules?: string
  placeholder?: string
  type?: string
  id?: string
}>()

const emits = defineEmits<{
  (e: 'update:modelValue', payload: string | number): void
}>()

const modelValue = computed({
  get: () => props.modelValue,
  set: (val) => {
    emits('update:modelValue', val as string | number)
  }
})

const inputId = computed(
  () => props.id || props.name || `input-${Math.random().toString(36).substr(2, 9)}`
)
</script>

<template>
  <input
    :id="inputId"
    :name="name"
    :type="type || 'text'"
    v-model="modelValue"
    :placeholder="placeholder"
    data-slot="input"
    :class="
      cn(
        'file:text-foreground placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground dark:bg-input/30 border-input flex h-9 w-full min-w-0 rounded-md border bg-transparent px-3 py-1 text-base shadow-xs transition-[color,box-shadow] outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm',
        'focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]',
        'aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive',
        name && 'mt-1',
        props.class
      )
    "
  />
</template>
