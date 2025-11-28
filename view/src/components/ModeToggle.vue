<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <button
        class="flex items-center gap-2 w-full px-2 py-1.5 text-sm rounded-md hover:bg-sidebar-accent hover:text-sidebar-accent-foreground whitespace-nowrap"
        @click.stop
      >
        <div class="relative h-4 w-4 flex-shrink-0">
          <Sun class="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon
            class="absolute inset-0 h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100"
          />
        </div>
        <span class="flex-1 text-left">Theme</span>
        <ChevronRight class="h-4 w-4 ml-auto flex-shrink-0" />
      </button>
    </DropdownMenuTrigger>
    <DropdownMenuContent side="right" align="start">
      <DropdownMenuLabel>Appearance</DropdownMenuLabel>
      <DropdownMenuSeparator />
      <DropdownMenuRadioGroup v-model="mode">
        <DropdownMenuRadioItem value="light">
          <Sun class="h-4 w-4" />
          <span>Light</span>
        </DropdownMenuRadioItem>
        <DropdownMenuRadioItem value="dark">
          <Moon class="h-4 w-4" />
          <span>Dark</span>
        </DropdownMenuRadioItem>
        <DropdownMenuRadioItem value="auto">
          <Monitor class="h-4 w-4" />
          <span>System</span>
        </DropdownMenuRadioItem>
      </DropdownMenuRadioGroup>
    </DropdownMenuContent>
  </DropdownMenu>
</template>

<script setup lang="ts">
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { useDarkMode } from '@/composables/useDarkMode'
import { ChevronRight, Monitor, Moon, Sun } from 'lucide-vue-next'

const { mode } = useDarkMode()
</script>
