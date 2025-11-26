<template>
  <div class="border rounded-lg overflow-hidden bg-card">
    <!-- Header badge -->
    <div class="flex items-center justify-between bg-muted border-b px-3 py-2">
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-muted-foreground">
          {{ isNewFile ? '📝 New File' : '📄 File Content' }}
        </span>
        <span v-if="fileName" class="text-xs text-muted-foreground font-mono">{{ fileName }}</span>
      </div>
      <div class="flex items-center gap-2">
        <span
          v-if="isNewFile"
          class="text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 px-2 py-1 rounded-full"
        >
          New
        </span>
        <span
          class="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-2 py-1 rounded-full"
        >
          {{ lineCount }} lines
        </span>
        <button
          @click="isExpanded = !isExpanded"
          class="text-xs text-muted-foreground hover:text-muted-foreground transition-colors"
        >
          {{ isExpanded ? 'Collapse' : 'Open' }}
        </button>
      </div>
    </div>

    <!-- Expandable content -->
    <div v-if="isExpanded" class="max-h-96 overflow-y-auto">
      <BaseEditor :modelValue="cleanContent" :read-only="true" />
    </div>
  </div>
</template>

<script setup lang="ts">
import BaseEditor from '@/components/base/BaseEditor.vue'
import { computed, ref } from 'vue'

const props = defineProps<{
  content?: string
  fileName?: string
  isNewFile?: boolean
}>()

const isExpanded = ref(false)

// Parse content to remove line numbers format and header lines
const cleanContent = computed(() => {
  if (!props.content) return ''

  let lines = props.content.split('\n')

  // Remove header lines "line number|line content" and "---|---" if present
  if (
    lines.length >= 2 &&
    lines[0].includes('line number|line content') &&
    lines[1].includes('---|---')
  ) {
    lines = lines.slice(2) // Remove first two header lines
  }

  // Check if content has line number format like "  1|version: 2"
  const hasLineNumbers = lines.some((line) => /^\s*\d+\|/.test(line))

  if (hasLineNumbers) {
    return lines
      .map((line) => {
        const match = line.match(/^\s*\d+\|(.*)$/)
        return match ? match[1] : line
      })
      .join('\n')
      .trim() // Remove leading/trailing whitespace
  }

  return lines.join('\n').trim()
})

const lineCount = computed(() => {
  return cleanContent.value.split('\n').length
})
</script>
