<script lang="ts">
import Chart from '@/components/Chart.vue'
import { Card, CardContent } from '@/components/ui/card'
import { NodeViewWrapper } from '@tiptap/vue-3'
import { defineComponent } from 'vue'

export default defineComponent({
  components: {
    NodeViewWrapper,
    Chart,
    Card,
    CardContent
  },
  props: ['node', 'updateAttributes', 'deleteNode', 'editor', 'extension', 'getPos', 'selected'],
  methods: {
    handleDelete() {
      this.deleteNode()
    }
  }
})
</script>

<template>
  <NodeViewWrapper class="chart-node-wrapper my-4">
    <Card class="p-0 pb-3.5 pt-1">
      <CardContent>
        <Chart :chartId="node.attrs.chartId" />
      </CardContent>
    </Card>
  </NodeViewWrapper>
</template>

<style scoped>
.chart-node-wrapper {
  cursor: default;
}
</style>
