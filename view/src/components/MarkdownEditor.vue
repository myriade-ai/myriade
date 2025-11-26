<template>
  <div class="unified-markdown-editor">
    <EditorContent :editor="editor" class="tiptap-editor-content" />

    <!-- BubbleMenu for text selection -->
    <BubbleMenu
      v-if="editor && showBubbleMenu"
      :editor="editor"
      :should-show="shouldShowMenu"
      class="bubble-menu-container"
    >
      <div
        class="flex items-center gap-1 bg-popover border border-border rounded-lg shadow-lg px-2 py-1.5"
      >
        <Button @click="handleImproveWriting" variant="ghost" size="sm" class="gap-2 text-sm h-8">
          <SparklesIcon class="h-4 w-4" />
          Improve writing
        </Button>
        <DropdownMenu v-model:open="showAskInput">
          <DropdownMenuTrigger as-child>
            <Button variant="ghost" size="sm" class="text-sm h-8"> Ask AI </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" class="w-[320px]">
            <!-- Input section -->
            <div class="py-2">
              <input
                ref="bubbleInputRef"
                v-model="bubbleQuestion"
                type="text"
                placeholder="Ask AI anything..."
                class="w-full border-0 focus:ring-0 text-sm outline-none"
                @keydown.enter="handleAskQuestion"
                @keydown.escape="handleCloseBubble"
                @click.stop
              />
            </div>

            <DropdownMenuSeparator />

            <!-- Suggested actions -->
            <DropdownMenuLabel class="text-xs">Suggested</DropdownMenuLabel>
            <DropdownMenuGroup>
              <DropdownMenuItem @click="handleSuggestedAction('improve')">
                <SparklesIcon class="h-4 w-4 text-purple-500" />
                <span>Improve writing</span>
              </DropdownMenuItem>
              <DropdownMenuItem @click="handleSuggestedAction('fix-grammar')">
                <svg
                  class="h-4 w-4 text-green-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                <span>Fix spelling & grammar</span>
              </DropdownMenuItem>
            </DropdownMenuGroup>

            <DropdownMenuSeparator />

            <!-- Edit section -->
            <DropdownMenuLabel class="text-xs">Edit</DropdownMenuLabel>
            <DropdownMenuGroup>
              <DropdownMenuItem @click="handleSuggestedAction('make-shorter')">
                <svg
                  class="h-4 w-4 text-blue-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 6h16M4 12h8m-8 6h16"
                  />
                </svg>
                <span>Make shorter</span>
              </DropdownMenuItem>
              <DropdownMenuItem @click="handleSuggestedAction('simplify')">
                <svg
                  class="h-4 w-4 text-purple-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
                <span>Simplify language</span>
              </DropdownMenuItem>
              <DropdownMenuItem @click="handleSuggestedAction('make-longer')">
                <svg
                  class="h-4 w-4 text-orange-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 6h16M4 12h16m-7 6h7"
                  />
                </svg>
                <span>Make longer</span>
              </DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </BubbleMenu>
  </div>
</template>

<script setup lang="ts">
import { EditorContent, useEditor } from '@tiptap/vue-3'
import { BubbleMenu } from '@tiptap/vue-3/menus'
import { onUnmounted, ref, watch, nextTick, computed } from 'vue'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Mention from '@tiptap/extension-mention'
import { QueryNode } from './editor/QueryNode'
import { ChartNode } from './editor/ChartNode'
import { AgentMentionNode } from './editor/AgentMentionNode'
import { UserMentionNode } from './editor/UserMentionNode'
import { serializeToMarkdown } from './editor/markdownSerializer'
import {
  createMentionSuggestion,
  getSuggestionComponent,
  getSelectHandler
} from './editor/mentions'
import { useConversationsStore } from '@/stores/conversations'
import { useContextsStore } from '@/stores/contexts'
import { useRouter } from 'vue-router'
import { Button } from './ui/button'
import { SparklesIcon } from 'lucide-vue-next'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from './ui/dropdown-menu'

interface Props {
  modelValue: string
  placeholder?: string
  disabled?: boolean
  documentId?: string
  /** Enable @ mentions for queries (inserts QueryNode) */
  enableQueryMentions?: boolean
  /** Enable @ mentions for charts (inserts ChartNode) */
  enableChartMentions?: boolean
  /** Enable @ mention for AI agent (inserts AgentMentionNode) */
  enableAgentMention?: boolean
  /** Whether to show the bubble menu for AI assistance (defaults to true) */
  showBubbleMenu?: boolean
  /** Minimum height for the editor content area */
  minHeight?: string
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Start writing...',
  disabled: false,
  documentId: undefined,
  enableQueryMentions: false,
  enableChartMentions: false,
  enableAgentMention: false,
  showBubbleMenu: true,
  minHeight: '200px'
})

// Check if any mention type is enabled
const hasMentionsEnabled = computed(
  () => props.enableQueryMentions || props.enableChartMentions || props.enableAgentMention
)

