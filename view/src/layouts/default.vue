<template>
  <SidebarProvider :default-open="true">
    <AppSidebar />
    <SidebarInset class="min-w-0 w-full">
      <div class="flex-1 flex flex-col">
        <AnonymousUserBar />
        <Suspense>
          <template #default>
            <router-view />
          </template>
          <template #fallback>
            <div class="flex items-center justify-center h-full">
              <div class="text-center">
                <div
                  class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"
                ></div>
                <p class="text-sm text-gray-600">Loading...</p>
              </div>
            </div>
          </template>
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
