<template>
  <TooltipProvider>
    <Tooltip>
      <TooltipTrigger as-child>
        <span :class="badgeClasses">
          <component :is="iconComponent" class="h-3.5 w-3.5" />
        </span>
      </TooltipTrigger>
      <TooltipContent>
        <p>{{ status.label }}</p>
      </TooltipContent>
    </Tooltip>
  </TooltipProvider>
</template>

<script setup lang="ts">
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { CheckCircle2, Circle, PenLine, Sparkles } from 'lucide-vue-next'
import { computed } from 'vue'
import type { AssetStatusInfo } from './types'

interface Props {
  status: AssetStatusInfo
}

const props = defineProps<Props>()

const iconComponent = computed(() => {
  switch (props.status.variant) {
    case 'published':
      return CheckCircle2
    case 'draft':
      return PenLine
    case 'ai-suggestion':
      return Sparkles
    case 'used':
      return Circle
    default:
      return Circle
  }
})

const badgeClasses = computed(() => {
  const base = 'inline-flex items-center justify-center rounded-full p-1'

  switch (props.status.variant) {
    case 'published':
      return `${base} text-green-600 dark:text-green-400`
    case 'draft':
      return `${base} text-yellow-600 dark:text-yellow-400`
    case 'ai-suggestion':
      return `${base} text-purple-600 dark:text-purple-400`
    case 'used':
      return `${base} text-blue-600 dark:text-blue-400`
    default:
      return `${base} text-gray-400 dark:text-gray-500`
  }
})
</script>
