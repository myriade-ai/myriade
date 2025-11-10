import axios from '@/plugins/axios'
import type { CatalogAsset } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import type { Table } from '@/stores/tables'
import { keepPreviousData, useQuery, type UseQueryReturnType } from '@tanstack/vue-query'
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
    databaseName: tableAsset.table_facet?.database_name || null,
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

  const databaseId = computed<string | null>(() => {
    try {
      return contextsStore.getSelectedContextDatabaseId()
    } catch (error) {
      return null
    }
  })

  const query = useQuery({
    queryKey: computed(() => ['catalog', 'assets', databaseId.value]),
    queryFn: async (): Promise<CatalogAsset[]> => {
      const currentDatabaseId = databaseId.value
      if (!currentDatabaseId) {
        throw new Error('No database selected')
      }

      const response: AxiosResponse<CatalogAsset[]> = await axios.get(
        `/api/databases/${currentDatabaseId}/catalog/assets`
      )

      return response.data
    },
    // Only run query when we have a context selected
    enabled: computed(() => !!databaseId.value),

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

/**
 * TanStack Query hook for searching catalog assets
 * Returns only asset IDs matching the search query using server-side fuzzy matching
 * Triggered for queries >= 3 characters or when tag/status filters are selected
 */
export function useCatalogSearchQuery(
  databaseId: Ref<string | null>,
  searchText: Ref<string>,
  enabled: Ref<boolean>,
  selectedTag: Ref<string>,
  selectedStatus: Ref<string>
): UseQueryReturnType<string[], Error> {
  const query = useQuery({
    queryKey: computed(() => [
      'catalog',
      'search',
      databaseId.value,
      searchText.value,
      selectedTag.value,
      selectedStatus.value
    ]),
    queryFn: async (): Promise<string[]> => {
      const currentDatabaseId = databaseId.value
      const currentSearchText = searchText.value
      const currentTag = selectedTag.value
      const currentStatus = selectedStatus.value

      if (!currentDatabaseId || !currentSearchText) {
        return []
      }

      // Build query params, excluding "__all__" values
      const params: {
        q: string
        tag_ids?: string[]
        statuses?: string[]
      } = {
        q: currentSearchText
      }

      if (currentTag && currentTag !== '__all__') {
        params.tag_ids = [currentTag]
      }

      if (currentStatus && currentStatus !== '__all__') {
        params.statuses = [currentStatus]
      }

      const response: AxiosResponse<string[]> = await axios.get(
        `/api/databases/${currentDatabaseId}/catalog/search`,
        { params }
      )

      return response.data
    },
    // Only run query when enabled, we have a database ID, and search text is >= 3 characters
    enabled: computed(() => enabled.value && !!databaseId.value && searchText.value.length >= 3),

    // Keep previous data while fetching new results (prevents blink effect)
    placeholderData: keepPreviousData,

    // Cache search results for 2 minutes
    staleTime: 2 * 60 * 1000,

    // Keep unused search results in cache for 5 minutes
    gcTime: 5 * 60 * 1000,

    // Don't refetch on window focus
    refetchOnWindowFocus: false,

    // Retry failed requests
    retry: 1,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 5000)
  })

  return query
}
