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

// We need to replace <QUERY:uuid> with link to the query
// eg. uuid d3a2541d-6fc6-4ae9-841e-055e60f0575e
const content = computed(() => {
  return props.content.replace(/<QUERY:([^>]+)>/g, '<a href="/query/$1">Query $1</a>')
})

// Sanitize HTML to prevent XSS attacks
const sanitizedHtml = computed(() => {
  const rawHtml = marked(content.value) as string
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
      'td'
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
}
</style>
