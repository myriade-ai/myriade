<template>
  <SidebarProvider :default-open="true">
    <AppSidebar />
    <SidebarInset class="min-w-0 w-full h-screen overflow-hidden">
      <div class="flex flex-col h-full bg-background">
        <AnonymousUserBar class="shrink-0" />
        <Suspense>
          <router-view class="flex-1 min-h-0 overflow-y-auto overscroll-contain" />
        </Suspense>
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>

<script setup lang="ts">
import AnonymousUserBar from '@/components/AnonymousUserBar.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar'
</script>
