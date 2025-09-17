<template>
  <div>
    <PageHeader title="Issues" />
    <div class="px-4 pt-4">
    <!-- Search and Filters -->
    <div class="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div class="relative flex-grow max-w-md">
        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <input
          type="text"
          v-model="searchQuery"
          placeholder="Search issues..."
          class="block w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md shadow-sm focus:border-primary-500 focus:outline-none focus:ring-primary-500 sm:text-sm"
        />
      </div>
      <div class="flex items-center space-x-2 text-sm text-gray-600">
        <span
          >{{ filteredIssues.length }} {{ filteredIssues.length === 1 ? 'issue' : 'issues' }}</span
        >
        <button
          v-if="searchQuery"
          @click="searchQuery = ''"
          class="text-primary-600 hover:text-primary-800"
        >
          Clear search
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="mb-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
      <!-- Entity Filter -->
      <div>
        <label for="entity-filter" class="block text-sm font-medium text-gray-700 mb-1"
          >Entity</label
        >
        <select
          id="entity-filter"
          v-model="selectedEntity"
          class="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md shadow-sm"
        >
          <option value="">All Entities</option>
          <option v-for="entity in store.entities" :key="entity.id" :value="entity.id">
            {{ entity.name }}
          </option>
        </select>
      </div>

      <!-- Status Filter -->
      <div>
        <label for="status-filter" class="block text-sm font-medium text-gray-700 mb-1"
          >Status</label
        >
        <select
          id="status-filter"
          v-model="selectedStatus"
          class="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md shadow-sm"
        >
          <option value="">All Statuses</option>
          <option value="OPEN">Open</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="RESOLVED">Resolved</option>
          <option value="CLOSED">Closed</option>
        </select>
      </div>

      <!-- Scope Filter -->
      <div>
        <label for="scope-filter" class="block text-sm font-medium text-gray-700 mb-1">Scope</label>
        <select
          id="scope-filter"
          v-model="selectedScope"
          class="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md shadow-sm"
        >
          <option value="">All Scopes</option>
          <option value="DATA">Data</option>
          <option value="BUSINESS">Business</option>
          <option value="BOTH">Both</option>
          <option value="UNKNOWN">Unknown</option>
        </select>
      </div>

      <!-- Clear Filters Button -->
      <div>
        <button
          @click="clearFilters"
          class="w-full sm:w-auto inline-flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          Clear Filters
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="store.loadingIssues" class="flex justify-center items-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      <p class="ml-3 text-gray-600">Loading issues...</p>
    </div>

    <!-- Error State -->
    <div
      v-else-if="store.errorIssues"
      class="bg-error-100 border border-error-400 text-error-700 px-4 py-3 rounded relative mb-6"
      role="alert"
    >
      <strong class="font-bold">Error!</strong>
      <span class="block sm:inline">{{ store.errorIssues }}</span>
    </div>

    <!-- Card-based Issue List -->
    <div v-else-if="filteredIssues.length > 0" class="space-y-4">
      <!-- Action Notification -->
      <div
        v-if="notification"
        class="mb-4 p-3 rounded-md shadow text-sm flex items-center"
        :class="
          notification.type === 'success'
            ? 'bg-green-100 text-green-800'
            : 'bg-error-100 text-error-800'
        "
      >
        <svg
          v-if="notification.type === 'success'"
          class="h-5 w-5 mr-2 flex-shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M5 13l4 4L19 7"
          />
        </svg>
        <svg
          v-else
          class="h-5 w-5 mr-2 flex-shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
        {{ notification.message }}
      </div>

      <!-- Each Issue Card -->
      <div
        v-for="issue in filteredIssues"
        :key="issue.id"
        class="bg-white rounded-lg shadow-md overflow-hidden"
      >
        <!-- Issue Header -->
        <div
          class="p-4 cursor-pointer border-b"
          :class="{ 'bg-primary-50': expandedIssue?.id === issue.id }"
          @click="toggleExpand(issue.id)"
        >
          <!-- Mobile layout -->
          <div class="flex flex-col space-y-2 sm:hidden">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div
                  :class="getPriorityBadgeClass(issue.severity)"
                  class="w-5 h-5 rounded-full flex-shrink-0"
                ></div>
                <h3 class="text-base font-medium text-gray-900 line-clamp-1">{{ issue.title }}</h3>
              </div>
              <svg
                class="h-5 w-5 text-gray-400 transform transition-transform duration-200 flex-shrink-0"
                :class="{ 'rotate-180': expandedIssue?.id === issue.id }"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </div>
            <div class="flex flex-wrap gap-2 text-xs">
              <span class="bg-gray-100 text-gray-800 font-medium px-2 py-1 rounded">
                {{ getEntityName(issue.business_entity_id) }}
              </span>
              <span
                :class="getStatusBadgeClass(issue.status)"
                class="font-medium px-2 py-1 rounded"
              >
                {{ issue.status }}
              </span>
              <span
                class="bg-primary-100 text-primary-800 text-xs font-medium ml-2 px-2.5 py-1 rounded"
                v-if="issue.scope"
              >
                {{ issue.scope }}
              </span>
            </div>
          </div>

          <!-- Desktop layout -->
          <div class="hidden sm:flex sm:justify-between sm:items-center">
            <div class="flex items-center space-x-3">
              <div
                :class="getPriorityBadgeClass(issue.severity)"
                class="w-5 h-5 rounded-full flex-shrink-0"
              ></div>
              <h3 class="text-lg font-medium text-gray-900">{{ issue.title }}</h3>
            </div>
            <div class="flex items-center">
              <!-- Entity Badge -->
              <span class="bg-gray-100 text-gray-800 text-xs font-medium mr-4 px-2.5 py-1 rounded">
                {{ getEntityName(issue.business_entity_id) }}
              </span>
              <!-- Status Badge -->
              <span
                :class="getStatusBadgeClass(issue.status)"
                class="text-xs font-medium mr-4 px-2.5 py-1 rounded"
              >
                {{ issue.status }}
              </span>
              <!-- Scope Badge -->
              <span
                v-if="issue.scope"
                class="bg-primary-100 text-primary-800 text-xs font-medium mr-4 px-2.5 py-1 rounded"
              >
                {{ issue.scope }}
              </span>
              <!-- Expand/Collapse Icon -->
              <svg
                class="h-5 w-5 text-gray-400 transform transition-transform duration-200"
                :class="{ 'rotate-180': expandedIssue?.id === issue.id }"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </div>
          </div>
        </div>

        <!-- Issue Details (Expanded Section) -->
        <div v-if="expandedIssue?.id === issue.id" class="border-t border-gray-100">
          <!-- View Mode -->
          <div v-if="expandedIssue.mode === 'view'" class="p-4 sm:p-5">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-2">
              <h4 class="text-base font-medium text-gray-900">Issue Details</h4>
              <button
                @click.stop="switchToEditMode(issue)"
                class="inline-flex items-center text-sm px-3 py-1.5 border border-gray-300 rounded-md text-primary-700 hover:bg-primary-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <svg class="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                  />
                </svg>
                Edit
              </button>
            </div>

            <!-- Mobile layout: stacked -->
            <div class="sm:hidden space-y-4">
              <div class="bg-gray-50 p-4 rounded-md">
                <p class="text-xs uppercase tracking-wide font-medium text-gray-500 mb-2">
                  Description
                </p>
                <MarkdownDisplay
                  class="text-sm text-gray-800"
                  :content="issue.description"
                ></MarkdownDisplay>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div class="bg-gray-50 p-3 rounded-md">
                  <p class="text-xs uppercase tracking-wide font-medium text-gray-500 mb-1">
                    Severity
                  </p>
                  <p class="text-sm text-gray-800 flex items-center">
                    <span
                      :class="getPriorityDotClass(issue.severity)"
                      class="inline-block w-3 h-3 rounded-full mr-1.5"
                    ></span>
                    {{ issue.severity }}
                  </p>
                </div>

                <div class="bg-gray-50 p-3 rounded-md">
                  <p class="text-xs uppercase tracking-wide font-medium text-gray-500 mb-1">
                    Status
                  </p>
                  <p :class="getStatusTextClass(issue.status)" class="text-sm font-medium">
                    {{ issue.status }}
                  </p>
                </div>
              </div>

              <div class="grid grid-cols-1 gap-3">
                <div class="bg-gray-50 p-3 rounded-md">
                  <p class="text-xs uppercase tracking-wide font-medium text-gray-500 mb-1">
                    Associated Entity
                  </p>
                  <p class="text-sm text-gray-800">{{ getEntityName(issue.business_entity_id) }}</p>
                </div>

                <div class="bg-gray-50 p-3 rounded-md">
                  <p class="text-xs uppercase tracking-wide font-medium text-gray-500 mb-1">
                    Scope
                  </p>
                  <p class="text-sm text-gray-800">{{ issue.scope }}</p>
                </div>

                <div class="bg-gray-50 p-3 rounded-md">
                  <p class="text-xs uppercase tracking-wide font-medium text-gray-500 mb-1">
                    Database ID
                  </p>
                  <p class="text-sm text-gray-800">{{ issue.database_id }}</p>
                </div>

                <div class="bg-gray-50 p-3 rounded-md">
                  <p class="text-xs uppercase tracking-wide font-medium text-gray-500 mb-1">
                    Message ID
                  </p>
                  <p class="text-sm text-gray-800">{{ issue.message_id }}</p>
                </div>
              </div>
            </div>

            <!-- Desktop layout: two columns -->
            <div class="hidden sm:grid grid-cols-1 lg:grid-cols-3 gap-6">
              <!-- Left side: Metadata -->
              <div class="space-y-4 lg:col-span-1">
                <div class="bg-gray-50 p-3 rounded-md">
                  <p class="text-xs uppercase tracking-wide font-medium text-gray-500 mb-1">
                    Severity
                  </p>
                  <p class="text-sm text-gray-800 flex items-center">
                    <span
                      :class="getPriorityDotClass(issue.severity)"
                      class="inline-block w-3 h-3 rounded-full mr-1.5"
                    ></span>
                    {{ issue.severity }}
                  </p>
                </div>

                <div class="bg-gray-50 p-3 rounded-md">
                  <p class="text-xs uppercase tracking-wide font-medium text-gray-500 mb-1">
                    Status
                  </p>
                  <p :class="getStatusTextClass(issue.status)" class="text-sm font-medium">
                    {{ issue.status }}
                  </p>
                </div>

                <div class="bg-gray-50 p-3 rounded-md">
                  <p class="text-xs uppercase tracking-wide font-medium text-gray-500 mb-1">
                    Associated Entity
                  </p>
                  <p class="text-sm text-gray-800">{{ getEntityName(issue.business_entity_id) }}</p>
                </div>

                <div class="bg-gray-50 p-3 rounded-md">
                  <p class="text-xs uppercase tracking-wide font-medium text-gray-500 mb-1">
                    Scope
                  </p>
                  <p class="text-sm text-gray-800">{{ issue.scope }}</p>
                </div>

                <div class="bg-gray-50 p-3 rounded-md">
                  <p class="text-xs uppercase tracking-wide font-medium text-gray-500 mb-1">
                    Database ID
                  </p>
                  <p class="text-sm text-gray-800">{{ issue.database_id }}</p>
                </div>

                <div class="bg-gray-50 p-3 rounded-md">
                  <p class="text-xs uppercase tracking-wide font-medium text-gray-500 mb-1">
                    Message ID
                  </p>
                  <p class="text-sm text-gray-800">{{ issue.message_id }}</p>
                </div>
              </div>

              <!-- Right side: Description -->
              <div class="lg:col-span-2">
                <div class="bg-gray-50 p-4 rounded-md h-full">
                  <p class="text-xs uppercase tracking-wide font-medium text-gray-500 mb-2">
                    Description
                  </p>
                  <MarkdownDisplay
                    class="text-sm text-gray-800"
                    :content="issue.description"
                  ></MarkdownDisplay>
                </div>
              </div>
            </div>
          </div>

          <!-- Edit Mode -->
          <div v-else-if="expandedIssue.mode === 'edit' && formState" class="p-4 sm:p-5">
            <form @submit.prevent="saveIssueChanges" class="space-y-6">
              <div>
                <label for="edit-title" class="block text-sm font-medium text-gray-700 mb-1">
                  Title
                </label>
                <input
                  type="text"
                  id="edit-title"
                  v-model="formState.title"
                  class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm p-2"
                  placeholder="Issue title"
                />
              </div>

              <!-- Mobile layout: stacked -->
              <div class="sm:hidden space-y-4">
                <div>
                  <label
                    for="mobile-edit-description"
                    class="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Description
                  </label>
                  <textarea
                    id="mobile-edit-description"
                    v-model="formState.description"
                    rows="6"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm p-2"
                    placeholder="Detailed description of the issue"
                  ></textarea>
                </div>

                <div>
                  <label
                    for="mobile-edit-severity"
                    class="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Severity
                  </label>
                  <select
                    id="mobile-edit-severity"
                    v-model="formState.severity"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm p-2"
                  >
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                    <option value="CRITICAL">Critical</option>
                  </select>
                </div>

                <div>
                  <label
                    for="mobile-edit-status"
                    class="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Status
                  </label>
                  <select
                    id="mobile-edit-status"
                    v-model="formState.status"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm p-2"
                  >
                    <option value="OPEN">Open</option>
                    <option value="IN_PROGRESS">In Progress</option>
                    <option value="RESOLVED">Resolved</option>
                    <option value="CLOSED">Closed</option>
                  </select>
                </div>

                <div>
                  <label
                    for="mobile-edit-scope"
                    class="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Scope
                  </label>
                  <select
                    id="mobile-edit-scope"
                    v-model="formState.scope"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm p-2"
                  >
                    <option value="DATA">Data</option>
                    <option value="BUSINESS">Business</option>
                    <option value="BOTH">Both</option>
                    <option value="UNKNOWN">Unknown</option>
                  </select>
                </div>
              </div>

              <!-- Desktop layout: two columns -->
              <div class="hidden sm:grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Left column: Form fields -->
                <div class="space-y-4 lg:col-span-1">
                  <div>
                    <label for="edit-severity" class="block text-sm font-medium text-gray-700 mb-1">
                      Severity
                    </label>
                    <select
                      id="edit-severity"
                      v-model="formState.severity"
                      class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm p-2"
                    >
                      <option value="HIGH">High</option>
                      <option value="MEDIUM">Medium</option>
                      <option value="LOW">Low</option>
                      <option value="CRITICAL">Critical</option>
                    </select>
                  </div>

                  <div>
                    <label for="edit-status" class="block text-sm font-medium text-gray-700 mb-1">
                      Status
                    </label>
                    <select
                      id="edit-status"
                      v-model="formState.status"
                      class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm p-2"
                    >
                      <option value="OPEN">Open</option>
                      <option value="IN_PROGRESS">In Progress</option>
                      <option value="RESOLVED">Resolved</option>
                      <option value="CLOSED">Closed</option>
                    </select>
                  </div>

                  <div>
                    <label for="edit-scope" class="block text-sm font-medium text-gray-700 mb-1">
                      Scope
                    </label>
                    <select
                      id="edit-scope"
                      v-model="formState.scope"
                      class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm p-2"
                    >
                      <option value="DATA">Data</option>
                      <option value="BUSINESS">Business</option>
                      <option value="BOTH">Both</option>
                      <option value="UNKNOWN">Unknown</option>
                    </select>
                  </div>
                </div>

                <!-- Right column: Description -->
                <div class="lg:col-span-2">
                  <label
                    for="edit-description"
                    class="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Description
                  </label>
                  <textarea
                    id="edit-description"
                    v-model="formState.description"
                    rows="8"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm p-2"
                    placeholder="Detailed description of the issue"
                  ></textarea>
                </div>
              </div>

              <div
                class="flex flex-col sm:flex-row justify-end space-y-2 sm:space-y-0 sm:space-x-3 pt-4 border-t border-gray-100"
              >
                <button
                  type="button"
                  @click.stop="cancelEditMode"
                  class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 w-full sm:w-auto"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 flex items-center justify-center w-full sm:w-auto"
                  :disabled="saving"
                >
                  <svg
                    v-if="saving"
                    class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      class="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      stroke-width="4"
                    ></circle>
                    <path
                      class="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  {{ saving ? 'Saving...' : 'Save Changes' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>

    <!-- No Issues State (with search distinction) -->
    <div
      v-else-if="searchQuery && sortedIssues.length > 0"
      class="text-center py-10 bg-white shadow-md rounded-lg"
    >
      <svg
        class="mx-auto h-12 w-12 text-gray-400"
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
      <h3 class="mt-2 text-sm font-medium text-gray-900">No matching issues</h3>
      <p class="mt-1 text-sm text-gray-500">Try adjusting your search query.</p>
      <button
        @click="searchQuery = ''"
        class="mt-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
      >
        Clear search
      </button>
    </div>

    <!-- No Issues State (when no issues at all) -->
    <div v-else class="text-center py-10 bg-gray-100 shadow-md rounded-lg">
      <svg
        class="mx-auto h-12 w-12 text-gray-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">No Issues Found</h3>
      <p class="mt-1 text-sm text-gray-500">There are currently no issues to display.</p>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import MarkdownDisplay from '@/components/MarkdownDisplay.vue'
