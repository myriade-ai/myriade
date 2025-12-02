import axios from '@/plugins/axios'
import { useContextsStore } from '@/stores/contexts'
import type { AssetTag } from '@/stores/catalog'
import { useMutation, useQuery, useQueryClient, type UseQueryReturnType } from '@tanstack/vue-query'
import type { AxiosResponse } from 'axios'
import { computed } from 'vue'

/**
 * TanStack Query hook for fetching catalog tags
 * Automatically refetches when database context changes
 */
export function useCatalogTags(): UseQueryReturnType<AssetTag[], Error> {
  const contextsStore = useContextsStore()

  const databaseId = computed<string | null>(() => {
    try {
      return contextsStore.getSelectedContextDatabaseId()
    } catch {
      return null
    }
  })

  const query = useQuery({
    queryKey: computed(() => ['catalog', 'tags', databaseId.value]),
    queryFn: async (): Promise<AssetTag[]> => {
      const currentDatabaseId = databaseId.value
      if (!currentDatabaseId) {
        throw new Error('No database selected')
      }

      const response: AxiosResponse<AssetTag[]> = await axios.get(
        `/api/databases/${currentDatabaseId}/catalog/tags`
      )

      return response.data
    },
    // Only run query when we have a database selected
    enabled: computed(() => !!databaseId.value),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000 // 10 minutes (formerly cacheTime)
  })

  return query
}

/**
 * TanStack Query mutation for creating a catalog tag
 */
export function useCreateCatalogTag() {
  return useMutation({
    mutationFn: async (variables: {
      databaseId: string
      name: string
      description?: string
    }): Promise<AssetTag> => {
      const response: AxiosResponse<AssetTag> = await axios.post(
        `/api/databases/${variables.databaseId}/catalog/tags`,
        {
          name: variables.name,
          description: variables.description
        }
      )
      return response.data
    }
  })
}

/**
 * TanStack Query mutation for updating a catalog tag
 */
export function useUpdateCatalogTag() {
  const queryClient = useQueryClient()
  const contextsStore = useContextsStore()

  const databaseId = computed<string | null>(() => {
    try {
      return contextsStore.getSelectedContextDatabaseId()
    } catch {
      return null
    }
  })

  return useMutation({
    mutationFn: async (variables: {
      tagId: string
      name?: string
      description?: string
    }): Promise<AssetTag> => {
      const response: AxiosResponse<AssetTag> = await axios.patch(
        `/api/catalogs/tags/${variables.tagId}`,
        {
          name: variables.name,
          description: variables.description
        }
      )
      return response.data
    },
    onMutate: async (variables) => {
      const currentDatabaseId = databaseId.value
      if (!currentDatabaseId) return

      const queryKey = ['catalog', 'tags', currentDatabaseId]

      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey })

      // Snapshot the previous value
      const previousTags = queryClient.getQueryData<AssetTag[]>(queryKey)

      // Optimistically update the cache
      queryClient.setQueryData<AssetTag[]>(queryKey, (oldData) => {
        if (!oldData) return oldData
        return oldData.map((tag) =>
          tag.id === variables.tagId
            ? {
                ...tag,
                name: variables.name ?? tag.name,
                description: variables.description ?? tag.description
              }
            : tag
        )
      })

      return { previousTags, queryKey }
    },
    onError: (_, __, context) => {
      // Rollback on error
      if (context?.previousTags) {
        queryClient.setQueryData(context.queryKey, context.previousTags)
      }
    },
    onSuccess: (updatedTag) => {
      const currentDatabaseId = databaseId.value
      if (!currentDatabaseId) return

      // Update with the actual server response
      queryClient.setQueryData<AssetTag[]>(['catalog', 'tags', currentDatabaseId], (oldData) => {
        if (!oldData) return oldData
        return oldData.map((tag) => (tag.id === updatedTag.id ? updatedTag : tag))
      })
    }
  })
}

/**
 * TanStack Query mutation for deleting a catalog tag
 */
export function useDeleteCatalogTag() {
  const queryClient = useQueryClient()
  const contextsStore = useContextsStore()

  const databaseId = computed<string | null>(() => {
    try {
      return contextsStore.getSelectedContextDatabaseId()
    } catch {
      return null
    }
  })

  return useMutation({
    mutationFn: async (tagId: string): Promise<void> => {
      await axios.delete(`/api/catalogs/tags/${tagId}`)
    },
    onMutate: async (tagId) => {
      const currentDatabaseId = databaseId.value
      if (!currentDatabaseId) return

      const queryKey = ['catalog', 'tags', currentDatabaseId]

      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey })

      // Snapshot the previous value
      const previousTags = queryClient.getQueryData<AssetTag[]>(queryKey)

      // Optimistically remove from cache
      queryClient.setQueryData<AssetTag[]>(queryKey, (oldData) => {
        if (!oldData) return oldData
        return oldData.filter((tag) => tag.id !== tagId)
      })

      return { previousTags, queryKey }
    },
    onError: (_, __, context) => {
      // Rollback on error
      if (context?.previousTags) {
        queryClient.setQueryData(context.queryKey, context.previousTags)
      }
    }
  })
}
