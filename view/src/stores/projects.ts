import axios from '@/plugins/axios'
import { defineStore } from 'pinia'
import { computed, ref, type WritableComputedRef } from 'vue'

interface ProjectTable {
  databaseName: string | null
  schemaName: string | null
  tableName: string | null
}

interface Project {
  id: number | null
  name: string
  description: string
  databaseId: number | null
  tables: ProjectTable[]
}

export const useProjectsStore = defineStore('projects', () => {
  // --- state ---
  const projects = ref<Project[]>([])
  const projectSelectedId = ref<number | null>(
    localStorage.getItem('projectId') ? parseInt(localStorage.getItem('projectId') ?? '') : null
  )

  // --- getters ---
  const projectSelected = computed<Project>({
    get: () => {
      return projects.value.find((db) => db.id === projectSelectedId.value) ?? ({} as Project)
    },
    set: (newProject: Project) => {
      projectSelectedId.value = newProject.id
      localStorage.setItem('projectId', String(newProject.id))
    }
  }) as WritableComputedRef<Project>

  const sortedProjects = computed(() => {
    return [...projects.value].sort((a, b) => a.id - b.id)
  })

  // --- actions ---
  async function fetchProjects({ refresh }: { refresh: boolean }) {
    if (projects.value.length > 0 && !refresh) return
    projects.value = await axios.get('/api/projects').then((res) => res.data)
  }

  function fetchProjectTables(projectId: number) {
    return axios.get(`/api/projects/${projectId}/schema`).then((res) => res.data)
  }

  async function selectProjectById(id: number) {
    projectSelectedId.value = id
    localStorage.setItem('projectId', id.toString())
  }

  async function updateProject(id: number, project: Project) {
    return axios.put(`/api/projects/${id}`, project)
  }

  async function createProject(project: Project): Promise<Project> {
    return axios.post('/api/projects', project).then((response) => response.data)
  }

  function deleteProject(id: number) {
    return axios.delete(`/api/projects/${id}`)
  }

  function getProjectById(id: number) {
    return axios
      .get('/api/projects')
      .then((response) => response.data.find((db: Project) => db.id === id))
  }

  function fetchProjectById(projectId: number) {
    return axios.get(`/api/projects/${projectId}`).then((res) => res.data)
  }

  // Return all reactive properties and methods
  return {
    // state
    projects,
    projectSelectedId,

    // getters
    projectSelected,
    sortedProjects,

    // actions
    fetchProjects,
    fetchProjectTables,
    selectProjectById,
    updateProject,
    createProject,
    deleteProject,
    getProjectById,
    fetchProjectById
  }
})
