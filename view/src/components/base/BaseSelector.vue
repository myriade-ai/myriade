<template>
  <select
    v-model="value"
    class="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-hidden focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
  >
    <option v-for="(option, ind) in options" :key="ind" :value="option.id">
      {{ option.public ? '(public) ' : '' }}{{ option.name }}
    </option>
  </select>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import { computed } from 'vue'

type BaseOption = {
  id: string
  name: string
  public?: boolean
}

const props = defineProps({
  options: {
    type: Array as PropType<BaseOption[]>,
    required: true
  },
  modelValue: {
    type: String as PropType<string | null>,
    required: false,
    default: null
  }
})

const emits = defineEmits(['update:modelValue'])

const value = computed({
  get: () => props.modelValue,
  set: (value) => emits('update:modelValue', value)
})
</script>