import PageHeader from '@/components/PageHeader.vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useQualityStore, type Issue } from '../stores/quality'

const store = useQualityStore()

// Search and filter state
const searchQuery = ref('')
const selectedEntity = ref<number | string>('') // Can be number (ID) or empty string for all
const selectedStatus = ref<string>('')
const selectedScope = ref<string>('')

// State for expanded row and its mode ('view' or 'edit')
const expandedIssue = ref<{ id: string; mode: 'view' | 'edit' } | null>(null)
// State for the form data when editing (deep copy of the issue)
const formState = ref<Issue | null>(null)
// Loading state for save operation
const saving = ref(false)
// Notification state
const notification = ref<{ type: 'success' | 'error'; message: string } | null>(null)

// Rename priorityOrder to severityOrder and use issue.severity
const severityOrder: Record<string, number> = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3
}

const sortedIssues = computed(() => {
  return [...store.issues].sort((a, b) => {
    const severityA = a.severity?.toUpperCase() || ''
    const severityB = b.severity?.toUpperCase() || ''
    return (severityOrder[severityA] || 99) - (severityOrder[severityB] || 99)
  })
})

const filteredIssues = computed(() => {
  let issuesToFilter = [...sortedIssues.value]

  // Apply entity filter
  if (selectedEntity.value) {
    issuesToFilter = issuesToFilter.filter(
      (issue) => issue.business_entity_id === selectedEntity.value
    )
  }

  // Apply status filter
  if (selectedStatus.value) {
    issuesToFilter = issuesToFilter.filter((issue) => issue.status === selectedStatus.value)
  }

  // Apply scope filter
  if (selectedScope.value) {
    issuesToFilter = issuesToFilter.filter((issue) => issue.scope === selectedScope.value)
  }

  // Apply search query
  if (!searchQuery.value.trim()) return issuesToFilter

  const query = searchQuery.value.toLowerCase().trim()

  return issuesToFilter.filter((issue) => {
    // Search in title
    if (issue.title.toLowerCase().includes(query)) return true

    // Search in description
    if (issue.description.toLowerCase().includes(query)) return true

    // Search in status
    if (issue.status.toLowerCase().includes(query)) return true

    // Search in severity
    if (issue.severity && issue.severity.toLowerCase().includes(query)) return true

    // Search in scope
    if (issue.scope && issue.scope.toLowerCase().includes(query)) return true

    // Search in entity name
    const entityName = getEntityName(issue.business_entity_id).toLowerCase()
    if (entityName.includes(query)) return true

    return false
  })
})

