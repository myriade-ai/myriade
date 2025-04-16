<template>
  <div class="min-h-screen bg-white font-sans">
    <slot />
  </div>
</template>

<script setup>
// Main layout component for homepage with Inter Variable font family
</script>

<style>
/* Ensuring Inter Variable font is applied throughout */
:root {
  --font-family: 'Inter Variable', 'Inter', sans-serif;
}

body {
  font-family: var(--font-family);
  color: rgb(21, 21, 21);
}
</style>