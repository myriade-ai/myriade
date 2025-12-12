import type { Editor } from '@tiptap/core'

/**
 * Get markdown from editor using tiptap-markdown's built-in serializer
 * This handles tables, lists, and all standard markdown automatically
 */
export function serializeToMarkdown(editor: Editor): string {
  // Use tiptap-markdown's built-in serialization
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const markdown = (editor.storage as any).markdown.getMarkdown() as string

  return markdown.trim()
}

/**
 * Parse markdown with <QUERY:uuid> and <CHART:uuid> tags
 * Strategy: Replace custom tags with placeholders, let markdown parse, then restore
 */
export function parseMarkdownToJSON(markdown: string): string {
  if (!markdown || markdown.trim() === '') {
    return ''
  }

  // Store custom tags with unique placeholders
  const customTags: Array<{ placeholder: string; type: string; id: string }> = []
  let counter = 0

  // Replace <QUERY:id> and <CHART:id> with placeholders
  let processedMarkdown = markdown.replace(
    /(<QUERY:([^>]+)>)|(<CHART:([^>]+)>)/g,
    (_match, queryMatch, queryId, chartMatch, chartId) => {
      const placeholder = `__CUSTOM_NODE_${counter}__`
      counter++

      if (queryMatch) {
        customTags.push({
          placeholder,
          type: 'query',
          id: queryId.trim()
        })
      } else if (chartMatch) {
        customTags.push({
          placeholder,
          type: 'chart',
          id: chartId.trim()
        })
      }

      // Return placeholder on its own line to preserve block structure
      return `\n\n${placeholder}\n\n`
    }
  )

  // Clean up extra newlines
  processedMarkdown = processedMarkdown.replace(/\n{3,}/g, '\n\n').trim()

  // Return the processed markdown with custom data attached
  // The Markdown extension will parse this, and we'll need to post-process it
  return processedMarkdown
}
