<template>
  <div class="message-display px-4 py-4 my-2 rounded-lg bg-gray-100">
    <!-- if message.display = false, then show as light gray (internal message) -->
    <div>
      <span class="flex justify-between items-center w-full">
        <span class="font-bold">{{ props.message.role }}</span>

        <span></span>
        <!-- Empty span to push content to the right -->
        <span class="flex items-center space-x-2 font-normal">
          <!-- Edit button for user messages -->
          <span v-if="props.message.role === 'user'" class="flex items-center space-x-2">
            <button
              class="text-blue-500 hover:text-blue-700 flex items-center"
              @click="toggleEditMode"
              title="Edit message"
            >
              <PencilSquareIcon class="h-4 w-4" />
              <span class="ml-1 hidden lg:inline">edit message</span>
            </button>
          </span>

          <!-- Edit inline button for SQL queries -->
          <span v-if="props.message.queryId" class="flex items-center space-x-2">
            <span v-if="props.message.role === 'user'" class="text-gray-400 mx-2">|</span>
            <button
              class="text-blue-500 hover:text-blue-700 flex items-center"
              @click="editInline"
              title="Edit inline"
            >
              <PencilSquareIcon class="h-4 w-4" />
              <span class="ml-1 hidden lg:inline">edit inline</span>
            </button>
            <span class="text-gray-400 mx-2">|</span>
            <a
              :href="`/query/${props.message.queryId}`"
              class="text-blue-500 hover:text-blue-700 flex items-center"
              target="_blank"
              title="Edit in new tab"
            >
              <PencilIcon class="h-4 w-4" />
              <span class="ml-1 hidden lg:inline">edit</span>
            </a>
          </span>
          <span
            v-if="
              (props.message.queryId || props.message.role === 'user') &&
              props.message.role !== 'function'
            "
            class="text-gray-400 mx-2"
            >|</span
          >
          <button
            v-if="props.message.role !== 'function'"
            class="text-blue-500 hover:text-blue-700 flex items-center"
            title="Regenerate from this message"
            @click="() => emit('regenerateFromMessage', props.message.id)"
          >
            <ArrowPathIcon class="h-4 w-4" />
            <span class="ml-1 hidden lg:inline">regenerate</span>
          </button>
        </span>
      </span>
    </div>

    <!-- Edit mode for user messages -->
    <div v-if="isEditing && props.message.role === 'user'" class="mt-2 mb-2">
      <textarea
        v-model="editedContent"
        class="w-full border border-gray-300 rounded-sm py-2 px-3"
        rows="4"
      ></textarea>
      <div class="flex justify-end mt-2">
        <button
          @click="cancelEdit"
          class="mr-2 px-3 py-1 text-sm text-gray-700 bg-gray-200 rounded-sm hover:bg-gray-300"
        >
          Cancel
        </button>
        <button
          @click="saveEdit"
          class="px-3 py-1 text-sm text-white bg-blue-500 rounded-sm hover:bg-blue-600"
        >
          Send
        </button>
      </div>
    </div>

    <!-- Normal display mode -->
    <div v-else>
      <template v-for="(part, index) in parsedText">
        <span
          v-if="part.type === 'text'"
          :key="`text-${index}`"
          v-html="renderMarkdown(part.content)"
        ></span>
        <div
          style="white-space: pre-wrap; background-color: #db282873; padding: 0.6rem"
          v-if="part.type === 'error'"
          :key="`error-${index}`"
        >
          {{ part.content }}
        </div>
        <BaseEditor
          v-if="part.type === 'sql'"
          :modelValue="part.content"
          :read-only="true"
          :key="`sql-${index}`"
        ></BaseEditor>
        <BaseTable v-if="part.type === 'json'" :data="part.content" :key="`json-${index}`" />
        <Echart v-if="part.type === 'echarts'" :option="part.content" :key="`echarts-${index}`" />
      </template>

      <div v-if="props.message.image">
        <img :src="`data:image/png;base64,${props.message.image}`" />
      </div>
      <div v-if="props.message.functionCall">
        <b>> {{ props.message.functionCall?.name }} </b>
        <p v-if="props.message.functionCall?.name === 'memory_search'">
          Search: "{{ props.message.functionCall?.arguments?.search }}"
        </p>
        <p v-else-if="props.message.functionCall?.name === 'think'">
          {{ props.message.functionCall?.arguments?.thought }}
        </p>
        <p v-else-if="props.message.functionCall?.name === 'ask_user'">
          {{ props.message.functionCall?.arguments?.question }}
        </p>
        <BaseEditor
          v-else-if="props.message.functionCall?.name.endsWith('sql_query')"
          :modelValue="props.message.functionCall?.arguments?.query"
          :read-only="true"
        ></BaseEditor>
        <BaseEditorPreview
          v-else-if="props.message.functionCall?.name === 'submit'"
          :queryId="props.message.queryId"
          :databaseId="databaseSelectedId"
        ></BaseEditorPreview>
        <pre v-else class="arguments">{{ props.message.functionCall?.arguments }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from '@/plugins/axios'
import yaml from 'js-yaml'
import { marked } from 'marked'
import { computed, defineEmits, defineProps, onMounted, ref } from 'vue'

// Components
import BaseEditor from '@/components/base/BaseEditor.vue'
import BaseEditorPreview from '@/components/base/BaseEditorPreview.vue'
import BaseTable from '@/components/base/BaseTable.vue'
import Echart from '@/components/Echart.vue'
import { ArrowPathIcon, PencilIcon, PencilSquareIcon } from '@heroicons/vue/24/outline'

// Store
import { useDatabasesStore } from '@/stores/databases'

const { databaseSelectedId } = useDatabasesStore()

interface FunctionCall {
  name: string
  arguments: any
}

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
  emit('editInlineClick', props.message.functionCall?.arguments?.query)
}

async function executeSql(sql: string) {
  try {
    const result = await axios.post('/api/query/_run', {
      query: sql,
      databaseId: databaseSelectedId.value
    })
    console.log(result.data.rows)
    sqlResult.value = result.data.rows
    sqlCount.value = result.data.count
  } catch (error) {
    console.error('Error executing SQL:', error)
  }
}

function renderMarkdown(text: string) {
  return marked(text)
}

const parsedText = computed(() => {
  const regex = /```((?:sql|json|error|ya?ml-graph|echarts))\s*([\s\S]*?)\s*```/g
  let match
  let lastIndex = 0
  const parts: Array<{ type: string; content: any }> = []

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
.message-display {
  border: 1px solid #e5e7eb;
  overflow: hidden;
}
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
}
</style>
