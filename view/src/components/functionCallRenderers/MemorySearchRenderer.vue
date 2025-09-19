<template>
  <p>
    Search: "{{ functionCall.arguments.search }}"
  </p>
</template>

<script setup lang="ts">
import type { MemorySearchCall } from '@/types/functionCalls'

defineProps<{
  functionCall: MemorySearchCall
}>()
</script>