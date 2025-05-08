<template>
  <v-ace-editor
    class="shadow-xs focus:ring-blue-500 focus:border-blue-500 block w-full text-lg border-gray-300 rounded-md"
    v-model:value="inputText"
    lang="sql"
    mode="sql"
    theme="monokai"
    :min-lines="isReadOnly ? 2 : 5"
    :max-lines="20"
    @keydown.enter.meta.exact="runQuery"
    :options="{ readOnly: isReadOnly, showPrintMargin: false, fontSize: 14 }"
    placeholder="SELECT * FROM ..."
  />
</template>

<script setup lang="ts">
import type { WritableComputedRef } from 'vue'
import { computed, defineComponent } from 'vue'
import { VAceEditor } from 'vue3-ace-editor'
// Import after vue3-ace-editor
import 'brace/mode/sql'
import 'brace/theme/monokai'

defineComponent({ VAceEditor })

const props = defineProps({
  modelValue: {
    type: String,
    required: true
  },
  readOnly: {
    type: Boolean,
    default: false
  }
})
const emits = defineEmits(['update:modelValue', 'runQuery'])

const runQuery = () => {
  emits('runQuery')
}

const isReadOnly = computed(() => props.readOnly)

const inputText: WritableComputedRef<string> = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    if (!props.readOnly) {
      emits('update:modelValue', value)
    }
  }
})
</script>

<style>
.ace_gutter {
  top: 10px;
  margin: -10px;
}
.ace_scroller {
  top: 10px;
  margin: -10px;
}

/* .ace_layer.ace_marker-layer {
  display: none;
} */
</style>
