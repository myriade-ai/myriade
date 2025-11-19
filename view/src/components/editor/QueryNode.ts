import { Node, mergeAttributes } from '@tiptap/core'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import QueryNodeView from './QueryNodeView.vue'

export interface QueryNodeAttrs {
  queryId: string
}

export const QueryNode = Node.create({
  name: 'queryNode',

  group: 'block',

  atom: true, // Treated as a single unit, not editable internally

  addAttributes() {
    return {
      queryId: {
        default: null,
        renderHTML: (attributes) => {
          if (!attributes.queryId) {
            return {}
          }
          return {
            'data-query-id': attributes.queryId
          }
        }
      }
    }
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-type="query-node"]',
        getAttrs: (element) => {
          if (typeof element === 'string') return false
          const queryId = element.getAttribute('data-query-id')
          if (!queryId) return false
          return { queryId }
        }
      }
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes(HTMLAttributes, { 'data-type': 'query-node' })]
  },

  addNodeView() {
    return VueNodeViewRenderer(QueryNodeView)
  }
})
