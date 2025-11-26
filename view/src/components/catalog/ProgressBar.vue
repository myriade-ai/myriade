<template>
  <!-- Full-width mode -->
  <div v-if="size === 'md'" class="w-full">
    <div v-if="label" class="flex items-center justify-between mb-2">
      <span class="text-sm font-medium">{{ label }}</span>
      <span class="text-sm font-medium">{{ percentage }}%</span>
    </div>
    <div class="w-full h-2 bg-muted rounded-sm overflow-hidden">
      <div
        class="h-full transition-all duration-300 rounded-sm"
        :class="barColorClass"
        :style="{ width: `${Math.min(percentage, 100)}%` }"
      />
    </div>
  </div>

  <!-- Inline mode (compact) -->
  <div v-else class="flex items-center gap-2">
    <div class="h-1.5 w-24 bg-muted rounded-sm overflow-hidden flex-shrink-0">
      <div
        class="h-full transition-all duration-300 rounded-sm"
        :class="barColorClass"
        :style="{ width: `${Math.min(percentage, 100)}%` }"
      />
    </div>
    <span class="text-xs font-medium text-foreground whitespace-nowrap">{{ percentage }}%</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  percentage: number
  label?: string
  size?: 'sm' | 'md'
}

const props = withDefaults(defineProps<Props>(), {
  label: undefined,
  size: 'sm'
})

const barColorClass = computed(() => {
  if (props.percentage >= 70) {
    return 'bg-green-600'
  } else if (props.percentage >= 30) {
    return 'bg-yellow-500'
  } else {
    return 'bg-red-500'
  }
})
</script>
