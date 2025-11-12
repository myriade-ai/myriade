import axios from '@/plugins/axios'
import { useContextsStore } from '@/stores/contexts'
import { useQuery, type UseQueryReturnType } from '@tanstack/vue-query'
import type { AxiosResponse } from 'axios'
import { computed, type Ref } from 'vue'

export interface OverallStats {
  total_assets: number
  completion_percentage: number
  assets_validated: number
  assets_ai_generated: number
  assets_to_review: number
}

export interface SchemaStats {
  schema_name: string
  schema_asset_id: string
  table_count: number
  completion_percentage: number
}

export interface DatabaseStats {
  database_id: string
  database_name: string
  total_schemas: number
  total_tables: number
  total_columns: number
  completion_percentage: number
  last_updated: string | null
  schemas: SchemaStats[]
}

export interface DashboardStatsResponse {
  overall: OverallStats
  databases: DatabaseStats[]
}

/**
 * TanStack Query hook for fetching dashboard statistics
 * Fetches aggregated catalog statistics for a database
 */
export function useDashboardStatsQuery(
  databaseId?: Ref<string | null | undefined>
): UseQueryReturnType<DashboardStatsResponse, Error> {
  const contextsStore = useContextsStore()

  const selectedDatabaseId = computed<string | null>(() => {
    if (databaseId?.value) {
      return databaseId.value
    }
    try {
      return contextsStore.getSelectedContextDatabaseId()
    } catch {
      return null
    }
  })

  const query = useQuery({
    queryKey: computed(() => ['dashboard-stats', selectedDatabaseId.value]),
    queryFn: async (): Promise<DashboardStatsResponse> => {
      const currentDatabaseId = selectedDatabaseId.value
      if (!currentDatabaseId) {
        throw new Error('No database selected')
      }

      const response: AxiosResponse<DashboardStatsResponse> = await axios.get(
        `/api/databases/${currentDatabaseId}/catalog/dashboard-stats`
      )

      return response.data
    },
    // Only run query when we have a database selected
    enabled: computed(() => !!selectedDatabaseId.value),

    // Cache for 2 minutes - stats don't change frequently
    staleTime: 2 * 60 * 1000,
    gcTime: 10 * 60 * 1000,

    // Don't refetch on window focus
    refetchOnWindowFocus: false,

    // Retry failed requests with exponential backoff
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
  })

  return query
}
