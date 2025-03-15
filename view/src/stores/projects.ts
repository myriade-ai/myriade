import axios from '@/plugins/axios'
import type { Ref, WritableComputedRef } from 'vue'
import { computed, ref } from 'vue'

export interface Project {
  id: number
  name: string
  description: string
}

const projects: Ref<Project[]> = ref([])

const fetchProjects = async ({ refresh }: { refresh: boolean }) => {
  if (projects.value.length > 0 && !refresh) return
  projects.value = await axios.get('/api/projects').then((res) => res.data)
}

const projectSelectedId: Ref<number | null> = ref(
  localStorage.getItem('projectId') ? parseInt(localStorage.getItem('projectId') ?? '') : null
)

const projectSelected: WritableComputedRef<Project> = computed({
  get: () => {
    return projects.value.find((db) => db.id === projectSelectedId.value) ?? ({} as Project)
  },
  set: (newProject: Project) => {
    projectSelectedId.value = newProject.id
    localStorage.setItem('projectId', String(newProject.id))
  }
})

const fetchProjectTables = (projectId: number) => {
  return axios.get(`/api/projects/${projectId}/schema`).then((res) => res.data)
}

const selectProjectById = async (id: number) => {
  projectSelectedId.value = id
  localStorage.setItem('projectId', id.toString())
}

const updateProject = async (id: number, project: Project) => {
  return axios.put('/api/projects/' + id, project)
}

const createProject = async (project: Project): Promise<Project> => {
  return axios.post('/api/projects', project).then((response) => response.data)
}

const deleteProject = (id: number) => {
  return axios.delete('/api/projects/' + id)
}

const getProjectById = (id: number) => {
  return axios
    .get('/api/projects/')
    .then((response) => response.data.find((db: Project) => db.id === id))
}

const fetchProjectById = (projectId: number) => {
  return axios.get(`/api/projects/${projectId}`).then((res) => res.data)
}

export const useProjects = () => {
  return {
    fetchProjects,
    projects,
    projectSelected,
    projectSelectedId,
    selectProjectById,
    fetchProjectTables,
    updateProject,
    createProject,
    deleteProject,
    getProjectById,
    fetchProjectById
  }
}
