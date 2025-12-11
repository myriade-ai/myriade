<template>
  <div :class="$attrs.class ?? '' + ' markdown-content'" v-html="sanitizedHtml"></div>
</template>

<script setup lang="ts">
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { computed } from 'vue'

const props = defineProps<{
  content: string
}>()

// Process custom tags before markdown parsing
const processedContent = computed(() => {
  return props.content
    .replace(/<QUERY:([^>]+)>/g, '<a href="/query/$1">Query $1</a>')
    .replace(/<AGENT:([^>]+)>/g, '<span class="agent-mention">@Myriade Agent</span>')
    .replace(/<USER:([^>]+)>/g, '<span class="user-mention">@$1</span>')
})

// Sanitize HTML to prevent XSS attacks
const sanitizedHtml = computed(() => {
  // Enable GFM for table support, but we still sanitize output with DOMPurify
  const rawHtml = marked(processedContent.value, {
    breaks: true,
    gfm: true // Enable GitHub Flavored Markdown for tables support
  }) as string
  return DOMPurify.sanitize(rawHtml, {
    ALLOWED_TAGS: [
      'h1',
      'h2',
      'h3',
      'h4',
      'h5',
      'h6',
      'p',
      'br',
      'strong',
      'em',
      'u',
      'a',
      'ul',
      'ol',
      'li',
      'blockquote',
      'code',
      'pre',
      'table',
      'thead',
      'tbody',
      'tr',
      'th',
      'td',
      'span'
    ],
    ALLOWED_ATTR: ['href', 'title', 'class']
  })
})
</script>

<style>
.markdown-content {
  /* Inherit font-size from parent for flexibility */
  font-size: inherit;
  line-height: 1.5;

  h1 {
    font-size: 1.25em;
    font-weight: 600;
    margin-bottom: 0.75rem;
    margin-top: 0.5rem;
  }
  h2 {
    font-size: 1.125em;
    font-weight: 600;
    margin-bottom: 0.5rem;
    margin-top: 0.375rem;
  }
  h3 {
    font-size: 1em;
    font-weight: 600;
    margin-bottom: 0.375rem;
  }
  h4 {
    font-size: 0.9375em;
    font-weight: 600;
    margin-bottom: 0.375rem;
  }
  p {
    margin-bottom: 0.5rem;
  }
  p:last-child {
    margin-bottom: 0;
  }
  ul {
    margin-bottom: 0.5rem;
    list-style-type: disc;
    padding-left: 1.25rem;
  }
  ol {
    margin-bottom: 0.5rem;
    list-style-type: decimal;
    padding-left: 1.25rem;
  }
  li {
    padding-left: 0;
    margin-bottom: 0.25rem;
  }
  a {
    color: var(--primary);
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 0.75rem;
    font-size: 0.9375em;
  }
  th,
  td {
    border: 1px solid var(--border);
    padding: 0.375rem 0.5rem;
  }
  pre {
    background-color: var(--muted);
    border: 1px solid var(--border);
    border-radius: 0.375rem;
    padding: 0.75rem;
    overflow-x: auto;
    margin-bottom: 0.5rem;
    font-size: 0.875em;
  }
  code {
    background-color: var(--muted);
    padding: 0.125rem 0.25rem;
    border-radius: 0.25rem;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.875em;
  }
  pre code {
    background-color: transparent;
    padding: 0;
    border-radius: 0;
  }
  blockquote {
    border-left: 3px solid var(--border);
    padding-left: 0.75rem;
    margin-left: 0;
    margin-bottom: 0.5rem;
    color: var(--muted-foreground);
    font-style: italic;
  }
  .agent-mention {
    display: inline-flex;
    align-items: center;
    gap: 0.2rem;
    padding: 0.1rem 0.35rem;
    border-radius: 0.25rem;
    background-color: oklch(from var(--gold) l c h / 0.15);
    color: var(--foreground);
    font-weight: 500;
    font-size: 0.9em;
  }
  .agent-mention-icon {
    width: 0.875rem;
    height: 0.875rem;
    margin-right: 0.1em;
    color: var(--gold);
  }
  .user-mention {
    display: inline-flex;
    align-items: center;
    padding: 0.1rem 0.35rem;
    border-radius: 0.25rem;
    background-color: rgb(219 234 254); /* blue-100/primary-100 */
    color: rgb(29 78 216); /* blue-700/primary-700 */
    font-weight: 500;
    font-size: 0.9em;
  }
}

/* Dark mode adjustments for mentions */
.dark .markdown-content {
  .agent-mention {
    background-color: oklch(from var(--gold) l c h / 0.2);
    color: var(--gold);
  }
  .agent-mention-icon {
    color: var(--gold);
  }
  .user-mention {
    background-color: rgb(30 58 138 / 0.3); /* blue-900/30 */
    color: rgb(147 197 253); /* blue-300 */
  }
}
</style>
