<template>
  <BaseEditor :modelValue="functionCall.arguments.query" :read-only="true" />
</template>

<script setup lang="ts">
import BaseEditor from '@/components/base/BaseEditor.vue'
import type { SqlQueryCall } from '@/types/functionCalls'

defineProps<{
  functionCall: SqlQueryCall
}>()
</script>
