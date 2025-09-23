export interface FeatureFlag {
  name: string
  code: string
  enabled: boolean
}

export type FeatureFlagCode = string
export type FeatureFlagConfig = FeatureFlag | FeatureFlagCode

// Vite modes for feature flag environments
export type ViteMode = 'development' | 'staging' | 'production'
