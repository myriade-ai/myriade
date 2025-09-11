<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { useField } from 'vee-validate'
import { computed } from 'vue'
import Label from '@/components/ui/label/Label.vue'
import Input from './Input.vue'

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

// Use vee-validate's useField if name is provided, otherwise use regular v-model
const fieldResult = props.name
  ? useField(props.name, props.rules, {
      initialValue: props.defaultValue
    })
  : null

const errorMessage = computed(() => fieldResult?.errorMessage?.value)

const modelValue = computed({
  get: () => (fieldResult ? fieldResult.value.value : props.modelValue),
  set: (val) => {
    if (fieldResult) {
      fieldResult.handleChange(val)
    }
    emits('update:modelValue', val as string | number)
  }
})

const handleBlur = () => {
  if (fieldResult) {
    fieldResult.handleBlur()
  }
}

const inputId = computed(
  () => props.id || props.name || `input-${Math.random().toString(36).substr(2, 9)}`
)
</script>

<template>
  <div class="space-y-2">
    <Label v-if="name" :for="inputId" :class="cn('text-sm font-medium leading-none')">
      {{ name }}
    </Label>
    <Input
      :id="inputId"
      :name="name"
      :type="type || 'text'"
      v-model="modelValue"
      :placeholder="placeholder"
      @blur="handleBlur"
    />
    <p v-if="errorMessage" class="text-sm text-destructive">
      {{ errorMessage }}
    </p>
  </div>
</template>
