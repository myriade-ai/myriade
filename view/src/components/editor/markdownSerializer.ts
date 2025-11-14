import { Node as ProseMirrorNode } from '@tiptap/pm/model'

/**
 * Custom markdown serializer that handles Query and Chart nodes
 * Converts Tiptap/ProseMirror document to markdown with <QUERY:uuid> and <CHART:uuid> tags
 */
export function serializeToMarkdown(doc: ProseMirrorNode): string {
  let markdown = ''

  doc.descendants((node) => {
    // Handle query nodes
    if (node.type.name === 'queryNode') {
      const queryId = node.attrs.queryId
      if (queryId) {
        markdown += `<QUERY:${queryId}>\n\n`
      }
      return false // Don't traverse into this node
    }

    // Handle chart nodes
    if (node.type.name === 'chartNode') {
      const chartId = node.attrs.chartId
      if (chartId) {
        markdown += `<CHART:${chartId}>\n\n`
      }
      return false // Don't traverse into this node
    }

    // Handle paragraph
    if (node.type.name === 'paragraph') {
      if (node.textContent) {
        markdown += serializeInlineContent(node) + '\n\n'
      }
      return false
    }

    // Handle headings
    if (node.type.name === 'heading') {
      const level = node.attrs.level || 1
      markdown += '#'.repeat(level) + ' ' + serializeInlineContent(node) + '\n\n'
      return false
    }

    // Handle bullet list
    if (node.type.name === 'bulletList') {
      node.forEach((child) => {
        if (child.type.name === 'listItem') {
          markdown += '- ' + serializeInlineContent(child) + '\n'
        }
      })
      markdown += '\n'
      return false
    }

    // Handle ordered list
    if (node.type.name === 'orderedList') {
      let index = 1
      node.forEach((child) => {
        if (child.type.name === 'listItem') {
          markdown += `${index}. ` + serializeInlineContent(child) + '\n'
          index++
        }
      })
      markdown += '\n'
      return false
    }

    // Handle blockquote
    if (node.type.name === 'blockquote') {
      node.forEach((child) => {
        const content = serializeInlineContent(child)
        if (content) {
          markdown += '> ' + content + '\n'
        }
      })
      markdown += '\n'
      return false
    }

    // Handle code block
    if (node.type.name === 'codeBlock') {
      const lang = node.attrs.language || ''
      markdown += '```' + lang + '\n' + node.textContent + '\n```\n\n'
      return false
    }

    // Handle horizontal rule
    if (node.type.name === 'horizontalRule') {
      markdown += '---\n\n'
      return false
    }

    // Handle hard break
    if (node.type.name === 'hardBreak') {
      markdown += '  \n'
      return false
    }

    return true
  })

  return markdown.trim()
}

/**
 * Serialize inline content (text with marks like bold, italic, etc.)
 */
function serializeInlineContent(node: ProseMirrorNode): string {
  let text = ''

  node.descendants((child) => {
    if (child.isText) {
      let content = child.text || ''

      // Apply marks in the correct order
      if (child.marks && child.marks.length > 0) {
        child.marks.forEach((mark) => {
          switch (mark.type.name) {
            case 'bold':
              content = `**${content}**`
              break
            case 'italic':
              content = `*${content}*`
              break
            case 'code':
              content = `\`${content}\``
              break
            case 'strike':
              content = `~~${content}~~`
              break
            case 'link':
              const href = mark.attrs.href
              content = `[${content}](${href})`
              break
          }
        })
      }

      text += content
    }

    return true
  })

  return text
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
    (match, queryMatch, queryId, chartMatch, chartId) => {
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