const getEntityName = (entityId: string | undefined | null): string => {
  if (entityId === undefined || entityId === null) return 'N/A'
  const entity = store.entities.find((e) => e.id === entityId)
  return entity ? entity.name : `ID: ${entityId}`
}

const toggleExpand = (issueId: string) => {
  if (expandedIssue.value?.id === issueId) {
    expandedIssue.value = null // Collapse if already expanded
    formState.value = null
  } else {
    expandedIssue.value = { id: issueId, mode: 'view' } // Expand in view mode
    formState.value = null
  }
}

const switchToEditMode = (issue: Issue) => {
  if (expandedIssue.value?.id === issue.id) {
    formState.value = JSON.parse(JSON.stringify(issue)) // Deep copy for editing
    expandedIssue.value.mode = 'edit'
  }
}

const cancelEditMode = () => {
  if (expandedIssue.value) {
    expandedIssue.value.mode = 'view'
    formState.value = null
  }
}

const saveIssueChanges = async () => {
  if (formState.value && expandedIssue.value) {
    try {
      saving.value = true
      await store.updateIssue(formState.value)

      // Find the original issue in the store.issues and update it
      const index = store.issues.findIndex((i) => i.id === formState.value!.id)
      if (index !== -1) {
        store.issues[index] = JSON.parse(JSON.stringify(formState.value))
      }

      expandedIssue.value.mode = 'view' // Switch back to view mode

      // Show success notification
      notification.value = {
        type: 'success',
        message: 'Issue updated successfully'
      }
    } catch (error) {
      console.error('Failed to save issue changes:', error)
      // Show error notification
      notification.value = {
        type: 'error',
        message: 'Failed to update issue. Please try again.'
      }
    } finally {
      saving.value = false

      // Auto-dismiss notification after 3 seconds
      setTimeout(() => {
        notification.value = null
      }, 3000)
    }
  }
}

