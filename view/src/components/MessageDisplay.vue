<template>
  <div
    ref="messageRef"
    class="w-full flex flex-col item-end"
    :class="props.message.role === 'user' ? 'group' : ''"
  >
    <div
      :class="
        cn(
          props.message.role === 'user'
            ? cn(
                'bg-gray-100 rounded-lg p-4',
                isEditing ? 'w-full rounded-xl' : 'max-w-3/4 ml-auto'
              )
            : 'w-full p-2'
        )
      "
      @click.stop="props.message.role === 'user' ? toggleActionsVisibility() : undefined"
    >
      <div class="w-full overflow-y-hidden">
        <div v-if="isEditing">
          <Textarea
            v-model="editedContent"
            class="w-full min-h-8 border-none shadow-none outline-none focus-visible:ring-0 py-2 px-3 resize-none max-h-36"
            rows="2"
          />
          <div class="flex flex-col sm:flex-row justify-end mt-2 gap-2">
            <Button @click="cancelEdit" variant="secondary" size="sm" class="bg-white">
              Cancel
            </Button>
            <Button @click="saveEdit" size="sm" class="bg-primary hover:bg-primary/90">
              Send
            </Button>
          </div>
        </div>

        <!-- Normal display mode -->
        <div v-else class="w-full overflow-hidden">
          <!-- Function response renderer for CodeEditor read_file operations -->
          <div
            v-if="props.message.role === 'function' && props.message.name?.includes('read_file')"
          >
            <CodeFileDisplay :content="props.message.content" />
          </div>
          <template v-else v-for="(part, index) in parsedText">
            <div v-if="part.type === 'markdown'" :key="`text-${index}`" class="w-full">
              <MarkdownDisplay :content="part.content"></MarkdownDisplay>
            </div>
            <div v-if="part.type === 'text'" :key="`text-${index}`" class="w-full">
              <pre class="whitespace-pre-wrap">{{ part.content }}</pre>
            </div>
            <div
              v-if="part.type === 'error'"
              :key="`error-${index}`"
              class="w-full overflow-x-auto p-2 sm:p-3 bg-red-100 border border-red-300 rounded text-sm"
              style="white-space: pre-wrap"
            >
              {{ part.content }}
            </div>
            <div
              v-if="part.type === 'query'"
              :key="`query-${index}`"
              class="w-full overflow-hidden py-2"
            >
              <Card class="p-0 pb-3.5 pt-1">
                <CardContent>
                  <BaseEditorPreview :queryId="part.query_id"></BaseEditorPreview>
                </CardContent>
              </Card>
            </div>
            <div
              v-if="part.type === 'chart' && part.chart_id"
              :key="`chart-${index}`"
              class="w-full py-2"
            >
              <Card class="p-0 pb-3.5 pt-1">
                <CardContent>
                  <Chart :chartId="part.chart_id" />
                </CardContent>
              </Card>
            </div>
            <div v-if="part.type === 'sql'" :key="`sql-${index}`" class="w-full overflow-hidden">
              <BaseEditor :modelValue="part.content" :read-only="true"></BaseEditor>
            </div>
            <div v-if="part.type === 'json'" :key="`json-${index}`" class="w-full overflow-x-auto">
              <DataTable
                :data="Array.isArray(part.content) ? part.content : part.content.rows || []"
                :count="
                  part.content.count ?? (Array.isArray(part.content) ? part.content.length : 0)
                "
                :columns="part.content.columns"
                class="mt-2"
              />
            </div>
          </template>

          <div v-if="props.message.image" class="w-full">
            <img :src="`data:image/png;base64,${props.message.image}`" class="max-w-full h-auto" />
          </div>

          <FunctionCallRenderer
            v-else-if="props.message.functionCall"
            :functionCall="props.message.functionCall"
            :queryId="props.message.queryId"
          />
          <AskQueryConfirmation
            v-if="needsConfirmation && queryData && props.message.role === 'assistant'"
            :queryId="queryData.id"
            :operationType="queryData.operationType"
            :status="queryData.status"
            @rejected="emit('rejected')"
          />
          <AskCatalogConfirmation
            v-if="catalogOperation && props.message.role === 'assistant'"
            :function-call="props.message.functionCall"
            :asset="props.message.asset"
            :term="props.message.term"
          />
        </div>
      </div>

      <!-- Message actions at bottom for assistant messages -->
      <div
        v-if="!isEditing && props.message.role !== 'user'"
        class="flex items-center gap-1 mt-2 justify-start -ml-2"
      >
        <!-- Edit inline button for SQL queries -->
        <template v-if="props.message.queryId">
          <Button variant="ghost" size="sm" class="p-1" @click="editInline" title="Edit inline">
            <SquarePen class="h-3 w-3 sm:h-4 sm:w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            class="p-1"
            @click="editInNewTab"
            title="Edit in new tab"
          >
            <Pencil class="h-3 w-3 sm:h-4 sm:w-4" />
          </Button>
        </template>

        <Button
          variant="ghost"
          size="sm"
          class="p-1"
          :disabled="isCopying"
          title="Copy message"
          @click="copyMessage"
        >
          <Loader2 v-if="isCopying" class="h-3 w-3 sm:h-4 sm:w-4 animate-spin" />
          <Check v-else-if="isCopied" class="h-3 w-3 sm:h-4 sm:w-4" />
          <Copy v-else class="h-3 w-3 sm:h-4 sm:w-4" />
        </Button>

        <Button
          v-if="props.message.role !== 'function'"
          variant="ghost"
          size="sm"
          class="p-1"
          title="Regenerate from this message"
          @click="() => emit('regenerateFromMessage', props.message.id)"
        >
          <RotateCcw class="h-3 w-3 sm:h-4 sm:w-4" />
        </Button>
      </div>
    </div>

    <!-- Message actions outside card for user messages -->
    <div
      v-if="!isEditing && props.message.role === 'user'"
      :class="
        cn(
          'flex items-center gap-1 mt-2',
          'max-w-3/4 ml-auto justify-end',
          '-mr-2',
          'transition-opacity',
          showActions ? 'opacity-100' : 'opacity-0 sm:group-hover:opacity-100'
        )
      "
    >
      <!-- Copy button for user messages -->
      <Button
        @click="copyMessage"
        title="Copy message"
        variant="ghost"
        size="sm"
        class="p-1"
        :disabled="isCopying"
      >
        <Loader2 v-if="isCopying" class="h-3 w-3 sm:h-4 sm:w-4 animate-spin" />
        <Check v-else-if="isCopied" class="h-3 w-3 sm:h-4 sm:w-4" />
        <Copy v-else class="h-3 w-3 sm:h-4 sm:w-4" />
      </Button>

      <!-- Edit button for user messages -->
      <Button @click="toggleEditMode" title="Edit message" variant="ghost" size="sm" class="p-1">
        <SquarePen class="h-3 w-3 sm:h-4 sm:w-4" />
      </Button>

      <!-- Edit inline button for SQL queries -->
      <template v-if="props.message.queryId">
        <Button variant="ghost" size="sm" class="p-1" @click="editInline" title="Edit inline">
          <SquarePen class="h-3 w-3 sm:h-4 sm:w-4" />
        </Button>
        <Button variant="ghost" size="sm" class="p-1" @click="editInNewTab" title="Edit in new tab">
          <Pencil class="h-3 w-3 sm:h-4 sm:w-4" />
        </Button>
      </template>

      <Button
        variant="ghost"
        size="sm"
        class="p-1"
        title="Regenerate from this message"
        @click="() => emit('regenerateFromMessage', props.message.id)"
      >
        <RotateCcw class="h-3 w-3 sm:h-4 sm:w-4" />
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useQueriesStore } from '@/stores/queries'
import { computed, defineEmits, defineProps, onMounted, onUnmounted, ref } from 'vue'

