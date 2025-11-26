import { Node, mergeAttributes } from '@tiptap/core'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import UserMentionNodeView from './UserMentionNodeView.vue'

export interface UserMentionNodeAttrs {
  userId: string
  label?: string
}

export const UserMentionNode = Node.create({
  name: 'userMentionNode',

  group: 'inline',

  inline: true,

  atom: true, // Treated as a single unit, not editable internally

  addAttributes() {
    return {
      userId: {
        default: null,
        renderHTML: (attributes) => {
          if (!attributes.userId) {
            return {}
          }
          return {
            'data-user-id': attributes.userId
          }
        }
      },
      label: {
        default: null,
        renderHTML: (attributes) => {
          return {
            'data-user-label': attributes.label
          }
        }
      }
    }
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-type="user-mention"]',
        getAttrs: (element) => {
          if (typeof element === 'string') return false
          const userId = element.getAttribute('data-user-id')
          const label = element.getAttribute('data-user-label')
          if (!userId) return false
          return { userId, label }
        }
      }
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return ['span', mergeAttributes(HTMLAttributes, { 'data-type': 'user-mention' })]
  },

  addNodeView() {
    return VueNodeViewRenderer(UserMentionNodeView)
  }
})
