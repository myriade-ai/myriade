<template>
  <div :class="$attrs.class + ' markdown-content'" v-html="marked(content)"></div>
</template>

<script setup lang="ts">
import { marked } from 'marked'
import { computed } from 'vue'

const props = defineProps<{
  content: string
}>()

// We need to replace <QUERY:uuid> with link to the query
// eg. uuid d3a2541d-6fc6-4ae9-841e-055e60f0575e
const content = computed(() => {
  return props.content.replace(/<QUERY:([^>]+)>/g, '<a href="/query/$1">Query $1</a>')
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
    color: #007bff;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1rem;
  }
  th,
  td {
    border: 1px solid #dee2e6;
    padding: 0.2rem;
  }
}
</style>
