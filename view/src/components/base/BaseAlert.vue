<template>
  <div class="rounded-md bg-error-50 p-4">
    <div class="flex">
      <div class="shrink-0">
        <XCircleIcon class="h-5 w-5 text-error-400" aria-hidden="true" />
      </div>
      <div class="ml-3">
        <h3 class="text-sm font-medium text-error-800">
          <slot name="title" />
        </h3>
        <div class="mt-2 text-sm text-error-700"><slot></slot></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { XCircleIcon } from '@heroicons/vue/24/solid'
</script>
