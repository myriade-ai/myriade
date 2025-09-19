<template>
  <p class="text-sm text-gray-500">
    <MarkdownDisplay :content="functionCall.arguments.thought" />
  </p>
</template>

<script setup lang="ts">
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'
import type { ThinkCall } from '@/types/functionCalls'

defineProps<{
  functionCall: ThinkCall
}>()
</script>