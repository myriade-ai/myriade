import { Node, mergeAttributes } from '@tiptap/core'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import ChartNodeView from './ChartNodeView.vue'

export interface ChartNodeAttrs {
  chartId: string
}

export const ChartNode = Node.create({
  name: 'chartNode',

  group: 'block',

  atom: true, // Treated as a single unit, not editable internally

  addAttributes() {
    return {
      chartId: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-chart-id'),
        renderHTML: (attributes) => {
          if (!attributes.chartId) {
            return {}
          }
          return {
            'data-chart-id': attributes.chartId
          }
        }
      }
    }
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-type="chart-node"]',
        getAttrs: (element) => {
          if (typeof element === 'string') return false
          const chartId = element.getAttribute('data-chart-id')
          if (!chartId) return false
          return { chartId }
        }
      }
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes(HTMLAttributes, { 'data-type': 'chart-node' })]
  },

  addNodeView() {
    return VueNodeViewRenderer(ChartNodeView)
  }
})
