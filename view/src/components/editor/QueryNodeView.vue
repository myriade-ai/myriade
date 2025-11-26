<script lang="ts">
import { defineComponent } from 'vue'
import { Card, CardContent } from '@/components/ui/card'
import { NodeViewWrapper } from '@tiptap/vue-3'
import DataTable from '../DataTable.vue'

export default defineComponent({
  name: 'QueryNodeView',
  components: {
    NodeViewWrapper,
    Card,
    CardContent,
    DataTable
  },
  props: {
    node: {
      type: Object,
      required: true
    },
    updateAttributes: Function,
    deleteNode: Function,
    editor: Object,
    extension: Object,
    getPos: Function,
    selected: Boolean
  },
  data() {
    return {
      queryData: null as any,
      loading: true,
      error: null as string | null
    }
  },
  async mounted() {
    try {
      const { useQueryEditor } = await import('@/composables/useQueryEditor')
      const { fetchQuery, fetchQueryResults } = useQueryEditor()

      const query = await fetchQuery(this.node.attrs.queryId)
      const result = await fetchQueryResults(this.node.attrs.queryId)

      this.queryData = {
        title: query.title || 'Untitled Query',
        sql: query.sql,
        rows: result.rows,
        columns: result.columns || [],
        count: result.count,
        is_favorite: query.is_favorite
      }
      this.loading = false
    } catch (error) {
      console.error('Error fetching query data:', error)
      this.error = 'Failed to load query'
      this.loading = false
    }
  }
})
</script>

<template>
  <NodeViewWrapper class="query-node-wrapper my-4">
    <Card class="p-0 pb-3.5 pt-1">
      <CardContent>
        <div v-if="loading" class="p-4 text-center text-muted-foreground">Loading query...</div>
        <div v-else-if="error" class="p-4 text-center text-red-500">
          {{ error }}
        </div>
        <div v-else-if="queryData" class="space-y-4">
          <div class="pb-3 border-b">
            <h3 class="font-semibold text-lg text-foreground">{{ queryData.title }}</h3>
          </div>
          <div class="bg-muted p-3 rounded font-mono text-sm">
            {{ queryData.sql }}
          </div>
          <DataTable :data="queryData.rows" :count="queryData.count" :columns="queryData.columns" />
        </div>
      </CardContent>
    </Card>
  </NodeViewWrapper>
</template>

<style scoped>
.query-node-wrapper {
  cursor: default;
}
</style>
