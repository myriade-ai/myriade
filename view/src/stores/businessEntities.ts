import axios from '@/plugins/axios'
import { useContextsStore } from '@/stores/contexts'
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export interface BusinessEntity {
  id: number
  name: string
  completeness: number | null
  quality_score: number | null
  recommendations: string[] | null
  review_date: string | null
  report: any
  review_conversation_id: number | null
}

export const useBusinessEntitiesStore = defineStore('businessEntities', () => {
  const entities = ref<BusinessEntity[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const contextsStore = useContextsStore()

  const fetchEntities = async () => {
    loading.value = true
    error.value = null

    try {
      const contextId = contextsStore.contextSelected?.id
      if (!contextId) {
        entities.value = []
        loading.value = false
        return
      }
      const response = await axios.get('/api/business-entities', {
        params: { contextId }
      })
      entities.value = response.data
    } catch (e) {
      error.value =
        e instanceof Error ? e.message : 'An error occurred while fetching business entities'
      console.error('Error fetching business entities:', e)
      entities.value = []
    } finally {
      loading.value = false
    }
  }

  watch(
    () => contextsStore.contextSelected,
    (newContext, oldContext) => {
      if (newContext?.id !== oldContext?.id) {
        fetchEntities()
      }
    },
    { deep: true }
  )

  if (contextsStore.contextSelected?.id) {
    fetchEntities()
  }

  return {
    entities,
    loading,
    error,
    fetchEntities
  }
})