// Computed mention suggestion based on enabled mention types
const mentionSuggestionConfig = computed(() => {
  const options = {
    enableQueryMentions: props.enableQueryMentions,
    enableChartMentions: props.enableChartMentions,
    enableAgentMention: props.enableAgentMention
  }

  const component = getSuggestionComponent(options)
  if (!component) return null

  const selectHandler = getSelectHandler(options)
  return createMentionSuggestion(component, selectHandler)
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'submit'): void
}>()

// Get stores and router for conversation creation
const conversationsStore = useConversationsStore()
const contextsStore = useContextsStore()
const router = useRouter()

// BubbleMenu state
const bubbleQuestion = ref('')
const bubbleInputRef = ref<HTMLInputElement | null>(null)
const showAskInput = ref(false)

// Watch for dropdown open state to focus input
watch(showAskInput, async (isOpen) => {
  if (isOpen) {
    await nextTick()
    setTimeout(() => {
      bubbleInputRef.value?.focus()
    }, 100)
  }
})

// Control when to show the bubble menu
const shouldShowMenu = () => {
  if (!editor.value) return false

  const { state } = editor.value
  const { selection } = state
  const { from, to } = selection

  // Only show if there's a text selection (not just cursor position)
  if (from === to) return false

  // Only show if there's selected text
  const { doc } = state
  const selectedText = doc.textBetween(from, to, ' ')
  return selectedText.trim().length > 0
}

// Handle improve writing action
const handleImproveWriting = async () => {
  if (!editor.value) return

  const { state } = editor.value
  const { from, to } = state.selection
  const selectedText = state.doc.textBetween(from, to, '\n')

  // Create the question for improving writing
  let question = `Please improve the following text from the document:\n\n"${selectedText}"\n\nMake it clearer, more concise, and better written while preserving the original meaning.`

  // Add document ID if available
  if (props.documentId) {
    question = `[Document ID: ${props.documentId}]\n\n${question}`
  }

  try {
    // Get the current context
    const contextSelected = contextsStore.contextSelected
    if (!contextSelected) {
      alert('Please select a database context first')
      return
    }

    // Create a new conversation
    const newConversation = await conversationsStore.createConversation(contextSelected.id)

    await conversationsStore.sendMessage(newConversation.id, question, 'text')

    router.push({ name: 'ChatPage', params: { id: newConversation.id } })

    // Reset bubble menu state
    showAskInput.value = false
    bubbleQuestion.value = ''
  } catch (error) {
    console.error('Failed to create conversation:', error)
    alert('Failed to start conversation. Please try again.')
  }
}

// Handle suggested actions from dropdown
const handleSuggestedAction = async (action: string) => {
  if (!editor.value) return

  const { state } = editor.value
  const { from, to } = state.selection
  const selectedText = state.doc.textBetween(from, to, '\n')

  const actionPrompts: Record<string, string> = {
    improve: `Please improve the following text:\n\n"${selectedText}"\n\nMake it clearer, more concise, and better written while preserving the original meaning.`,
    'fix-grammar': `Please fix the spelling and grammar in the following text:\n\n"${selectedText}"\n\nCorrect any errors while keeping the original style and meaning.`,
    'make-shorter': `Please make the following text shorter and more concise:\n\n"${selectedText}"\n\nRemove unnecessary words while keeping the key message.`,
    simplify: `Please simplify the language in the following text:\n\n"${selectedText}"\n\nMake it easier to understand while keeping the same meaning.`,
    'make-longer': `Please expand the following text with more details and context:\n\n"${selectedText}"\n\nAdd relevant information while maintaining clarity.`
  }

  let question = actionPrompts[action] || bubbleQuestion.value

  // Add document ID if available
  if (props.documentId) {
    question = `[Document ID: ${props.documentId}]\n\n${question}`
  }

  try {
    const contextSelected = contextsStore.contextSelected
    if (!contextSelected) {
      alert('Please select a database context first')
      return
    }

    const newConversation = await conversationsStore.createConversation(contextSelected.id)
    await conversationsStore.sendMessage(newConversation.id, question, 'text')
    router.push({ name: 'ChatPage', params: { id: newConversation.id } })

    // Reset state
    showAskInput.value = false
    bubbleQuestion.value = ''
  } catch (error) {
    console.error('Failed to create conversation:', error)
    alert('Failed to start conversation. Please try again.')
  }
}

