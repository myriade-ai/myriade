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
  // Initialize with null or a sensible default. It will be updated after fetching.
  const contextSelected = useLocalStorage<Context | null>(
    'contextSelected',
    null,
    { serializer: StorageSerializers.object } // Explicitly use JSON serialization
  )

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

  // Actions
  async function initializeContexts() {
    // Fetch data if not already loaded (Pinia might handle this internally if stores are already used)
    // Consider adding checks or using existing store state to see if fetch is needed
    await projectsStore.fetchProjects({ refresh: false }) // Avoid refreshing if data might already be there
    await databasesStore.fetchDatabases({ refresh: false })

    // Update selected context only if it's null/invalid or doesn't exist in the new list
    const currentSelectionValid = contexts.value.some(
      (context) => context.id === contextSelected.value?.id
    )
    if ((!contextSelected.value || !currentSelectionValid) && contexts.value.length > 0) {
      console.log('set default contextSelected')
      contextSelected.value = contexts.value[0]
    }
  }

  // Function to manually set the selected context
  function setSelectedContext(context: Context | null) {
    contextSelected.value = context
  }

  function setSelectedContextById(id: string) {
    const context = contexts.value.find((context) => context.id === id)
    contextSelected.value = context
  }

  return {
    // State
    contextSelected,
    // Getters
    contexts,
    // Actions
    initializeContexts,
    setSelectedContext,
    setSelectedContextById
  }
})
