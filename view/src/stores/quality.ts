import axios from '@/plugins/axios'
import { useContextsStore } from '@/stores/contexts'
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export interface Issue {
  id: string
  title: string
  description: string
  severity: string
  scope: string
  status: string
  database_id: number
  message_id: number
  business_entity_id: number
}

export interface BusinessEntity {
  id: number
  name: string
  definition?: string
  table_ref?: string
  completeness: number | null
  quality_score: number | null
  review_date: string | null
  report: any
  review_conversation_id: number | null
  issues: Issue[] | null
}

export const useQualityStore = defineStore('quality', () => {
  const entities = ref<BusinessEntity[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const issues = ref<Issue[]>([])
  const loadingIssues = ref(false)
  const errorIssues = ref<string | null>(null)
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

  const fetchIssues = async () => {
    loadingIssues.value = true
    errorIssues.value = null
    try {
      const contextId = contextsStore.contextSelected?.id
      if (!contextId) {
        issues.value = []
        loadingIssues.value = false
        return
      }
      const response = await axios.get('/api/issues', {
        params: { contextId } // Assuming issues are also context-dependent
      })
      issues.value = response.data
    } catch (e) {
      errorIssues.value = e instanceof Error ? e.message : 'An error occurred while fetching issues'
      console.error('Error fetching issues:', e)
      issues.value = []
    } finally {
      loadingIssues.value = false
    }
  }

  const updateIssue = async (updatedIssue: Issue) => {
    try {
      const response = await axios.put(`/api/issues/${updatedIssue.id}`, updatedIssue)
      const index = issues.value.findIndex((issue) => issue.id === updatedIssue.id)
      if (index !== -1) {
        issues.value[index] = response.data
      }
      // Optionally, re-fetch or handle errors if the backend doesn't return the updated issue
      return response.data
    } catch (e) {
      console.error('Error updating issue:', e)
      // Propagate the error or set an error state
      throw e
    }
  }

  watch(
    () => contextsStore.contextSelected,
    (newContext, oldContext) => {
      if (newContext?.id !== oldContext?.id) {
        fetchEntities()
        fetchIssues() // Fetch issues when context changes
      }
    },
    { deep: true }
  )

  if (contextsStore.contextSelected?.id) {
    fetchEntities()
    fetchIssues() // Initial fetch if context is already selected
  }

  return {
    entities,
    loading,
    error,
    fetchEntities,
    issues,
    loadingIssues,
    errorIssues,
    fetchIssues,
    updateIssue
  }
})
