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

    <!-- Code editor read file renderer - compact badge only -->
    <div v-else-if="isCodeEditorReadFileCall(functionCall)" class="flex items-center gap-2">
      <span class="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
        📄 Reading {{ (functionCall.arguments.path as string) || 'file' }}
        <span v-if="functionCall.arguments.start_line && functionCall.arguments.end_line">
          (lines {{ functionCall.arguments.start_line }}-{{ functionCall.arguments.end_line }})
        </span>
      </span>
    </div>

    <!-- Code editor string replace renderer - show diff -->
    <div v-else-if="isCodeEditorReplaceCall(functionCall)">
      <CodeDiffDisplay
        :oldString="(functionCall.arguments.old_string as string) || undefined"
        :newString="(functionCall.arguments.new_string as string) || undefined"
        :fileName="(functionCall.arguments.path as string) || undefined"
      />
    </div>

    <!-- Code editor create file renderer - show new file content -->
    <div v-else-if="isCodeEditorCreateFileCall(functionCall)">
      <CodeFileDisplay
        :content="(functionCall.arguments.content as string) || ''"
        :fileName="(functionCall.arguments.path as string) || undefined"
        :isNewFile="true"
      />
    </div>

    <!-- Hide catalog operations -->
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
  isCodeEditorCreateFileCall,
  isCodeEditorReadFileCall,
  isCodeEditorReplaceCall,
  isMemorySearchCall,
  isSqlQueryCall,
  isSubmitCall,
  isThinkCall
} from '@/types/functionCalls'
import { getFunctionCallDisplayInfo } from '@/utils/functionCallDisplayNames'
import { computed } from 'vue'

// Import components used by the inline renderers
import BaseEditor from '@/components/base/BaseEditor.vue'
import BaseEditorPreview from '@/components/base/BaseEditorPreview.vue'
import CodeDiffDisplay from '@/components/CodeDiffDisplay.vue'
import CodeFileDisplay from '@/components/CodeFileDisplay.vue'
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'

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
