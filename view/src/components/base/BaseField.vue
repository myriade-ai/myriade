<template>
  <div class="sm:col-span-6 mt-2">
    <label for="about" class="block text-sm font-medium text-gray-700">{{ name }}</label>
    <div class="mt-1">
      <!-- slot -->
      <slot />
    </div>
  </div>
</template>
<script setup lang="ts">
// Name from props
const { name } = defineProps<{ name: string }>()
</script>
