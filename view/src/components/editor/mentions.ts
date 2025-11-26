import { computePosition, flip, shift } from '@floating-ui/dom'
import type { Editor } from '@tiptap/core'
import { posToDOMRect, VueRenderer } from '@tiptap/vue-3'
import type { SuggestionKeyDownProps, SuggestionOptions, SuggestionProps } from '@tiptap/suggestion'
import type { Component } from 'vue'
import MentionSuggestion from '../MentionSuggestion.vue'
import AgentMentionSuggestion from '../AgentMentionSuggestion.vue'

// Generic mention item type that can be extended
export interface BaseMentionItem {
  id: string
  type: string
  label?: string
}

// Mention types that can be enabled
export interface MentionOptions {
  enableQueryMentions?: boolean
  enableChartMentions?: boolean
  enableAgentMention?: boolean
}

// Type for custom select handler
export type MentionSelectHandler = (item: BaseMentionItem, props: SuggestionProps) => void

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

// Default select handler for query/chart nodes (used in document editor)
const defaultSelectHandler: MentionSelectHandler = (item, props) => {
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

// Text mention select handler (inserts plain text mention like @myriade-agent)
export const textMentionSelectHandler: MentionSelectHandler = (item, props) => {
  const { view } = props.editor
  const { state, dispatch } = view
  const { tr } = state

  // Delete the @ mention text
  const from = props.range.from
  const to = props.range.to
  tr.delete(from, to)

  // Insert plain text mention
  const mentionText = item.label || `@${item.id}`
  tr.insertText(mentionText, from)
  dispatch(tr)
}

// Agent mention select handler (inserts an AgentMentionNode for styled display and <AGENT:id> serialization)
export const agentMentionSelectHandler: MentionSelectHandler = (item, props) => {
  const { view } = props.editor
  const { state, dispatch } = view
  const { tr } = state

  // Delete the @ mention text
  const from = props.range.from
  const to = props.range.to
  tr.delete(from, to)

  // Insert agentMentionNode
  const nodeSchema = props.editor.schema.nodes['agentMentionNode']
  if (nodeSchema) {
    const node = nodeSchema.create({
      agentId: item.id,
      label: item.label || 'Myriade Agent'
    })
    tr.insert(from, node)
    dispatch(tr)
  }
}

/**
 * Factory function to create a mention suggestion configuration
 * @param suggestionComponent - Vue component to render the suggestion dropdown
 * @param onSelect - Optional custom select handler (defaults to inserting query/chart nodes)
 */
export function createMentionSuggestion(
  suggestionComponent: Component = MentionSuggestion,
  onSelect?: MentionSelectHandler
): Omit<SuggestionOptions, 'editor'> {
  const selectHandler = onSelect || defaultSelectHandler

  return {
    // Return empty items - the component will handle fetching with TanStack Query
    items: () => [],

    render: () => {
      let component: VueRenderer | null = null
      let popup: HTMLElement | null = null
      // Keep track of the latest props to ensure range is up-to-date when selecting
      let latestProps: SuggestionProps | null = null

      return {
        onStart: (props: SuggestionProps) => {
          latestProps = props

          // Define the command handler that uses the latest props
          const selectItem = (item: BaseMentionItem) => {
            if (latestProps) {
              selectHandler(item, latestProps)
            }
          }

          component = new VueRenderer(suggestionComponent, {
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
          // Always update latestProps to keep range current
          latestProps = props

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
}

// Default export for backward compatibility (query/chart mentions)
export const mentionSuggestion = createMentionSuggestion(MentionSuggestion)

/**
 * Get the appropriate suggestion component based on enabled mention types
 */
export function getSuggestionComponent(options: MentionOptions): Component | null {
  const { enableQueryMentions, enableChartMentions, enableAgentMention } = options

  // If query or chart mentions enabled, use MentionSuggestion (handles both)
  if (enableQueryMentions || enableChartMentions) {
    return MentionSuggestion
  }

  // If only agent mention enabled, use AgentMentionSuggestion
  if (enableAgentMention) {
    return AgentMentionSuggestion
  }

  // No mentions enabled
  return null
}

/**
 * Get the appropriate select handler based on enabled mention types
 */
export function getSelectHandler(options: MentionOptions): MentionSelectHandler | undefined {
  const { enableQueryMentions, enableChartMentions, enableAgentMention } = options

  // If query or chart mentions enabled, use default handler (query/chart nodes)
  if (enableQueryMentions || enableChartMentions) {
    return undefined // Uses defaultSelectHandler in createMentionSuggestion
  }

  // If only agent mention enabled, use agent handler
  if (enableAgentMention) {
    return agentMentionSelectHandler
  }

  return undefined
}