// Handle ask question action
const handleAskQuestion = async () => {
  if (!bubbleQuestion.value.trim() || !editor.value) return

  const { state } = editor.value
  const { from, to } = state.selection
  const selectedText = state.doc.textBetween(from, to, '\n')

  // Create the question with context
  let fullQuestion = `Regarding this text from the document:\n\n"${selectedText}"\n\n${bubbleQuestion.value}`

  // Add document ID if available
  if (props.documentId) {
    fullQuestion = `[Document ID: ${props.documentId}]\n\n${fullQuestion}`
  }

  try {
    // Get the current context
    const contextSelected = contextsStore.contextSelected
    if (!contextSelected) {
      alert('Please select a database context first')
      return
    }

    // Create a new conversation
    const newConversation = await conversationsStore.createConversation(contextSelected.id)

    await conversationsStore.sendMessage(newConversation.id, fullQuestion, 'text')

    router.push({ name: 'ChatPage', params: { id: newConversation.id } })

    // Clear the input and reset state
    bubbleQuestion.value = ''
    showAskInput.value = false
  } catch (error) {
    console.error('Failed to create conversation:', error)
    alert('Failed to start conversation. Please try again.')
  }
}

// Handle escape key
const handleCloseBubble = () => {
  bubbleQuestion.value = ''
  showAskInput.value = false
  editor.value?.commands.focus()
}

// Parse markdown content to HTML for initial load
function markdownToHTML(markdown: string): string {
  if (!markdown) return ''

  // Split by lines and process
  const lines = markdown.split('\n')
  const htmlParts: string[] = []
  let inParagraph = false
  let paragraphContent: string[] = []

  // Helper to process inline content including agent mentions and user mentions
  const processInlineContent = (text: string): string => {
    return text
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`(.+?)`/g, '<code>$1</code>')
      .replace(
        /<AGENT:([^>]+)>/g,
        '<span data-type="agent-mention" data-agent-id="$1" data-agent-label="Myriade Agent"></span>'
      )
      .replace(
        /<USER:([^>]+)>/g,
        '<span data-type="user-mention" data-user-label="$1"></span>'
      )
  }

  const flushParagraph = () => {
    if (paragraphContent.length > 0) {
      const content = processInlineContent(paragraphContent.join(' '))
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

// Build extensions array based on enabled features
const buildExtensions = () => {
  const extensions = [
    StarterKit,
    Placeholder.configure({
      placeholder: props.placeholder
    }),
    QueryNode,
    ChartNode,
    AgentMentionNode,
    UserMentionNode
  ]

  // Only add Mention extension if any mention type is enabled
  if (hasMentionsEnabled.value && mentionSuggestionConfig.value) {
    extensions.push(
      Mention.configure({
        HTMLAttributes: {
          class: 'mention',
          'data-type': 'mention',
          'data-id': null
        },
        renderLabel: ({ node }) => {
          return node.attrs.id || '@mention'
        },
        suggestion: mentionSuggestionConfig.value
      })
    )
  }

  return extensions
}

// Initialize Tiptap editor
const editor = useEditor({
  extensions: buildExtensions(),
  content: (() => {
    const html = props.modelValue ? markdownToHTML(props.modelValue) : ''
    return html
  })(),
  editorProps: {
    attributes: {
      class: `prose prose-sm max-w-none focus:outline-none min-h-[${props.minHeight}] p-4 rounded-lg`
    },
    handleKeyDown: (_view, event) => {
      // Handle Cmd+Enter (Mac) or Ctrl+Enter (Windows/Linux) to submit
      if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
        emit('submit')
        return true
      }
      return false
    }
  },
  onUpdate: ({ editor }) => {
    // Emit change immediately for parent to handle
    const markdown = serializeToMarkdown(editor.state.doc)
    if (markdown !== props.modelValue) {
      emit('update:modelValue', markdown)
    }
  },
  editable: !props.disabled
})

// Update editor content when prop changes
watch(
  () => props.modelValue,
  (newValue) => {
    if (!editor.value) return

    const currentMarkdown = serializeToMarkdown(editor.value.state.doc)
    if (newValue !== currentMarkdown) {
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

// Clean up editor on unmount
onUnmounted(() => {
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

.tiptap-editor-content .ProseMirror p.is-empty::before {
  color: var(--muted-foreground);
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

/* Prose styles for markdown rendering */
.tiptap-editor-content .ProseMirror {
  color: var(--foreground);
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
  background-color: var(--muted);
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.tiptap-editor-content .ProseMirror pre {
  background-color: var(--card);
  color: var(--card-foreground);
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
  border-left: 4px solid var(--border);
  padding-left: 1rem;
  margin-left: 0;
  margin-bottom: 1rem;
  color: var(--muted-foreground);
}

.tiptap-editor-content .ProseMirror hr {
  border: none;
  border-top: 2px solid var(--border);
  margin: 2rem 0;
}

.tiptap-editor-content .ProseMirror strong {
  font-weight: 600;
}

.tiptap-editor-content .ProseMirror em {
  font-style: italic;
}

.tiptap-editor-content .ProseMirror a {
  color: var(--primary);
  text-decoration: underline;
}

.tiptap-editor-content .ProseMirror a:hover {
  color: var(--primary);
}

/* Node selection styles */
.tiptap-editor-content .ProseMirror .ProseMirror-selectednode {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
  border-radius: 0.5rem;
}

/* Custom mention dropdown positioning */

/* Bubble menu styles */
.bubble-menu-container {
  z-index: 50;
}
</style>
