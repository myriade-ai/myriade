<template>
  <button
    class="px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-xs text-white bg-primary-500 hover:bg-primary-600 disabled:bg-primary-800 focus:outline-hidden focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
    @click="onClick"
  >
    <slot></slot>
  </button>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'

interface Props {
  onClick: () => void
}

defineProps<Props>()
</script>
