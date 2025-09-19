<template>
  <p>
    {{ functionCall.arguments.question }}
  </p>
</template>

<script setup lang="ts">
import type { AskUserCall } from '@/types/functionCalls'

defineProps<{
  functionCall: AskUserCall
}>()
</script>