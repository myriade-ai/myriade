import type { CatalogAsset } from '@/stores/catalog'

interface CatalogStats {
  total_assets: number
  completion_score: number
  assets_to_review: number
  assets_validated: number
  assets_with_ai_suggestions: number
  assets_with_description: number
}

/**
 * Compute catalog statistics from an array of assets
 * This allows calculating stats at any level (database, schema, table)
 */
export function computeCatalogStats(assets: CatalogAsset[]): CatalogStats {
  const totalAssets = assets.length

  if (totalAssets === 0) {
    return {
      total_assets: 0,
      completion_score: 0,
      assets_to_review: 0,
      assets_validated: 0,
      assets_with_ai_suggestions: 0,
      assets_with_description: 0
    }
  }

  const assetsWithDescription = assets.filter(
    (asset) => asset.description && asset.description.trim()
  ).length

  const assetsToReview = assets.filter(
    (asset) => asset.status === 'needs_review' || asset.status === 'requires_validation'
  ).length

  const assetsValidated = assets.filter((asset) => asset.status === 'validated').length

  const assetsWithAiSuggestions = assets.filter((asset) => asset.ai_suggestion).length

  const completionScore = Math.round((assetsWithDescription / totalAssets) * 100 * 10) / 10

  return {
    total_assets: totalAssets,
    completion_score: completionScore,
    assets_to_review: assetsToReview,
    assets_validated: assetsValidated,
    assets_with_ai_suggestions: assetsWithAiSuggestions,
    assets_with_description: assetsWithDescription
  }
}
