<template>
  <div
    class="message-display px-4 py-4 my-2 rounded-lg bg-gray-100"
    :class="{ 'bg-gray-300': message.display === false }"
  >
    <!-- if message.display = false, then show as light gray (internal message) -->
    <p class="font-bold">
      <span class="flex justify-between items-center w-full">
        {{ message.role }}
        <span class="flex items-center space-x-2">
          <span v-if="message.queryId" class="flex items-center space-x-2">
            <button 
              class="text-blue-500 hover:text-blue-700 flex items-center" 
              @click="editInline"
              title="Edit inline"
            >
              <PencilSquareIcon class="h-4 w-4" />
              <span class="ml-1">Edit inline</span>
            </button>
            <span class="text-gray-400">/</span>
            <a 
              :href="`/query/${message.queryId}`" 
              class="text-blue-500 hover:text-blue-700 flex items-center" 
              target="_blank"
              title="Edit in new tab"
            >
              <PencilIcon class="h-4 w-4" />
              <span class="ml-1">Edit</span>
            </a>
          </span>
          <button
            v-if="message.role !== 'function'"
            class="text-blue-500 hover:text-blue-700 flex items-center"
            title="Regenerate from this message"
            @click="$emit('regenerateFromMessage', message.id)"
          >
            <ArrowPathIcon class="h-4 w-4" />
            <span class="ml-1">Regenerate</span>
          </button>
        </span>
      </span>
    </p>

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
    </template>

    <div v-if="message.functionCall">
      <b>> {{ message.functionCall?.name }} </b>
      <p v-if="message.functionCall?.name === 'memory_search'">
        Search: "{{ message.functionCall?.arguments?.search }}"
      </p>
      <BaseEditor
        v-else-if="message.functionCall?.name === 'sql_query'"
        :modelValue="message.functionCall?.arguments?.query"
        :read-only="true"
      ></BaseEditor>
      <BaseEditorPreview
        v-else-if="message.functionCall?.name === 'submit'"
        :sqlQuery="message.functionCall?.arguments?.query"
        :database-id="databaseSelectedId"
      ></BaseEditorPreview>
      <div v-else-if="message?.functionCall?.name === 'render_echarts'">
        <Echart :option="message.functionCall?.arguments?.chart_options" />
      </div>
      <pre v-else class="arguments">{{ message.functionCall?.arguments }}</pre>
    </div>
  </div>
</template>

<script lang="ts">
import BaseTable from '@/components/BaseTable.vue'
import yaml from 'js-yaml'
import axios from '@/plugins/axios'
import BaseEditor from '@/components/BaseEditor.vue'
import BaseEditorPreview from '@/components/BaseEditorPreview.vue'
import { marked } from 'marked'
import { ArrowPathIcon, PencilIcon, PencilSquareIcon } from '@heroicons/vue/24/outline'
import Echart from '@/components/Echart.vue'

// Get databaseId from store
import { useDatabases } from '../stores/databases'
export const { databaseSelectedId } = useDatabases()

export default {
  components: {
    BaseTable,
    BaseEditor,
    BaseEditorPreview,
    ArrowPathIcon,
    PencilIcon,
    PencilSquareIcon,
    Echart
  },
  props: {
    message: {
      type: Object,
      required: true
    }
  },
  emits: ['editInlineClick', 'regenerateFromMessage'],
  data() {
    return {
      sqlResult: [] as Array<{
        [key: string]: string | number | boolean | null
      }>,
      sqlCount: 0,
      databaseSelectedId
    }
  },
  methods: {
    editInline() {
      this.$emit('editInlineClick', this.message.functionCall?.arguments?.query)
    },
    async executeSql(sql: string) {
      try {
        const result = await axios.post('/api/query/_run', {
          query: sql,
          databaseId: databaseSelectedId.value
        })
        console.log(result.data.rows)
        this.sqlResult = result.data.rows
        this.sqlCount = result.data.count
      } catch (error) {
        console.error('Error executing SQL:', error)
      }
    },
    renderMarkdown(text: string) {
      return marked(text)
    }
  },
  mounted() {
    this.parsedText.forEach((part) => {
      if (part.type === 'yml-graph' || part.type === 'yaml-graph') {
        this.executeSql(part.content.sql)
      }
    })
  },
  computed: {
    parsedText() {
      const regex = /```((?:sql|json|error|ya?ml-graph))\s*([\s\S]*?)\s*```/g
      let match
      let lastIndex = 0
      const parts = []

      while ((match = regex.exec(this.message.content)) !== null) {
        if (match.index > lastIndex) {
          parts.push({
            type: 'text',
            content: this.message.content.slice(lastIndex, match.index)
          })
        }

        let type = match[1]
        let content
        if (type === 'json') {
          content = JSON.parse(match[2].trim())
        } else if (type === 'sql') {
          content = match[2].trim()
        } else if (type === 'yml-graph' || type === 'yaml-graph') {
          // TODO: verify that this is a valid graph yaml
          content = yaml.load(match[2].trim())
          console.log('content', content)
        } else if (type === 'error') {
          content = match[2]
        } else {
          throw new Error(`Unknown type ${type}`)
        }

        parts.push({
          type: type,
          content: content
        })

        lastIndex = match.index + match[0].length
      }

      if (lastIndex < this.message.content?.length) {
        parts.push({
          type: 'text',
          content: this.message.content.slice(lastIndex)
        })
      }

      return parts
    }
  }
}
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