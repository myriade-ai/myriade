<template>
  <NodeViewWrapper as="span" class="agent-mention-wrapper">
    <span
      class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-purple-100 text-purple-700 font-medium text-sm cursor-default"
      contenteditable="false"
    >
      <span>@{{ node.attrs.label || 'Myriade Agent' }}</span>
    </span>
  </NodeViewWrapper>
</template>

<script setup lang="ts">
import { NodeViewWrapper } from '@tiptap/vue-3'

defineProps<{
  node: {
    attrs: {
      agentId: string
      label: string
    }
  }
}>()
</script>

<style>
.agent-mention-wrapper {
  display: inline;
}
</style>
