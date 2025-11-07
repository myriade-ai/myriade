import axios from '@/plugins/axios'
import { defineStore } from 'pinia'
import { computed, ref, type WritableComputedRef } from 'vue'

export interface ProjectTable {
  databaseName: string | null
  schemaName: string | null
  tableName: string | null
}

export interface Project {
  id: string | null
  name: string
  description: string
  databaseId: string | null
  tables: ProjectTable[]
}

export const useProjectsStore = defineStore('projects', () => {
  // --- state ---
  const projects = ref<Project[]>([])
  const projectSelectedId = ref<string | null>(localStorage.getItem('projectId') ?? null)

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

  function fetchProjectTables(projectId: string) {
    return axios.get(`/api/projects/${projectId}/schema`).then((res) => res.data)
  }

  async function selectProjectById(id: string) {
    projectSelectedId.value = id
    localStorage.setItem('projectId', id.toString())
  }

  async function updateProject(id: string, project: Project) {
    return axios.put(`/api/projects/${id}`, project)
  }

  async function createProject(project: Project): Promise<Project> {
    return axios.post('/api/projects', project).then((response) => response.data)
  }

  function deleteProject(id: string) {
    return axios.delete(`/api/projects/${id}`)
  }

  function getProjectById(id: string) {
    return axios
      .get('/api/projects')
      .then((response) => response.data.find((db: Project) => db.id === id))
  }

  function fetchProjectById(projectId: string) {
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
