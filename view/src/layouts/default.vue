<template>
  <SidebarProvider :default-open="true">
    <AppSidebar />
    <SidebarInset class="min-w-0 w-full">
      <div class="flex-1 flex flex-col">
        <AnonymousUserBar />
        <Suspense>
          <router-view />
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
