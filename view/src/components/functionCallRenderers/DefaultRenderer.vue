<template>
  <pre class="arguments">{{ functionCall.arguments }}</pre>
</template>

<script setup lang="ts">
import type { BaseFunctionCall } from '@/types/functionCalls'

defineProps<{
  functionCall: BaseFunctionCall
}>()
</script>

<style scoped>
.arguments {
  font-family: monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-x: auto;
  max-width: 100%;
}
</style>