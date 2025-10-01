<template>
  <div>
    <PageHeader
      title="Projects"
      subtitle="Manage your projects, so you can work on specific problems/topics."
    />
    <div class="px-6 py-4 w-full min-h-screen">
      <div class="max-w-4xl mx-auto">
        <div class="flex items-center gap-4 mb-6">
          <div class="flex-1">
            <Input
              v-model="searchQuery"
              type="text"
              placeholder="Search projects..."
              class="w-full"
            />
          </div>
          <Button as-child>
            <router-link to="/projects/new" class="flex items-center gap-2">
              <PlusIcon class="h-4 w-4" />
              New Project
            </router-link>
          </Button>
        </div>

        <div v-if="filteredProjects.length === 0 && searchQuery === ''" class="text-center py-12">
          <div
            class="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center"
          >
            <svg
              class="w-8 h-8 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2-2H5a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
          <p class="text-gray-500 mb-6">Get started by creating your first project.</p>
          <Button as-child variant="outline">
            <router-link to="/projects/new" class="flex items-center gap-2">
              <PlusIcon class="h-4 w-4" />
              Create your first project
            </router-link>
          </Button>
        </div>

        <div
          v-else-if="filteredProjects.length === 0 && searchQuery !== ''"
          class="text-center py-12"
        >
          <div
            class="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center"
          >
            <svg
              class="w-8 h-8 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900 mb-2">No projects found</h3>
          <p class="text-gray-500 mb-6">No projects match your search for "{{ searchQuery }}"</p>
        </div>

        <div v-else class="grid gap-4">
          <Card
            v-for="project in filteredProjects"
            :key="project.id!"
            class="hover:shadow-md transition-shadow cursor-pointer"
            @click="navigateToProject(project.id!)"
          >
            <CardHeader class="flex items-start justify-between">
              <div class="space-y-2">
                <CardTitle>{{ project.name }}</CardTitle>
                <CardDescription v-if="project.description" class="line-clamp-10 overflow-hidden">
                  {{ project.description }}
                </CardDescription>
              </div>
              <span
                v-if="getProjectDatabase(project)?.engine"
                :class="getEngineColor(getProjectDatabase(project)!.engine!)"
                class="px-2 py-1 rounded-md text-xs font-medium capitalize"
              >
                {{ getProjectDatabase(project)?.engine }}
              </span>
              <span
                v-else
                class="px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800"
              >
                No database
              </span>
            </CardHeader>
          </Card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectsStore } from '@/stores/projects'
import PageHeader from '@/components/PageHeader.vue'
import { useDatabasesStore, type Database, type Engine } from '@/stores/databases'
import { PlusIcon } from '@heroicons/vue/20/solid'
import Button from '@/components/ui/button/Button.vue'
import Card from '@/components/ui/card/Card.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import CardDescription from '@/components/ui/card/CardDescription.vue'
import Input from '@/components/ui/input/Input.vue'

interface Project {
  id: string | null
  name: string
  description: string
  databaseId: string | null
  tables: Array<{
    databaseName: string | null
    schemaName: string | null
    tableName: string | null
  }>
}

const projectsStore = useProjectsStore()
const databasesStore = useDatabasesStore()
const router = useRouter()
const searchQuery = ref('')

projectsStore.fetchProjects({ refresh: true })
databasesStore.fetchDatabases({ refresh: true })

const navigateToProject = (projectId: string) => {
  router.push(`/projects/${projectId}`)
}

const getProjectDatabase = (project: Project): Database | undefined => {
  if (!project.databaseId) return undefined
  return databasesStore.databases.find((db: Database) => db.id === project.databaseId)
}

const getEngineColor = (engine: Engine) => {
  const engineColors: Record<Engine, string> = {
    postgres: 'bg-blue-100 text-blue-800',
    mysql: 'bg-orange-100 text-orange-800',
    snowflake: 'bg-cyan-100 text-cyan-800',
    sqlite: 'bg-gray-100 text-gray-800',
    bigquery: 'bg-yellow-100 text-yellow-800',
    motherduck: 'bg-purple-100 text-purple-800'
  }
  return engineColors[engine] || 'bg-gray-100 text-gray-800'
}

const filteredProjects = computed(() => {
  if (!searchQuery.value.trim()) {
    return projectsStore.sortedProjects
  }

  const query = searchQuery.value.toLowerCase().trim()
  return projectsStore.sortedProjects.filter((project: Project) => {
    const matchesName = project.name.toLowerCase().includes(query)
    const database = getProjectDatabase(project)
    const matchesEngine = database?.engine?.toLowerCase().includes(query) || false

    return matchesName || matchesEngine
  })
})
</script>
