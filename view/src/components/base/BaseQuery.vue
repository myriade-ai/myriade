<!-- eslint-disable vue/no-mutating-props -->
<template>
  <div class="flex items-center gap-2 justify-end">
    <input
      type="text"
      placeholder="Database used for X,Y and Z..."
      class="flex-1 rounded-md border-gray-300 shadow-xs focus:border-primary-500 focus:ring-primary-500"
      v-model="props.editor.query.title"
      :style="{ 'max-width': '540px' }"
    />
    <BaseButton
      class="disabled:bg-gray-300"
      @click="props.editor.updateQuery"
      :disabled="!editor.queryIsModified || !editor.query.sql"
    >
      Save query
    </BaseButton>
  </div>

  <br />
  <div class="relative">
    <BaseEditor v-model="props.editor.query.sql" @run-query="() => props.editor.runQuery()" />
    <button
      class="absolute bottom-2 right-2 bg-primary-500 hover:bg-primary-600 text-white rounded-full p-3 shadow-lg focus:outline-none focus:ring-2 focus:ring-primary-500 flex items-center justify-center disabled:bg-primary-800"
      @click="props.editor.runQuery"
      :disabled="props.editor.loading.value"
      aria-label="Run query"
      type="button"
    >
      <ArrowPathIcon v-if="editor.loading.value" class="animate-reverse-spin h-6 w-6 text-white" />
      <PlayIcon v-else class="h-6 w-6" />
    </button>
  </div>
</template>

<script setup lang="ts">
import BaseButton from '@/components/base/BaseButton.vue'
import BaseEditor from '@/components/base/BaseEditor.vue'
import { useQueryEditor } from '@/composables/useQueryEditor'
import { ArrowPathIcon } from '@heroicons/vue/24/outline'
import { PlayIcon } from '@heroicons/vue/24/solid'
import { defineProps } from 'vue'

const props = defineProps({
  editor: {
    type: Object as () => ReturnType<typeof useQueryEditor>,
    required: true
  }
})
</script>
