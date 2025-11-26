import { useColorMode } from '@vueuse/core'

export type ColorMode = 'light' | 'dark' | 'auto'

export function useDarkMode() {
  const mode = useColorMode({
    selector: 'html',
    attribute: 'class',
    modes: {
      light: 'light',
      dark: 'dark',
      auto: 'auto'
    }
  })

  return {
    mode,
    setMode: (newMode: ColorMode) => {
      mode.value = newMode
    }
  }
}