// Helper functions for styling based on priority and status
const getPriorityBadgeClass = (priority: string) => {
  const p = priority?.toUpperCase() || ''
  if (p === 'CRITICAL') return 'bg-pink-600' // Added CRITICAL
  if (p === 'HIGH') return 'bg-error-500'
  if (p === 'MEDIUM') return 'bg-amber-400'
  return 'bg-green-500' // LOW or other
}

const getPriorityDotClass = (priority: string) => {
  const p = priority?.toUpperCase() || ''
  if (p === 'CRITICAL') return 'bg-error-600' // Added CRITICAL
  if (p === 'HIGH') return 'bg-error-500'
  if (p === 'MEDIUM') return 'bg-warning-500'
  return 'bg-success-500' // LOW or other
}

const getStatusBadgeClass = (status: string) => {
  const s = status?.toUpperCase() || ''
  if (s === 'OPEN') return 'bg-info-100 text-info-800'
  if (s === 'IN_PROGRESS') return 'bg-warning-100 text-warning-800'
  if (s === 'RESOLVED') return 'bg-success-100 text-success-800'
  if (s === 'CLOSED' || s === 'DONE') return 'bg-neutral-100 text-neutral-800'
  return 'bg-neutral-100 text-neutral-800'
}

const getStatusTextClass = (status: string) => {
  const s = status?.toUpperCase() || ''
  if (s === 'OPEN') return 'text-primary-700'
  if (s === 'IN_PROGRESS') return 'text-yellow-700'
  if (s === 'RESOLVED') return 'text-green-700'
  if (s === 'CLOSED' || s === 'DONE') return 'text-gray-700'
  return 'text-gray-700'
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedEntity.value = ''
  selectedStatus.value = ''
  selectedScope.value = ''
}

onMounted(() => {
  if (!store.issues.length && !store.loadingIssues) {
    store.fetchIssues()
  }
  if (!store.entities.length && !store.loading) {
    // Fetch entities if not already loaded
    store.fetchEntities()
  }
})

// Clear notification when changing issues
watch(expandedIssue, () => {
  notification.value = null
})
</script>

<style>
.line-clamp-1 {
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}
</style>
