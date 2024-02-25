<template>
  <div
    class="message-display px-4 py-4 mb-2 rounded-lg bg-gray-100"
    :class="{ 'bg-gray-300': message.display === false }"
  >
    <!-- if message.display = hide, then show as light gray -->
    <p class="font-bold">
      <span class="flex justify-between items-center w-full">
        {{ message.role }}
        <!-- Link to /query/{{ message.queryId }} if message.queryId is defined -->
        <span v-if="message.queryId">
          <button class="text-blue-500" @click="editInline">Edit inline</button>
          /
          <a :href="`/query/${message.queryId}`" class="text-blue-500" target="_blank"> Edit </a>
        </span>
      </span>
    </p>

    <div v-if="message.functionCall">
      <b>> {{ message.functionCall?.name }} </b>
      <p v-if="message.functionCall?.name === 'MEMORY_SEARCH'">
        Search: "{{ message.functionCall?.arguments?.search }}"
      </p>
      <div v-else-if="message.functionCall?.name === 'PLOT_WIDGET' && databaseSelectedId">
        <Widget
          :database-id="databaseSelectedId"
          :sql="message.functionCall?.arguments?.sql"
          :visualisationParams="visualisationParams"
        ></Widget>
      </div>
      <BaseEditor
        v-else-if="message.functionCall?.name === 'SQL_QUERY'"
        :modelValue="message.functionCall?.arguments?.query"
        :read-only="true"
      ></BaseEditor>
      <BaseEditorPreview
        v-else-if="message.functionCall?.name === 'SUBMIT'"
        :sqlQuery="message.functionCall?.arguments?.query"
      ></BaseEditorPreview>
      <pre v-else class="arguments">{{ message.functionCall?.arguments }}</pre>
    </div>

    <template v-for="(part, index) in parsedText">
      <span style="white-space: pre-wrap" v-if="part.type === 'text'" :key="`text-${index}`">
        {{ part.content }}
      </span>
      <BaseEditor
        v-if="part.type === 'sql'"
        :modelValue="part.content"
        :read-only="true"
        :key="`sql-${index}`"
      ></BaseEditor>
      <BaseTable v-if="part.type === 'json'" :data="part.content" :key="`json-${index}`" />
      <BaseBuilder
        v-if="(part.type === 'yml-graph' || part.type === 'yaml-graph') && sqlResult"
        :context="part.content"
        :count="sqlCount"
        :data="sqlResult"
      ></BaseBuilder>
    </template>
  </div>
</template>

<script lang="ts">
import BaseTable from '@/components/BaseTable.vue'
import BaseBuilder from '@/components/BaseBuilder.vue'
import Widget from '@/components/Widget.vue'
import yaml from 'js-yaml'
import axios from 'axios'
import BaseEditor from '@/components/BaseEditor.vue'
import BaseEditorPreview from '@/components/BaseEditorPreview.vue'

// Get databaseId from store
import { useDatabases } from '../stores/databases'
export const { databaseSelectedId } = useDatabases()

export default {
  components: {
    BaseTable,
    BaseEditor,
    BaseEditorPreview,
    BaseBuilder,
    Widget
  },
  props: {
    message: {
      type: Object,
      required: true
    }
  },
  emits: ['editInlineClick'],
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
    visualisationParams() {
      if (this.message.functionCall?.name !== 'PLOT_WIDGET') return
      const params = this.message.functionCall?.arguments
      return {
        ...params?.params,
        caption: params?.caption,
        type: params?.outputType
      }
    },
    parsedText() {
      const regex = /```((?:sql|json|ya?ml-graph))\s*([\s\S]*?)\s*```/g
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
</style>
