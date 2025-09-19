<template>
  <div
    :class="
      cn(
        'my-2',
        props.message.role === 'user'
          ? cn('bg-gray-100 rounded-lg p-4', isEditing ? 'w-full' : 'max-w-3/4 ml-auto')
          : 'w-full p-2'
      )
    "
  >
    <!-- Message header with role and actions -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
      <span class="font-bold text-sm text-gray-600" :v-if="props.message.role !== 'user'">{{
        props.message.role
      }}</span>
      <div class="flex items-center font-normal flex-wrap justify-end">
        <!-- Edit button for user messages -->
        <span v-if="props.message.role === 'user'" class="flex items-center">
          <Button
            @click="toggleEditMode"
            title="Edit message"
            variant="ghost"
            class="text-primary-600 hover:text-primary-800 p-0 px-0"
          >
            <SquarePen class="h-3 w-3 sm:h-4 sm:w-4" />
          </Button>
        </span>

        <!-- Edit inline button for SQL queries -->
        <span v-if="props.message.queryId" class="flex items-center">
          <Button
            variant="ghost"
            size="sm"
            class="text-primary-600 hover:text-primary-800 hover:bg-gray-200 p-1"
            @click="editInline"
            title="Edit inline"
          >
            <SquarePen class="h-3 w-3 sm:h-4 sm:w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            class="text-primary-600 hover:text-primary-800 hover:bg-gray-200 p-1"
            @click="editInNewTab"
            title="Edit in new tab"
          >
            <Pencil class="h-3 w-3 sm:h-4 sm:w-4" />
          </Button>
        </span>

        <Button
          v-if="props.message.role !== 'function'"
          variant="ghost"
          size="sm"
          class="text-primary-600 hover:text-primary-800 p-1"
          title="Regenerate from this message"
          @click="() => emit('regenerateFromMessage', props.message.id)"
        >
          <RotateCcw class="h-3 w-3 sm:h-4 sm:w-4" />
        </Button>
      </div>
    </div>

    <!-- Message content -->
    <div class="w-full overflow-y-hidden">
      <!-- Edit mode for user messages -->
      <div v-if="isEditing && props.message.role === 'user'" class="mt-2 mb-2">
        <Textarea
          v-model="editedContent"
          class="w-full border border-gray-300 rounded-sm py-2 px-3 resize-none"
          rows="4"
        />
        <div class="flex flex-col sm:flex-row justify-end mt-2 gap-2">
          <Button @click="cancelEdit" variant="secondary" size="sm"> Cancel </Button>
          <Button @click="saveEdit" size="sm"> Send </Button>
        </div>
      </div>

      <!-- Normal display mode -->
      <div v-else class="w-full overflow-hidden">
        <template v-for="(part, index) in parsedText">
          <div v-if="part.type === 'text'" :key="`text-${index}`" class="w-full">
            <MarkdownDisplay :content="part.content"></MarkdownDisplay>
          </div>
          <div
            v-if="part.type === 'error'"
            :key="`error-${index}`"
            class="w-full overflow-x-auto p-2 sm:p-3 bg-red-100 border border-red-300 rounded text-sm"
            style="white-space: pre-wrap"
          >
            {{ part.content }}
          </div>
          <div v-if="part.type === 'query'" :key="`query-${index}`" class="w-full overflow-hidden">
            <BaseEditorPreview
              :queryId="part.query_id"
              :databaseId="databaseSelectedId ?? undefined"
            ></BaseEditorPreview>
          </div>
          <div v-if="part.type === 'chart' && part.chart_id" :key="`chart-${index}`" class="w-full">
            <Chart :chartId="part.chart_id" />
          </div>
          <div v-if="part.type === 'sql'" :key="`sql-${index}`" class="w-full overflow-hidden">
            <BaseEditor :modelValue="part.content" :read-only="true"></BaseEditor>
          </div>
          <div v-if="part.type === 'json'" :key="`json-${index}`" class="w-full overflow-x-auto">
            <BaseTable :data="part.content" :count="part.content.length" />
          </div>
          <!-- TODO: remove -->
          <Echart v-if="part.type === 'echarts'" :option="part.content" :key="`echarts-${index}`" />
        </template>

        <div v-if="props.message.image" class="w-full">
          <img :src="`data:image/png;base64,${props.message.image}`" class="max-w-full h-auto" />
        </div>
        <FunctionCallRenderer
          v-if="props.message.functionCall"
          :functionCall="props.message.functionCall as FunctionCall"
          :queryId="props.message.queryId"
          :databaseSelectedId="databaseSelectedId"
        />
        <AskQueryConfirmation
          v-if="needsConfirmation && queryData && props.message.role === 'assistant'"
          :queryId="queryData.id"
          :operationType="queryData.operationType"
          :status="queryData.status"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from '@/plugins/axios'
import { useQueriesStore } from '@/stores/queries'
import yaml from 'js-yaml'
import { computed, defineEmits, defineProps, onMounted, ref } from 'vue'

// Components
import AskQueryConfirmation from '@/components/AskQueryConfirmation.vue'
import BaseEditor from '@/components/base/BaseEditor.vue'
import BaseEditorPreview from '@/components/base/BaseEditorPreview.vue'
import BaseTable from '@/components/base/BaseTable.vue'
import Chart from '@/components/Chart.vue'
import Echart from '@/components/Echart.vue'
import { FunctionCallRenderer } from '@/components/functionCallRenderers'
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'
// Store
import { cn } from '@/lib/utils'
import { useDatabasesStore } from '@/stores/databases'
import type { FunctionCall } from '@/types/functionCalls'
import { Pencil, RotateCcw, SquarePen } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { Button } from './ui/button'
import { Textarea } from './ui/textarea'

