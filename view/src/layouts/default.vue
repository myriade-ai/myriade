<template>
  <SidebarProvider :default-open="true">
    <AppSidebar />
    <SidebarInset class="min-w-0 w-full h-screen">
      <div class="flex flex-col h-full bg-page-background">
        <AnonymousUserBar />
        <Suspense>
          <router-view class="flex-1 flex flex-col min-h-0" />
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
