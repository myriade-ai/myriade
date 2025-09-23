import { useFeatureFlagsStore } from '@/stores/featureFlags'
import type { FeatureFlagConfig } from '@/types/featureFlags'

/**
 * Check if a feature flag is enabled
 * @param config - Either a feature flag code (string) or a FeatureFlag object
 * @returns boolean - true if feature is enabled, false otherwise
 *
 * @example
 * // Using feature code
 * if (isFeatureEnabled('new-chat-ui')) {
 *   // Show new chat UI
 * }
 *
 * // Using feature config object
 * const feature = { name: 'Beta Features', code: 'beta-features', enabled: true }
 * if (isFeatureEnabled(feature)) {
 *   // Show beta features
 * }
 */
export function isFeatureEnabled(config: FeatureFlagConfig): boolean {
  const featureFlagsStore = useFeatureFlagsStore()
  return featureFlagsStore.isFeatureEnabled(config)
}

export { useFeatureFlagsStore } from '@/stores/featureFlags'
export type { FeatureFlag, FeatureFlagConfig, FeatureFlagCode } from '@/types/featureFlags'
