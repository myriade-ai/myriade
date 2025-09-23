import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { FeatureFlag, FeatureFlagConfig } from '@/types/featureFlags'

const STORAGE_KEY = 'myriade-feature-flags'

const DEFAULT_FEATURE_FLAGS: FeatureFlag[] = [
  {
    name: 'Catalog',
    code: 'catalog',
    enabled: false
  }
]

export const useFeatureFlagsStore = defineStore('featureFlags', () => {
  const featureFlags = ref<FeatureFlag[]>([])

  const loadFeatureFlags = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsedFlags = JSON.parse(stored) as FeatureFlag[]

        // Merge with defaults to handle new flags
        const mergedFlags = DEFAULT_FEATURE_FLAGS.map((defaultFlag) => {
          const storedFlag = parsedFlags.find((f) => f.code === defaultFlag.code)
          return storedFlag || defaultFlag
        })

        featureFlags.value = mergedFlags
      } else {
        featureFlags.value = [...DEFAULT_FEATURE_FLAGS]
      }
    } catch (error) {
      console.error('Failed to load feature flags:', error)
      featureFlags.value = [...DEFAULT_FEATURE_FLAGS]
    }
  }

  const saveFeatureFlags = () => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(featureFlags.value))
    } catch (error) {
      console.error('Failed to save feature flags:', error)
    }
  }

  const toggleFeatureFlag = (code: string) => {
    const flag = featureFlags.value.find((f) => f.code === code)
    if (flag) {
      flag.enabled = !flag.enabled
      saveFeatureFlags()
    }
  }

  // Check if a feature is enabled
  const isFeatureEnabled = (config: FeatureFlagConfig): boolean => {
    // Only enable feature flags in development and staging modes
    const mode = import.meta.env.MODE
    if (mode === 'production') {
      return false
    }

    const code = typeof config === 'string' ? config : config.code
    const flag = featureFlags.value.find((f) => f.code === code)
    return flag?.enabled || false
  }

  const isDevelopment = computed(() => {
    const mode = import.meta.env.MODE
    return mode === 'development' || mode === 'staging'
  })

  // Initialize store
  loadFeatureFlags()

  return {
    featureFlags,
    isDevelopment,
    toggleFeatureFlag,
    isFeatureEnabled,
    loadFeatureFlags,
    saveFeatureFlags
  }
})
