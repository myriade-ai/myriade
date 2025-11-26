import { usePreferredDark, useStorage } from '@vueuse/core'
import { computed, watch } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'

// Store the user's preference (light, dark, or system)
export const themeMode = useStorage<ThemeMode>('theme-mode', 'system')

// Detect system preference
const prefersDark = usePreferredDark()

// Computed property for the actual theme to apply
export const isDark = computed(() => {
  if (themeMode.value === 'system') {
    return prefersDark.value
  }
  return themeMode.value === 'dark'
})

// Watch isDark and apply to HTML element
watch(
  isDark,
  (dark) => {
    if (dark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  },
  { immediate: true }
)

// Helper function to set theme mode
export const setThemeMode = (mode: ThemeMode) => {
  themeMode.value = mode
}
