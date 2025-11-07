<template>
  <header
    :class="[
      'flex h-16 shrink-0 items-center gap-2 border-b px-4 bg-white',
      sticky && 'sticky top-0 z-10'
    ]"
  >
    <SidebarTrigger class="md:hidden -ml-1" />
    <div class="flex gap-2 items-baseline flex-1">
      <h1 class="text-xl">{{ title }}</h1>
      <p v-if="subtitle" class="hidden md:block text-sm text-gray-500">
        {{ subtitle }}
      </p>
    </div>
    <div v-if="$slots.actions" class="flex items-center gap-2">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup lang="ts">
import { SidebarTrigger } from '@/components/ui/sidebar'

interface Props {
  title: string
  subtitle?: string
  sticky?: boolean
}

defineProps<Props>()
</script>
