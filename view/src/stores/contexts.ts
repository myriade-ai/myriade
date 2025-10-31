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
      name: project.name
    }))
    const databaseContexts = databasesStore.databases.map((database: any) => ({
      id: `database-${database.id}`,
      type: 'database' as const, // Use 'as const' for literal type
      name: database.name
    }))
    return [...projectContexts, ...databaseContexts]
  })

  // Computed property to get the selected context object based on ID
  const contextSelected = computed<Context | null>(() => {
    if (!contextSelectedId.value) return null
    return contexts.value.find((context) => context.id === contextSelectedId.value) || null
  })

  // Actions
  let initializationPromise: Promise<void> | null = null

  async function initializeContexts() {
    // Return existing promise if initialization is already in progress
    if (initializationPromise) {
      return initializationPromise
    }

    initializationPromise = (async () => {
      try {
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
      } finally {
        // Reset the promise after completion (success or failure)
        initializationPromise = null
      }
    })()

    return initializationPromise
  }

  // Function to manually set the selected context by ID
  function setSelectedContext(contextId: string | null) {
    contextSelectedId.value = contextId
  }

  // Function to manually set the selected context by object (for backward compatibility)
  function setSelectedContextByObject(context: Context | null) {
    contextSelectedId.value = context?.id || null
  }

  function getDatabaseIdFromContext(contextId: string): string {
    if (contextId.startsWith('project-')) {
      const projectId = contextId.replace('project-', '')
      const project = projectsStore.projects.find(
        (project: any) => String(project.id) === projectId
      )
      const databaseId = project?.databaseId
      if (!databaseId) {
        throw new Error(`Project with id ${contextId} does not have a databaseId`)
      }
      return databaseId
    }
    if (contextId.startsWith('database-')) {
      return contextId.replace('database-', '')
    }
    throw new Error(`Invalid contextId: ${contextId}`)
  }

  function getSelectedContextDatabaseId(): string {
    const contextId = contextSelectedId.value
    if (!contextId) {
      throw new Error('No context selected')
    }
    return getDatabaseIdFromContext(contextId)
  }

  return {
    // State
    contextSelectedId,
    // Getters
    contexts,
    contextSelected, // Returns the full context object based on selected ID
    getDatabaseIdFromContext,
    getSelectedContextDatabaseId,
    // Actions
    initializeContexts,
    setSelectedContext,
    setSelectedContextByObject
  }
})
