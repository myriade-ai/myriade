<template>
  <header class="flex h-16 shrink-0 items-center gap-2 border-b px-4">
    <SidebarTrigger class="md:hidden -ml-1" />
    <div class="flex gap-2 items-baseline">
      <h1 class="text-xl">{{ title }}</h1>
      <p v-if="subtitle" class="hidden md:block text-sm text-gray-500">
        {{ subtitle }}
      </p>
    </div>
  </header>
</template>

<script setup lang="ts">
import { SidebarTrigger } from '@/components/ui/sidebar'

interface Props {
  title: string
  subtitle?: string
}

defineProps<Props>()
</script>
