<template>
  <NodeViewWrapper as="span" class="user-mention-wrapper">
    <span
      class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-primary-100 text-primary-700 font-medium text-sm cursor-default"
      contenteditable="false"
    >
      <span>@{{ node.attrs.label || 'user' }}</span>
    </span>
  </NodeViewWrapper>
</template>

<script setup lang="ts">
import { NodeViewWrapper } from '@tiptap/vue-3'

defineProps<{
  node: {
    attrs: {
      userId: string
      label?: string
    }
  }
}>()
</script>

<style>
.user-mention-wrapper {
  display: inline;
}
</style>
