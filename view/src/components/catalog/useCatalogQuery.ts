import axios from '@/plugins/axios'
import type { CatalogAsset } from '@/stores/catalog'
import { useContextsStore } from '@/stores/contexts'
import { useQuery, type UseQueryReturnType } from '@tanstack/vue-query'
import type { AxiosResponse } from 'axios'
import { computed } from 'vue'

/**
 * TanStack Query hook for fetching catalog assets
 * Optimized for instant page display with cached data
 */
export function useCatalogAssetsQuery(): UseQueryReturnType<CatalogAsset[], Error> {
  const contextsStore = useContextsStore()

  const contextId = computed(() => contextsStore.contextSelected?.id)

  const query = useQuery({
    queryKey: ['catalog', 'assets', contextId.value],
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
