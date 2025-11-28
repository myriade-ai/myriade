<script setup lang="ts">
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { isDark, setThemeMode, themeMode } from '@/composables/useTheme'
import { Moon, Sun, Monitor } from 'lucide-vue-next'
import { computed } from 'vue'

const currentIcon = computed(() => {
  if (themeMode.value === 'light') return Sun
  if (themeMode.value === 'dark') return Moon
  return Monitor
})
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <Button variant="ghost" size="icon">
        <component :is="currentIcon" class="h-[1.2rem] w-[1.2rem] transition-all" />
        <span class="sr-only">Toggle theme</span>
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="end">
      <DropdownMenuItem @click="setThemeMode('light')">
        <Sun class="mr-2 h-4 w-4" />
        <span>Light</span>
      </DropdownMenuItem>
      <DropdownMenuItem @click="setThemeMode('dark')">
        <Moon class="mr-2 h-4 w-4" />
        <span>Dark</span>
      </DropdownMenuItem>
      <DropdownMenuItem @click="setThemeMode('system')">
        <Monitor class="mr-2 h-4 w-4" />
        <span>System</span>
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template>
