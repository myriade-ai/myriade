import { Node, mergeAttributes } from '@tiptap/core'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import AgentMentionNodeView from './AgentMentionNodeView.vue'

export interface AgentMentionNodeAttrs {
  agentId: string
  label: string
}

export const AgentMentionNode = Node.create({
  name: 'agentMentionNode',

  group: 'inline',

  inline: true,

  atom: true, // Treated as a single unit, not editable internally

  addAttributes() {
    return {
      agentId: {
        default: null,
        renderHTML: (attributes) => {
          if (!attributes.agentId) {
            return {}
          }
          return {
            'data-agent-id': attributes.agentId
          }
        }
      },
      label: {
        default: 'Myriade Agent',
        renderHTML: (attributes) => {
          return {
            'data-agent-label': attributes.label
          }
        }
      }
    }
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-type="agent-mention"]',
        getAttrs: (element) => {
          if (typeof element === 'string') return false
          const agentId = element.getAttribute('data-agent-id')
          const label = element.getAttribute('data-agent-label')
          if (!agentId) return false
          return { agentId, label: label || 'Myriade Agent' }
        }
      }
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return ['span', mergeAttributes(HTMLAttributes, { 'data-type': 'agent-mention' })]
  },

  addNodeView() {
    return VueNodeViewRenderer(AgentMentionNodeView)
  }
})
