import { useDatabasesStore } from '@/stores/databases'
import { useProjectsStore } from '@/stores/projects'
import { StorageSerializers, useLocalStorage } from '@vueuse/core'
import { defineStore } from 'pinia'
import { computed } from 'vue'

// Define the type for a context item
interface Context {
  id: string
  type: 'project' | 'database'
  name: string
}

export const useContextsStore = defineStore('contexts', () => {
  const projectsStore = useProjectsStore()
  const databasesStore = useDatabasesStore()

  // State
  // Store only the context ID instead of the full object
  const contextSelectedId = useLocalStorage<string | null>('contextSelectedId', null, {
    serializer: StorageSerializers.string
  })

  // Getters
  const contexts = computed<Context[]>(() => {
    const projectContexts = projectsStore.projects.map((project: any) => ({
      id: `project-${project.id}`,
      type: 'project' as const, // Use 'as const' for literal type
      name: `project > ${project.name}`
    }))
    const databaseContexts = databasesStore.databases.map((database: any) => ({
      id: `database-${database.id}`,
      type: 'database' as const, // Use 'as const' for literal type
      name: `database > ${database.name}`
    }))
    return [...projectContexts, ...databaseContexts]
  })

  // Computed property to get the selected context object based on ID
  const contextSelected = computed<Context | null>(() => {
    if (!contextSelectedId.value) return null
    return contexts.value.find((context) => context.id === contextSelectedId.value) || null
  })

  // Actions
  async function initializeContexts() {
    // Fetch data if not already loaded (Pinia might handle this internally if stores are already used)
    // Consider adding checks or using existing store state to see if fetch is needed
    await projectsStore.fetchProjects({ refresh: false }) // Avoid refreshing if data might already be there
    await databasesStore.fetchDatabases({ refresh: false })

    // Update selected context only if it's null/invalid or doesn't exist in the new list
    const currentSelectionValid = contexts.value.some(
      (context) => context.id === contextSelectedId.value
    )

    if ((!contextSelectedId.value || !currentSelectionValid) && contexts.value.length > 0) {
      contextSelectedId.value = contexts.value[0].id
    }
  }

  // Function to manually set the selected context by ID
  function setSelectedContext(contextId: string | null) {
    contextSelectedId.value = contextId
  }

  // Function to manually set the selected context by object (for backward compatibility)
  function setSelectedContextByObject(context: Context | null) {
    contextSelectedId.value = context?.id || null
  }

  return {
    // State
    contextSelectedId,
    // Getters
    contexts,
    contextSelected, // Returns the full context object based on selected ID
    // Actions
    initializeContexts,
    setSelectedContext,
    setSelectedContextByObject
  }
})
