<template>
  <div
    class="bg-white border border-slate-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow"
  >
    <div class="flex items-start justify-between mb-3">
      <div class="flex items-center gap-2">
        <component v-if="icon" :is="icon" class="h-5 w-5" :class="iconColor" />
        <h3 class="font-semibold text-base">{{ title }}</h3>
      </div>
      <slot name="header-action" />
    </div>

    <div class="space-y-3">
      <slot />
    </div>

    <div v-if="$slots.footer" class="mt-4 pt-4 border-t border-slate-100">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'

interface Props {
  title: string
  icon?: Component
  iconColor?: string
}

withDefaults(defineProps<Props>(), {
  iconColor: 'text-slate-600'
})
</script>
