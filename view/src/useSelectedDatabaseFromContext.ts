import { useContextsStore } from '@/stores/contexts'
import { useDatabasesStore, type Database } from '@/stores/databases'
import { computed } from 'vue'

export function useSelectedDatabaseFromContext() {
  const contextsStore = useContextsStore()
  const databasesStore = useDatabasesStore()

  const selectedDatabase = computed<Database | null>(() => {
    const context = contextsStore.contextSelected
    if (context && context.type === 'database') {
      const dbId = context.id.replace('database-', '')
      return databasesStore.databases.find((db: Database) => db.id === dbId) || null
    }
    return null
  })

  return { selectedDatabase }
}
