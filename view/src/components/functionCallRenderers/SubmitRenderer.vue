<template>
  <BaseEditorPreview
    :queryId="queryId"
    :databaseId="databaseSelectedId ?? undefined"
  />
</template>

<script setup lang="ts">
import BaseEditorPreview from '@/components/base/BaseEditorPreview.vue'
import type { SubmitCall } from '@/types/functionCalls'

defineProps<{
  functionCall: SubmitCall
  queryId?: string
  databaseSelectedId?: string | null
}>()
</script>