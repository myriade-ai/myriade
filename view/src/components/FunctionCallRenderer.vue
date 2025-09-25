<template>
  <div>
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

    <div v-else-if="argumentsNameToHide.includes(functionCall.name)"></div>

    <!-- Default fallback renderer -->
    <div v-else>
      <pre class="arguments">{{ functionCall.arguments }}</pre>
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

const argumentsNameToHide = [
  'CatalogTool-catalog__update_asset',
  'CatalogTool-catalog__upsert_term'
]

// Compute display information for the function call
const displayInfo = computed(() => getFunctionCallDisplayInfo(props.functionCall.name))
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
