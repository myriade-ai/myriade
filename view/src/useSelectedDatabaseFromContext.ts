import { useContextsStore } from '@/stores/contexts'
import { useDatabasesStore, type Database } from '@/stores/databases'
import { useProjectsStore } from '@/stores/projects'
import { computed } from 'vue'

export function useSelectedDatabaseFromContext() {
  const contextsStore = useContextsStore()
  const databasesStore = useDatabasesStore()
  const projectsStore = useProjectsStore()

  const selectedDatabase = computed<Database | null>(() => {
    const context = contextsStore.contextSelected
    if (!context) {
      return null
    }

    if (context.type === 'database') {
      const dbId = context.id.replace('database-', '')
      return databasesStore.databases.find((db: Database) => db.id === dbId) || null
    }

    if (context.type === 'project') {
      const projectId = context.id.replace('project-', '')
      const project = projectsStore.projects.find((p: any) => p.id === projectId)
      if (project?.databaseId) {
        return databasesStore.databases.find((db: Database) => db.id === project.databaseId) || null
      }
    }

    return null
  })

  return { selectedDatabase }
}
