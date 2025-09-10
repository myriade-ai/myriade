<template>
  <div>
    <AnonymousUserBar />
    <div>
      <Suspense>
        <router-view />
      </Suspense>
    </div>
  </div>
</template>

<script setup lang="ts">
import AnonymousUserBar from '@/components/AnonymousUserBar.vue'
</script>
