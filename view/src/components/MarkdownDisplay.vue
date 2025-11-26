<template>
  <div :class="$attrs.class ?? '' + ' markdown-content'" v-html="sanitizedHtml"></div>
</template>

<script setup lang="ts">
import { marked } from 'marked'
import DOMPurify from 'dompurify'
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
  // Disable auto-linking in markdown
  const rawHtml = marked(processedContent.value, {
    breaks: true,
    gfm: false // Disable GitHub Flavored Markdown (which auto-links emails)
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
  h1 {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 1rem;
  }
  h2 {
    font-size: 1.25rem;
    font-weight: 600;
  }
  h3 {
    font-size: 1rem;
    font-weight: 600;
  }
  h4 {
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: 1rem;
  }
  ul {
    margin-bottom: 1rem;
    list-style-type: disc;
    padding-left: 1rem;
  }
  ol {
    margin-bottom: 1rem;
    list-style-type: decimal;
    padding-left: 1rem;
  }
  li {
    padding-left: 0rem;
  }
  a {
    color: var(--primary);
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1rem;
  }
  th,
  td {
    border: 1px solid var(--border);
    padding: 0.2rem;
  }
  pre {
    background-color: var(--muted);
    border: 1px solid var(--border);
    border-radius: 0.375rem;
    padding: 1rem;
    overflow-x: auto;
    margin-bottom: 1rem;
  }
  code {
    background-color: var(--muted);
    padding: 0.2rem 0.4rem;
    border-radius: 0.25rem;
    font-family: monospace;
    font-size: 0.875em;
  }
  pre code {
    background-color: transparent;
    padding: 0;
    border-radius: 0;
  }
  .agent-mention {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.125rem 0.375rem;
    border-radius: 0.375rem;
    background-color: rgb(243 232 255); /* purple-100 */
    color: rgb(126 34 206); /* purple-700 */
    font-weight: 500;
    font-size: 0.875rem;
  }
  .agent-mention-icon {
    width: 1rem;
    height: 1rem;
    margin-right: 0.15em;
    color: rgb(126 34 206); /* purple-700 */
  }
  .user-mention {
    display: inline-flex;
    align-items: center;
    padding: 0.125rem 0.375rem;
    border-radius: 0.375rem;
    background-color: rgb(219 234 254); /* blue-100/primary-100 */
    color: rgb(29 78 216); /* blue-700/primary-700 */
    font-weight: 500;
    font-size: 0.875rem;
  }
}
</style>
