import axios from '@/plugins/axios'
import type { CatalogAsset } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import type { Table } from '@/stores/tables'
import { useQuery, type UseQueryReturnType } from '@tanstack/vue-query'
import type { AxiosResponse } from 'axios'
import { computed, type Ref } from 'vue'

export interface AssetSourceMetadata {
  description?: string
  tags?: string[]
}

export interface AssetSources {
  [providerName: string]: AssetSourceMetadata
}

/**
 * Converts CatalogAsset objects to Table format
 * Optimized to O(n) time complexity using Map for column lookup
 */
export function convertCatalogAssetsToTables(assets: CatalogAsset[]): Table[] {
  // Single pass: Build index of columns by parent table ID
  const columnsByTableId = new Map<
    string,
    Array<{
      id: string
      name: string
      type: string
      description: string
    }>
  >()

  // Separate tables and columns in a single pass
  const tableAssets: CatalogAsset[] = []

  for (const asset of assets) {
    if (asset.type === 'TABLE') {
      tableAssets.push(asset)
    } else if (asset.type === 'COLUMN') {
      const parentTableId = asset.column_facet?.parent_table_asset_id
      if (parentTableId) {
        if (!columnsByTableId.has(parentTableId)) {
          columnsByTableId.set(parentTableId, [])
        }
        columnsByTableId.get(parentTableId)!.push({
          id: asset.id,
          name: asset.column_facet?.column_name || asset.name || '',
          type: asset.column_facet?.data_type || '',
          description: asset.description || ''
        })
      }
    }
  }

  // Convert tables using pre-built column map - O(n) instead of O(n²)
  return tableAssets.map((tableAsset) => ({
    name: tableAsset.table_facet?.table_name || tableAsset.name || '',
    schema: tableAsset.table_facet?.schema || '',
    description: tableAsset.description || '',
    columns: columnsByTableId.get(tableAsset.id) || [],
    used: false // This flag will be computed later based on query context
  }))
}

/**
 * TanStack Query hook for fetching catalog assets
 * Optimized for instant page display with cached data
 */
export function useCatalogAssetsQuery(): UseQueryReturnType<CatalogAsset[], Error> {
  const contextsStore = useContextsStore()

  const contextId = computed(() => contextsStore.contextSelected?.id)

  const query = useQuery({
    queryKey: ['catalog', 'assets', contextId],
    queryFn: async (): Promise<CatalogAsset[]> => {
      const currentContextId = contextId.value
      if (!currentContextId) {
        throw new Error('No context selected')
      }

      const response: AxiosResponse<CatalogAsset[]> = await axios.get(
        `/api/catalogs/${currentContextId}/assets`
      )

      return response.data
    },
    // Only run query when we have a context selected
    enabled: computed(() => !!contextId.value),

    // KEY: Long stale time means cached data shown immediately on page navigation
    // Data is considered "fresh" for 5 minutes, so no refetch on navigation
    staleTime: 5 * 60 * 1000,

    // Keep unused data in cache for 10 minutes
    gcTime: 10 * 60 * 1000,

    // Don't refetch on window focus - reduces unnecessary requests
    refetchOnWindowFocus: false,

    // Retry failed requests with exponential backoff
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

    // KEY: Initialize from cache immediately - this makes page display instant
    placeholderData: (previousData) => previousData
  })

  return query
}

/**
 * TanStack Query hook for fetching asset sources (DBT, Snowflake metadata)
 */
export function useAssetSourcesQuery(
  assetId: Ref<string | null | undefined>
): UseQueryReturnType<AssetSources, Error> {
  const query = useQuery({
    queryKey: ['catalog', 'asset-sources', assetId],
    queryFn: async (): Promise<AssetSources> => {
      const currentAssetId = assetId.value
      if (!currentAssetId) {
        throw new Error('No asset ID provided')
      }

      const response: AxiosResponse<AssetSources> = await axios.get(
        `/api/catalogs/assets/${currentAssetId}/sources`
      )

      return response.data
    },
    // Only run query when we have an asset ID
    enabled: computed(() => !!assetId.value),

    // Cache for 5 minutes
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,

    // Don't refetch on window focus
    refetchOnWindowFocus: false,

    // Retry failed requests
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
  })

  return query
}
