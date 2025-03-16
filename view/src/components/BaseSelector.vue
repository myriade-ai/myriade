<template>
  <select
    v-model="value"
    class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
  >
    <option v-for="(option, ind) in options" :key="ind" :value="option">
      {{ option.public ? '(public) ' : '' }}{{ option.name }}
    </option>
  </select>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import { computed } from 'vue'

type BaseOption = {
  name: string
}

const props = defineProps({
  options: {
    type: Array as PropType<BaseOption[]>,
    required: true
  },
  modelValue: {
    type: Object as PropType<BaseOption>,
    required: true
  }
})

const emits = defineEmits(['update:modelValue'])

const value = computed({
  get: () => props.modelValue,
  set: (value) => emits('update:modelValue', value)
})
</script>
