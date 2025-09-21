<template>
  <div :class="$attrs.class + ' markdown-content'" v-html="marked(content)"></div>
</template>

<script setup lang="ts">
import { marked } from 'marked'
import { computed } from 'vue'

const props = defineProps<{
  content: string
}>()

// Note: <QUERY:> and <CHART:> tags should be handled by the message parsing logic,
// not converted to simple links here. This ensures proper interactive components with favorites.
const content = computed(() => {
  return props.content
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