// Components
import AskCatalogConfirmation from '@/components/AskCatalogConfirmation.vue'
import AskQueryConfirmation from '@/components/AskQueryConfirmation.vue'
import BaseEditor from '@/components/base/BaseEditor.vue'
import BaseEditorPreview from '@/components/base/BaseEditorPreview.vue'
import Chart from '@/components/Chart.vue'
import DataTable from '@/components/DataTable.vue'
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'
// Store
import { cn } from '@/lib/utils'
import type { Message } from '@/stores/conversations'
import axios from '@/plugins/axios'
import { Check, Copy, Loader2, Pencil, RotateCcw, SquarePen } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import CodeFileDisplay from './CodeFileDisplay.vue'
import FunctionCallRenderer from './FunctionCallRenderer.vue'
import { Button } from './ui/button'
import { Card, CardContent } from './ui/card'
import { Textarea } from './ui/textarea'

const router = useRouter()

const props = defineProps<{
  message: Message
}>()

const emit = defineEmits(['editInlineClick', 'regenerateFromMessage', 'rejected'])

// Local state
const isEditing = ref(false)
const editedContent = ref('')
const isCopied = ref(false)
const isCopying = ref(false)
const showActions = ref(false)
const messageRef = ref<HTMLElement | null>(null)

// Query confirmation using store
const queriesStore = useQueriesStore()
const queryData = computed(() => queriesStore.getQuery(props.message.queryId))
const needsConfirmation = computed(() => queriesStore.needsConfirmation(props.message.queryId))

