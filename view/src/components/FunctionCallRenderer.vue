<template>
  <div v-if="!shouldHide">
    <div class="flex items-center gap-2 mb-2">
      <span class="text-lg">{{ displayInfo.icon }}</span>
      <b class="text-gray-700">{{ displayInfo.displayName }}</b>
      <span v-if="displayInfo.description" class="text-sm text-gray-500">
        - {{ displayInfo.description }}
      </span>
    </div>

    <!-- Memory search renderer -->
    <div v-if="isMemorySearchCall(functionCall)">
      <p>Search: "{{ functionCall.arguments.search }}"</p>
    </div>

    <!-- Think renderer -->
    <div v-else-if="isThinkCall(functionCall)">
      <p class="text-sm text-gray-500">
        <MarkdownDisplay :content="functionCall.arguments.thought" />
      </p>
    </div>

    <!-- Ask user renderer -->
    <div v-else-if="isAskUserCall(functionCall)">
      <p>
        {{ functionCall.arguments.question }}
      </p>
    </div>

    <!-- SQL query renderer -->
    <div v-else-if="isSqlQueryCall(functionCall)">
      <BaseEditor :modelValue="functionCall.arguments.query" :read-only="true" />
    </div>

    <!-- Submit renderer -->
    <div v-else-if="isSubmitCall(functionCall)">
      <BaseEditorPreview :queryId="queryId" :databaseId="databaseSelectedId ?? undefined" />
    </div>

    <!-- Default fallback renderer -->
    <div v-else>
      <pre class="arguments">{{ formattedArguments }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FunctionCall } from '@/types/functionCalls'
import {
  isAskUserCall,
  isMemorySearchCall,
  isSqlQueryCall,
  isSubmitCall,
  isThinkCall
} from '@/types/functionCalls'
import { getFunctionCallDisplayInfo } from '@/utils/functionCallDisplayNames'
import { computed } from 'vue'

// Import components used by the inline renderers
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'
import BaseEditor from '@/components/base/BaseEditor.vue'
import BaseEditorPreview from '@/components/base/BaseEditorPreview.vue'

const props = defineProps<{
  functionCall: FunctionCall
  queryId?: string
  databaseSelectedId?: string | null
}>()

// Compute display information for the function call
const displayInfo = computed(() => getFunctionCallDisplayInfo(props.functionCall.name))

const sanitizedArguments = computed(() => {
  const args = props.functionCall.arguments
  if (!args || typeof args !== 'object') {
    return args
  }

  if ('proposal' in (args as Record<string, unknown>)) {
    const { proposal, ...rest } = args as Record<string, unknown>
    return rest
  }

  return args
})

const formattedArguments = computed(() => {
  const args = sanitizedArguments.value
  if (args === null || args === undefined) return ''
  if (typeof args === 'string') return args
  if (typeof args === 'number' || typeof args === 'boolean') return String(args)
  try {
    return JSON.stringify(args, null, 2)
  } catch (e) {
    console.error('Error formatting arguments:', e)
    return String(args)
  }
})

const shouldHide = computed(() => {
  const name = props.functionCall.name
  if (name === 'CatalogTool-catalog__update_asset' || name === 'CatalogTool-catalog__upsert_term') {
    return true
  }

  const args = props.functionCall.arguments
  if (typeof args === 'object' && args !== null && 'proposal' in args) {
    const proposal = (args as Record<string, any>).proposal
    const operation = proposal?.operation
    return operation === 'update_asset' || operation === 'upsert_term'
  }

  return false
})
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
