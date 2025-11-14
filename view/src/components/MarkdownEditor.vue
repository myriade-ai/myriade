<template>
  <div class="unified-markdown-editor">
    <EditorContent :editor="editor" class="tiptap-editor-content" />
  </div>
</template>

<script setup lang="ts">
import { EditorContent, useEditor } from '@tiptap/vue-3'
import { onUnmounted, ref, watch } from 'vue'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Mention from '@tiptap/extension-mention'
import { QueryNode } from './editor/QueryNode'
import { ChartNode } from './editor/ChartNode'
import { serializeToMarkdown } from './editor/markdownSerializer'
import { mentionSuggestion } from './editor/mentions'

interface Props {
  modelValue: string
  placeholder?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Start writing... Use @ to mention queries or charts',
  disabled: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const isActivelyEditing = ref(false)
const editingTimeout = ref<number | null>(null)

// Parse markdown content to HTML for initial load
function markdownToHTML(markdown: string): string {
  if (!markdown) return ''

  // Split by lines and process
  const lines = markdown.split('\n')
  const htmlParts: string[] = []
  let inParagraph = false
  let paragraphContent: string[] = []

  const flushParagraph = () => {
    if (paragraphContent.length > 0) {
      const content = paragraphContent
        .join(' ')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code>$1</code>')
      htmlParts.push(`<p>${content}</p>`)
      paragraphContent = []
    }
    inParagraph = false
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trimmedLine = line.trim()

    // Check for custom tags
    const queryMatch = trimmedLine.match(/^<QUERY:([^>]+)>$/)
    const chartMatch = trimmedLine.match(/^<CHART:([^>]+)>$/)

    if (queryMatch) {
      flushParagraph()
      const html = `<div data-type="query-node" data-query-id="${queryMatch[1].trim()}"></div>`
      htmlParts.push(html)
      continue
    }

    if (chartMatch) {
      flushParagraph()
      htmlParts.push(`<div data-type="chart-node" data-chart-id="${chartMatch[1].trim()}"></div>`)
      continue
    }

    // Check for headings
    if (trimmedLine.startsWith('### ')) {
      flushParagraph()
      htmlParts.push(`<h3>${trimmedLine.substring(4)}</h3>`)
      continue
    }

    if (trimmedLine.startsWith('## ')) {
      flushParagraph()
      htmlParts.push(`<h2>${trimmedLine.substring(3)}</h2>`)
      continue
    }

    if (trimmedLine.startsWith('# ')) {
      flushParagraph()
      htmlParts.push(`<h1>${trimmedLine.substring(2)}</h1>`)
      continue
    }

    // Check for list items
    if (trimmedLine.startsWith('- ')) {
      flushParagraph()
      htmlParts.push(`<ul><li>${trimmedLine.substring(2)}</li></ul>`)
      continue
    }

    // Check for horizontal rule
    if (trimmedLine === '---') {
      flushParagraph()
      htmlParts.push('<hr>')
      continue
    }

    // Empty line - end paragraph
    if (trimmedLine === '') {
      flushParagraph()
      continue
    }

    // Regular text - add to paragraph
    if (!inParagraph) {
      inParagraph = true
    }
    paragraphContent.push(trimmedLine)
  }

  // Flush any remaining paragraph
  flushParagraph()

  return htmlParts.join('')
}

// Initialize Tiptap editor
const editor = useEditor({
  extensions: [
    StarterKit,
    Placeholder.configure({
      placeholder: props.placeholder
    }),
    Mention.configure({
      HTMLAttributes: {
        class: 'mention',
        'data-type': 'mention',
        'data-id': null
      },
      renderLabel: ({ node }) => {
        return node.attrs.id || '@mention'
      },
      suggestion: mentionSuggestion
    }),
    QueryNode,
    ChartNode
  ],
  content: (() => {
    const html = props.modelValue ? markdownToHTML(props.modelValue) : ''
    return html
  })(),
  editorProps: {
    attributes: {
      class: 'prose prose-sm max-w-none focus:outline-none min-h-[200px] p-4 rounded-lg'
    }
  },
  onUpdate: ({ editor }) => {
    // Mark as actively editing and emit immediately
    isActivelyEditing.value = true

    // Clear any existing editing timeout
    if (editingTimeout.value !== null) {
      clearTimeout(editingTimeout.value)
    }

    // Set timeout to mark as no longer actively editing after 3 seconds of inactivity
    // This gives enough time for saves to complete and caches to update
    editingTimeout.value = window.setTimeout(() => {
      isActivelyEditing.value = false
    }, 3000)

    // Emit change immediately for parent to handle debouncing
    const markdown = serializeToMarkdown(editor.state.doc)
    if (markdown !== props.modelValue) {
      emit('update:modelValue', markdown)
    }
  },
  editable: !props.disabled
})

// Update editor content when prop changes (but not while actively editing)
watch(
  () => props.modelValue,
  (newValue) => {
    if (!editor.value) return

    // Don't sync content during active editing to prevent content reversion
    if (isActivelyEditing.value) {
      console.log('Skipping editor sync - user is actively editing')
      return
    }

    const currentMarkdown = serializeToMarkdown(editor.value.state.doc)
    if (newValue !== currentMarkdown) {
      console.log('Syncing editor content with props:', {
        from: currentMarkdown.substring(0, 50),
        to: newValue.substring(0, 50)
      })
      const html = markdownToHTML(newValue)
      editor.value.commands.setContent(html)
    }
  },
  { immediate: true }
)

// Watch disabled prop
watch(
  () => props.disabled,
  (disabled) => {
    if (editor.value) {
      editor.value.setEditable(!disabled)
    }
  }
)

// Clean up timeout and editor on unmount
onUnmounted(() => {
  if (editingTimeout.value !== null) {
    clearTimeout(editingTimeout.value)
  }
  if (editor.value) {
    editor.value.destroy()
  }
})
</script>

<style>
/* Tiptap editor styles */
.tiptap-editor-content .ProseMirror {
  outline: none;
}

.tiptap-editor-content .ProseMirror p.is-editor-empty:first-child::before {
  color: #adb5bd;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

/* Prose styles for markdown rendering */
.tiptap-editor-content .ProseMirror {
  color: #374151;
}

.tiptap-editor-content .ProseMirror h1 {
  font-size: 1.875rem;
  font-weight: 700;
  margin-top: 2rem;
  margin-bottom: 1rem;
  line-height: 1.2;
}

.tiptap-editor-content .ProseMirror h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  line-height: 1.3;
}

.tiptap-editor-content .ProseMirror h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.tiptap-editor-content .ProseMirror p {
  margin-bottom: 1rem;
  line-height: 1.75;
}

.tiptap-editor-content .ProseMirror ul,
.tiptap-editor-content .ProseMirror ol {
  margin-bottom: 1rem;
  padding-left: 1.5rem;
}

.tiptap-editor-content .ProseMirror li {
  margin-bottom: 0.5rem;
}

.tiptap-editor-content .ProseMirror code {
  background-color: #f3f4f6;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.tiptap-editor-content .ProseMirror pre {
  background-color: #1f2937;
  color: #f9fafb;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin-bottom: 1rem;
}

.tiptap-editor-content .ProseMirror pre code {
  background-color: transparent;
  padding: 0;
  color: inherit;
}

.tiptap-editor-content .ProseMirror blockquote {
  border-left: 4px solid #e5e7eb;
  padding-left: 1rem;
  margin-left: 0;
  margin-bottom: 1rem;
  color: #6b7280;
}

.tiptap-editor-content .ProseMirror hr {
  border: none;
  border-top: 2px solid #e5e7eb;
  margin: 2rem 0;
}

.tiptap-editor-content .ProseMirror strong {
  font-weight: 600;
}

.tiptap-editor-content .ProseMirror em {
  font-style: italic;
}

.tiptap-editor-content .ProseMirror a {
  color: #3b82f6;
  text-decoration: underline;
}

.tiptap-editor-content .ProseMirror a:hover {
  color: #2563eb;
}

/* Node selection styles */
.tiptap-editor-content .ProseMirror .ProseMirror-selectednode {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
  border-radius: 0.5rem;
}

/* Custom mention dropdown positioning */
</style>
