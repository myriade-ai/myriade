<template>
  <button
    :class="
      'px-4 py-2 inline-flex items-center border border-transparent text-base font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2' +
      ' ' +
      (props.color === 'secondary'
        ? 'text-muted-foreground bg-card hover:bg-muted focus:ring-primary-500  border border-input'
        : 'text-white bg-primary-600 hover:bg-primary-700 focus:ring-primary-500')
    "
    @click="onClick"
  >
    <span v-if="props.isLoading" class="flex items-center">
      <svg
        class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        ></circle>
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        ></path>
      </svg>
      <slot v-if="slots.loading" name="loading" class="flex items-center"></slot>
      <slot v-else></slot>
    </span>
    <slot v-else></slot>
  </button>
</template>

<script setup lang="ts">
import { defineProps, useSlots, type PropType } from 'vue'

const props = defineProps({
  color: {
    type: String as PropType<'primary' | 'secondary'>,
    default: 'primary'
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  onClick: {
    type: Function as PropType<() => void>,
    required: true
  }
})
const slots = useSlots()
</script>
