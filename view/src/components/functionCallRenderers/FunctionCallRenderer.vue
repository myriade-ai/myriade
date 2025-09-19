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
    <MemorySearchRenderer v-if="isMemorySearchCall(functionCall)" :functionCall="functionCall" />

    <!-- Think renderer -->
    <ThinkRenderer v-else-if="isThinkCall(functionCall)" :functionCall="functionCall" />
    <!-- Ask user renderer -->
    <AskUserRenderer v-else-if="isAskUserCall(functionCall)" :functionCall="functionCall" />
    <!-- SQL query renderer -->
    <SqlQueryRenderer
      v-else-if="isSqlQueryCall(functionCall)"
      :functionCall="functionCall as SqlQueryCall"
    />

    <!-- Submit renderer -->
    <SubmitRenderer
      v-else-if="isSubmitCall(functionCall)"
      :functionCall="functionCall"
      :queryId="queryId"
      :databaseSelectedId="databaseSelectedId"
    />

    <!-- Default fallback renderer -->
    <DefaultRenderer v-else :functionCall="functionCall" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FunctionCall, SqlQueryCall } from '@/types/functionCalls'
import {
  isMemorySearchCall,
  isThinkCall,
  isAskUserCall,
  isSqlQueryCall,
  isSubmitCall
} from '@/types/functionCalls'
import { getFunctionCallDisplayInfo } from '@/utils/functionCallDisplayNames'

// Import all renderer components
import MemorySearchRenderer from './MemorySearchRenderer.vue'
import ThinkRenderer from './ThinkRenderer.vue'
import AskUserRenderer from './AskUserRenderer.vue'
import SqlQueryRenderer from './SqlQueryRenderer.vue'
import SubmitRenderer from './SubmitRenderer.vue'
import DefaultRenderer from './DefaultRenderer.vue'

const props = defineProps<{
  functionCall: FunctionCall
  queryId?: string
  databaseSelectedId?: string | null
}>()

// Compute display information for the function call
const displayInfo = computed(() => getFunctionCallDisplayInfo(props.functionCall.name))
</script>
