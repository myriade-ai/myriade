<template>
  <div
    class="tabs-list inline-flex h-10 items-center justify-center rounded-md bg-gray-100 p-1 text-gray-500"
    :class="$attrs.class"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
// No props needed, just a container for tab triggers
</script>
