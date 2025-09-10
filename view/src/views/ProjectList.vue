<template>
  <div class="max-w-7xl mx-auto px-4">
    <div class="mt-6 flow-root">
      <div v-if="projectsStore.sortedProjects.length === 0" class="text-center">
        <svg
          class="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            vector-effect="non-scaling-stroke"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"
          />
        </svg>
        <h3 class="mt-2 text-sm font-semibold text-gray-900">No projects</h3>
        <p class="mt-1 text-sm text-gray-500">Get started by creating a new project.</p>
      </div>
      <ul role="list" class="divide-y divide-gray-200">
        <li v-for="project in projectsStore.sortedProjects" :key="project.id!" class="py-4">
          <div class="flex items-center space-x-4">
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-gray-900">
                {{ project.id }} - {{ project.name }}
              </p>
              <p class="truncate text-sm text-gray-500">
                {{ project.engine }}
              </p>
            </div>
            <div>
              <router-link
                :to="'/projects/' + project.id"
                class="inline-flex items-center rounded-full border border-gray-300 bg-white px-2.5 py-0.5 text-sm font-medium leading-5 text-gray-700 shadow-xs hover:bg-gray-50"
              >
                Edit
              </router-link>
            </div>
          </div>
        </li>
      </ul>
    </div>
    <div class="mt-6 text-center">
      <router-link
        to="/projects/new"
        href="#"
        class="flex w-full items-center justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-xs hover:bg-gray-50"
      >
        <PlusIcon class="-ml-0.5 mr-1.5 h-5 w-5" aria-hidden="true" />
        New Project
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useProjectsStore } from '@/stores/projects'
import { PlusIcon } from '@heroicons/vue/20/solid'

const projectsStore = useProjectsStore()

projectsStore.fetchProjects({ refresh: true })
</script>
