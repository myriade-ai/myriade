<template>
  <div class="min-h-full">
    <Header />
    <div>
      <Suspense>
        <router-view />
      </Suspense>
    </div>
  </div>
</template>

<script setup lang="ts">
import Header from '@/components/Header.vue'
</script>
