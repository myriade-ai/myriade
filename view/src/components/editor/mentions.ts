import { computePosition, flip, shift } from '@floating-ui/dom'
import type { Editor } from '@tiptap/core'
import { posToDOMRect, VueRenderer } from '@tiptap/vue-3'
import type { SuggestionKeyDownProps, SuggestionOptions, SuggestionProps } from '@tiptap/suggestion'
import MentionSuggestion from '../MentionSuggestion.vue'
import type { MentionItem } from '@/composables/useDocumentMentions'

// Helper function to update popup position using Floating UI
const updatePosition = (editor: Editor, element: HTMLElement) => {
  const virtualElement = {
    getBoundingClientRect: () =>
      posToDOMRect(editor.view, editor.state.selection.from, editor.state.selection.to)
  }

  computePosition(virtualElement, element, {
    placement: 'bottom-start',
    strategy: 'absolute',
    middleware: [shift(), flip()]
  }).then(({ x, y, strategy }) => {
    element.style.position = strategy
    element.style.left = `${x}px`
    element.style.top = `${y}px`
  })
}

export const mentionSuggestion: Omit<SuggestionOptions, 'editor'> = {
  // Return empty items - the component will handle fetching with TanStack Query
  items: () => [],

  render: () => {
    let component: VueRenderer | null = null
    let popup: HTMLElement | null = null

    return {
      onStart: (props: SuggestionProps) => {
        // Define the command handler that inserts the custom node
        const selectItem = (item: MentionItem) => {
          // Insert our custom node instead of a simple mention
          const nodeType = item.type === 'query' ? 'queryNode' : 'chartNode'
          const attrName = item.type === 'query' ? 'queryId' : 'chartId'

          // Use editor commands directly
          const { view } = props.editor
          const { state, dispatch } = view
          const { tr } = state

          // Delete the @ mention text
          const from = props.range.from
          const to = props.range.to
          tr.delete(from, to)

          // Insert our custom node
          const nodeSchema = props.editor.schema.nodes[nodeType]
          if (nodeSchema) {
            const node = nodeSchema.create({
              [attrName]: item.id
            })
            tr.insert(from, node)
            dispatch(tr)
          }
        }

        component = new VueRenderer(MentionSuggestion, {
          props: {
            query: props.query,
            command: selectItem
          },
          editor: props.editor
        })

        if (!props.clientRect) {
          return
        }

        const element = component.element as HTMLElement
        if (!element) {
          return
        }

        popup = element
        popup.style.position = 'absolute'
        document.body.appendChild(popup)

        updatePosition(props.editor, popup)
      },

      onUpdate(props: SuggestionProps) {
        if (component) {
          component.updateProps({
            query: props.query
          })
        }

        if (!props.clientRect || !popup) {
          return
        }

        updatePosition(props.editor, popup)
      },

      onKeyDown(props: SuggestionKeyDownProps): boolean {
        if (props.event.key === 'Escape') {
          if (popup && popup.parentNode) {
            popup.parentNode.removeChild(popup)
            popup = null
          }
          if (component) {
            component.destroy()
            component = null
          }
          return true
        }

        // Forward keyboard events to the component
        return component?.ref?.onKeyDown(props) ?? false
      },

      onExit() {
        if (popup && popup.parentNode) {
          popup.parentNode.removeChild(popup)
          popup = null
        }
        if (component) {
          component.destroy()
          component = null
        }
      }
    }
  }
}
