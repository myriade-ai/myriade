<template>
  <div class="internal-message-preview">
    <!-- Collapsed preview -->
    <div v-if="!isExpanded" class="relative">
      <div class="preview-content max-h-40 overflow-hidden">
        <slot></slot>
      </div>
      <div class="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-gray-50 to-transparent pointer-events-none"></div>
    </div>
    
    <!-- Expanded full content -->
    <div v-else>
      <slot></slot>
    </div>
    
    <!-- Toggle button -->
    <div class="flex justify-center mt-2">
      <Button
        variant="ghost"
        size="sm"
        @click="toggleExpand"
        class="text-xs text-gray-600 hover:text-gray-900"
      >
        <ChevronDown v-if="!isExpanded" class="h-3 w-3 mr-1" />
        <ChevronUp v-else class="h-3 w-3 mr-1" />
        {{ isExpanded ? 'Show less' : 'Show more' }}
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Button } from './ui/button'
import { ChevronDown, ChevronUp } from 'lucide-vue-next'

const isExpanded = ref(false)

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}
</script>

<style scoped>
.preview-content {
  position: relative;
}
</style>