// Detect catalog operations based on function call name and available asset/term data
const catalogOperation = computed(() => {
  const functionCall = props.message.functionCall
  if (!functionCall) return false

  // Check if it's a catalog operation based on function name
  const isCatalogFunction =
    functionCall.name?.includes('catalog') ||
    functionCall.name?.includes('update_asset') ||
    functionCall.name?.includes('upsert_term')

  // Also check if we have asset or term data in the message
  const hasAssetOrTermData = !!(props.message.asset || props.message.term)

  return isCatalogFunction || hasAssetOrTermData
})

const toggleActionsVisibility = () => {
  showActions.value = !showActions.value
}

const handleClickOutside = (event: MouseEvent) => {
  if (messageRef.value && !messageRef.value.contains(event.target as Node)) {
    showActions.value = false
  }
}

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

const queryCopyCache = new Map<string, string>()
const chartCopyCache = new Map<string, string>()

const buildAssistantCopyContent = async () => {
  const parts = parsedText.value
  if (!parts?.length) {
    if (typeof props.message.content === 'string') {
      return props.message.content
    }

    try {
      return JSON.stringify(props.message.content, null, 2)
    } catch (error) {
      console.error('Failed to serialise assistant message content:', error)
      return ''
    }
  }

  const segments: string[] = []

  for (const part of parts) {
    if (!part) continue
    let chunk = ''

    if (part.type === 'markdown' || part.type === 'text') {
      if (typeof part.content === 'string') {
        chunk = part.content.trim()
      }
    } else if (part.type === 'error') {
      chunk = `Error:\n${String(part.content ?? '')}`.trim()
    } else if (part.type === 'sql') {
      const sql = String(part.content ?? '').trim()
      if (sql) {
        chunk = ['```sql', sql, '```'].join('\n')
      }
    } else if (part.type === 'json') {
      chunk = formatStructuredContent(part.content)
    } else if (part.type === 'query' && part.query_id) {
      chunk = await formatQueryForCopy(part.query_id)
    } else if (part.type === 'chart' && part.chart_id) {
      chunk = await formatChartForCopy(part.chart_id)
    }

    if (chunk) {
      segments.push(chunk)
    }
  }

  return segments.filter(Boolean).join('\n\n')
}

type TableRow = Record<string, unknown>
type TableColumn = string | { name?: string }
type QueryResultsPayload = {
  rows?: unknown[]
  columns?: TableColumn[]
}

const formatStructuredContent = (content: unknown) => {
  if (!content) return ''

  const rows = extractRows(content)
  const columnsSource = extractColumns(content, rows)

  if (rows.length && columnsSource.length) {
    return buildMarkdownTable(rows, columnsSource)
  }

  try {
    return JSON.stringify(content, null, 2)
  } catch (error) {
    console.error('Failed to serialise structured content:', error)
    return String(content)
  }
}

const extractRows = (content: unknown): unknown[] => {
  if (Array.isArray(content)) {
    return content
  }

  if (content && typeof content === 'object') {
    const maybeRows = (content as { rows?: unknown[] }).rows
    if (Array.isArray(maybeRows)) {
      return maybeRows
    }
  }

  return []
}

const extractColumns = (content: unknown, rows: unknown[]): TableColumn[] => {
  if (Array.isArray(content)) {
    return extractColumnsFromRows(rows)
  }

  if (content && typeof content === 'object') {
    const maybeColumns = (content as { columns?: TableColumn[] }).columns
    if (Array.isArray(maybeColumns) && maybeColumns.length) {
      return maybeColumns
    }
  }

  return extractColumnsFromRows(rows)
}

const extractColumnsFromRows = (rows: unknown[]): string[] => {
  if (!rows.length) return []
  const firstRow = rows[0]
  if (firstRow && typeof firstRow === 'object' && !Array.isArray(firstRow)) {
    return Object.keys(firstRow as TableRow)
  }
  return []
}

const normaliseColumnNames = (columns: TableColumn[]) =>
  columns.map((column) => {
    if (!column) return ''
    if (typeof column === 'string') return column
    if (typeof column === 'object' && column.name && typeof column.name === 'string') {
      return column.name
    }
    return String(column)
  })

const escapeTableValue = (value: unknown) => {
  if (value === null || value === undefined) return ''
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (value instanceof Date) return value.toISOString()
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch (error) {
      console.error('Failed to serialise table cell value:', error)
      return '[object]'
    }
  }
  return String(value)
}

const buildMarkdownTable = (rows: unknown[], columns: TableColumn[]) => {
  const columnNames = normaliseColumnNames(columns)
  if (!columnNames.length) return ''

  const header = `| ${columnNames.join(' | ')} |`
  const separator = `| ${columnNames.map(() => '---').join(' | ')} |`
  const lines = rows.map((row) => {
    if (row && typeof row === 'object' && !Array.isArray(row)) {
      const rowRecord = row as TableRow
      const cells = columnNames.map((column) => escapeTableValue(rowRecord[column]))
      return `| ${cells.join(' | ')} |`
    }
    const cellValue = escapeTableValue(row)
    return `| ${cellValue} |`
  })

  return [header, separator, ...lines].join('\n')
}