const { databaseSelectedId } = useDatabasesStore()
const router = useRouter()

interface Message {
  content: string
  display: boolean
  role: string
  queryId?: string
  id?: string
  functionCall?: FunctionCall
  image?: string // base64 encoded image
}

const props = defineProps<{
  message: Message
}>()

const emit = defineEmits(['editInlineClick', 'regenerateFromMessage'])

// Local state
const sqlResult = ref<Array<Record<string, string | number | boolean | null>>>([])
const sqlCount = ref(0)
const isEditing = ref(false)
const editedContent = ref('')

// Query confirmation using store
const queriesStore = useQueriesStore()
const queryData = computed(() => queriesStore.getQuery(props.message.queryId))
const needsConfirmation = computed(() => queriesStore.needsConfirmation(props.message.queryId))

const toggleEditMode = () => {
  isEditing.value = !isEditing.value
  editedContent.value = props.message.content
}

const saveEdit = () => {
  emit('regenerateFromMessage', props.message.id, editedContent.value)
  isEditing.value = false
  editedContent.value = ''
}

const cancelEdit = () => {
  isEditing.value = false
  editedContent.value = ''
}

// Methods
function editInline() {
  // Type assertion since we know this is called only for SQL queries
  const sqlCall = props.message.functionCall as any
  emit('editInlineClick', sqlCall?.arguments?.query)
}

function editInNewTab() {
  if (props.message.queryId) {
    const routeData = router.resolve({
      name: 'Query',
      params: { id: props.message.queryId }
    })
    window.open(routeData.href, '_blank')
  }
}

// TODO: move to store
async function executeSql(sql: string) {
  try {
    const result = await axios.post('/api/query/_run', {
      query: sql,
      databaseId: databaseSelectedId
    })
    console.log(result.data.rows)
    sqlResult.value = result.data.rows
    sqlCount.value = result.data.count
  } catch (error) {
    console.error('Error executing SQL:', error)
  }
}

const parsedText = computed<
  Array<{ type: string; content: any; query_id?: string; chart_id?: string }>
>(() => {
  const regex = /```((?:sql|json|error|ya?ml-graph|echarts))\s*([\s\S]*?)\s*```/g
  let match
  let lastIndex = 0
  const parts: Array<{ type: string; content: any; query_id?: string; chart_id?: string }> = []

  // if content is a list, return it as is
  if (Array.isArray(props.message.content)) {
    return props.message.content as Array<{
      type: string
      content: any
      query_id?: string
      chart_id?: string
    }>
  }

  while ((match = regex.exec(props.message.content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({
        type: 'text',
        content: props.message.content.slice(lastIndex, match.index)
      })
    }

    let type = match[1]
    let content
    if (type === 'json') {
      content = JSON.parse(match[2].trim())
    } else if (type === 'sql') {
      content = match[2].trim()
    } else if (type === 'yml-graph' || type === 'yaml-graph') {
      content = yaml.load(match[2].trim())
      console.log('content', content)
    } else if (type === 'error') {
      content = match[2]
    } else if (type === 'echarts') {
      content = JSON.parse(match[2].trim())
    } else {
      throw new Error(`Unknown type ${type}`)
    }

    parts.push({
      type,
      content
    })

    lastIndex = match.index + match[0].length
  }

  // Remaining text after the last match
  if (lastIndex < props.message.content?.length) {
    parts.push({
      type: 'text',
      content: props.message.content.slice(lastIndex)
    })
  }

  return parts
})

onMounted(() => {
  // If we detect yml-graph blocks, execute the SQL in them automatically
  parsedText.value.forEach((part) => {
    if (part.type === 'yml-graph' || part.type === 'yaml-graph') {
      // In this example, we assume the YAML block has { sql: "..."}
      if (part.content && part.content.sql) {
        executeSql(part.content.sql)
      }
    }
  })
})
</script>

<style>
.sql-code {
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 2px 4px;
  font-family: monospace;
  white-space: pre-wrap;
}

.arguments {
  font-family: monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-x: auto;
  max-width: 100%;
}

.message-display :deep(h1) {
  font-size: 1.5em;
  font-weight: bold;
  margin-top: 1em;
  margin-bottom: 0.5em;
}

.message-display :deep(h2) {
  font-size: 1.3em;
  font-weight: bold;
  margin-top: 1em;
  margin-bottom: 0.5em;
}

.message-display :deep(p) {
  margin-bottom: 0.5em;
}

.message-display :deep(ul),
.message-display :deep(ol) {
  margin-left: 1.5em;
  margin-bottom: 0.5em;
}

.message-display :deep(code) {
  background-color: #f0f0f0;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: monospace;
  word-break: break-all;
  overflow-wrap: break-word;
}

.message-display :deep(pre) {
  overflow-x: auto;
  max-width: 100%;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-display :deep(table) {
  display: block;
  overflow-x: auto;
  white-space: nowrap;
  max-width: 100%;
}

@media (max-width: 640px) {
  .message-display :deep(h1) {
    font-size: 1.3em;
  }

  .message-display :deep(h2) {
    font-size: 1.2em;
  }
}
</style>
