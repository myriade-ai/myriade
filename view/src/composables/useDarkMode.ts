import { useColorMode } from '@vueuse/core'

export type ColorMode = 'light' | 'dark' | 'auto'

// Initialize color mode at module load (singleton pattern)
const mode = useColorMode({
  selector: 'html',
  attribute: 'class',
  storageKey: 'myriade-color-mode',
  modes: {
    light: 'light',
    dark: 'dark',
    auto: 'auto'
  },
  initialValue: 'auto'
})

export function useDarkMode() {
  return {
    mode,
    setMode: (newMode: ColorMode) => {
      mode.value = newMode
    }
  }
}