const formatQueryForCopy = async (queryId: string) => {
  if (queryCopyCache.has(queryId)) {
    return queryCopyCache.get(queryId) as string
  }

  try {
    const [queryResponse, resultsResponse] = await Promise.all([
      axios.get(`/api/query/${queryId}`),
      axios.get(`/api/query/${queryId}/results`).catch(() => null)
    ])

    const query = queryResponse.data
    const results = resultsResponse?.data as QueryResultsPayload | undefined

    const lines: string[] = [`SQL query (ID: ${queryId})`]

    if (query?.sql) {
      const formattedSql = String(query.sql).trim()
      if (formattedSql) {
        lines.push(['```sql', formattedSql, '```'].join('\n'))
      }
    }

    const rowsData = Array.isArray(results?.rows) ? results?.rows : null
    if (rowsData && rowsData.length) {
      const columnsData = results?.columns?.length
        ? (results.columns as TableColumn[])
        : extractColumnsFromRows(rowsData)
      const tableSection = buildMarkdownTable(rowsData, columnsData)
      if (tableSection) {
        lines.push('Query results:\n' + tableSection)
      }
    } else if (rowsData && rowsData.length === 0) {
      lines.push('Query results: (no rows returned)')
    }

    if (typeof window !== 'undefined') {
      lines.push(`Open in workspace: ${window.location.origin}/query/${queryId}`)
    }

    const formatted = lines.filter(Boolean).join('\n\n')
    queryCopyCache.set(queryId, formatted)
    return formatted
  } catch (error) {
    console.error('Failed to fetch query for copy:', error)
    return `Query ID: ${queryId}`
  }
}

const formatChartForCopy = async (chartId: string) => {
  if (chartCopyCache.has(chartId)) {
    return chartCopyCache.get(chartId) as string
  }

  try {
    const response = await axios.get(`/api/chart/${chartId}`)
    const chart = response.data

    const lines: string[] = [`Chart (ID: ${chartId})`]

    const title = chart?.config?.title?.text || chart?.name
    if (title) {
      lines.push(`Title: ${title}`)
    }

    if (chart?.config) {
      try {
        lines.push('Chart configuration:\n' + JSON.stringify(chart.config, null, 2))
      } catch (error) {
        console.error('Failed to serialise chart configuration:', error)
      }
    }

    if (typeof window !== 'undefined') {
      lines.push(`Open chart: ${window.location.origin}/chart/${chartId}`)
    }

    const formatted = lines.filter(Boolean).join('\n\n')
    chartCopyCache.set(chartId, formatted)
    return formatted
  } catch (error) {
    console.error('Failed to fetch chart for copy:', error)
    return `Chart ID: ${chartId}`
  }
}

const copyMessage = async () => {
  if (isCopying.value) return

  try {
    isCopying.value = true

    let contentToCopy = ''
    if (props.message.role === 'user') {
      if (typeof props.message.content === 'string') {
        contentToCopy = props.message.content
      } else {
        try {
          contentToCopy = JSON.stringify(props.message.content, null, 2)
        } catch (error) {
          console.error('Failed to serialise user message content:', error)
          contentToCopy = String(props.message.content ?? '')
        }
      }
    } else {
      contentToCopy = await buildAssistantCopyContent()
    }

    await navigator.clipboard.writeText(contentToCopy)
    isCopied.value = true
    setTimeout(() => {
      isCopied.value = false
    }, 2000)
  } catch (error) {
    console.error('Failed to copy message:', error)
  } finally {
    isCopying.value = false
  }
}

// Methods
function editInline() {
  const sqlArgs = props.message.functionCall?.arguments as { query?: string } | undefined
  emit('editInlineClick', sqlArgs?.query)
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

const parsedText = computed<
  Array<{ type: string; content: unknown; query_id?: string; chart_id?: string }>
>(() => {
  const regex = /```((?:sql|json|error))\s*([\s\S]*?)\s*```/g
  let match
  let lastIndex = 0
  const parts: Array<{ type: string; content: unknown; query_id?: string; chart_id?: string }> = []

  // if content is a list, return it as is
  if (Array.isArray(props.message.content)) {
    return props.message.content as Array<{
      type: string
      content: unknown
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
    let content: unknown
    if (type === 'json') {
      content = JSON.parse(match[2].trim())
    } else if (type === 'sql') {
      content = match[2].trim()
    } else if (type === 'error') {
      content = match[2]
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
  // Add click outside listener
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
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
