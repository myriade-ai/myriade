<template>
  <div class="min-h-full">
    <AnonymousUserBar />
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
import AnonymousUserBar from '@/components/AnonymousUserBar.vue'
</script>
