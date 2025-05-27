<template>
  <div class="flex h-screen">
    <!-- Left Panel: Business Entities Grid -->
    <div class="flex-1 bg-gray-100 p-4 overflow-y-auto">
      <h2 class="text-xl font-semibold mb-3 inline-block">Business Entities</h2>
      <button
        @click="startAutoScan"
        class="mb-3 ml-3 px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        :disabled="store.entities.length > 0"
        :class="{
          'opacity-50 cursor-not-allowed': store.entities.length > 0
        }"
      >
        Scan auto
      </button>

      <!-- Loading State -->
      <div v-if="store.loading" class="flex justify-center items-center h-32">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>

      <!-- Error State -->
      <div v-else-if="store.error" class="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path
                fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clip-rule="evenodd"
              />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">Error loading business entities</h3>
            <div class="mt-2 text-sm text-red-700">{{ store.error }}</div>
          </div>
        </div>
      </div>

      <!-- Search Input -->
      <div v-else class="mb-4 relative">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="Search entities..."
          class="w-full pl-10 pr-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
        <svg
          class="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M21 21l-4.35-4.35M17 10a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>

      <!-- Entity Cards Grid -->
      <div
        v-if="!store.loading && !store.error"
        class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      >
        <div
          v-for="entity in filteredEntities"
          :key="entity.id"
          class="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow cursor-pointer"
          @click="selectEntity(entity)"
        >
          <!-- Entity Header -->
          <div class="flex justify-between items-start mb-3">
            <h3 class="text-lg font-semibold text-gray-800">{{ entity.name }}</h3>
            <span v-if="entity.review_date" class="text-sm text-gray-500">{{
              formatDate(entity.review_date)
            }}</span>
            <span v-else class="text-sm text-gray-400">Not scanned</span>
          </div>

          <!-- Definition and Table Ref -->
          <div v-if="entity.definition || entity.table_ref" class="mb-3 text-sm text-gray-600">
            <p v-if="entity.definition" :title="entity.definition">
              <strong>Definition:</strong> {{ entity.definition }}
            </p>
            <p v-if="entity.table_ref" class="truncate" :title="entity.table_ref">
              <strong>Table:</strong> {{ entity.table_ref }}
            </p>
          </div>

          <!-- Unscanned State -->
          <div v-if="!entity.completeness && !entity.quality_score" class="text-center py-4">
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
            <h3 class="mt-2 text-sm font-medium text-gray-900">Not Scanned</h3>
            <p class="mt-1 text-sm text-gray-500">This entity hasn't been analyzed yet.</p>
            <button
              @click.stop="startAnalysis(entity)"
              class="mt-3 inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Start Analysis
            </button>
          </div>

          <!-- Scanned State -->
          <template v-else>
            <!-- Quality Metrics -->
            <div class="grid grid-cols-2 gap-4 mb-4">
              <div class="text-center">
                <div class="text-sm text-gray-600 mb-1">Completeness</div>
                <div class="relative">
                  <div class="h-2 bg-gray-200 rounded-full">
                    <div
                      class="h-2 rounded-full"
                      :class="getQualityColor(entity.completeness || 0)"
                      :style="{ width: `${entity.completeness || 0}%` }"
                    ></div>
                  </div>
                  <span class="text-sm font-medium mt-1 block"
                    >{{ entity.completeness || 0 }}%</span
                  >
                </div>
              </div>
              <div class="text-center">
                <div class="text-sm text-gray-600 mb-1">Quality Score</div>
                <div class="relative">
                  <div class="h-2 bg-gray-200 rounded-full">
                    <div
                      class="h-2 rounded-full"
                      :class="getQualityColor(entity.quality_score || 0)"
                      :style="{ width: `${entity.quality_score || 0}%` }"
                    ></div>
                  </div>
                  <span class="text-sm font-medium mt-1 block"
                    >{{ entity.quality_score || 0 }}%</span
                  >
                </div>
              </div>
            </div>

            <!-- Recommendations Preview -->
            <div v-if="entity.issues && entity.issues.length > 0" class="mt-3">
              <h4 class="text-sm font-medium text-gray-700 mb-2">Top Issues</h4>
              <ul class="text-sm text-gray-600 space-y-1">
                <li
                  v-for="(rec, index) in entity.issues.slice(0, 2)"
                  :key="index"
                  class="flex items-start"
                >
                  <svg
                    class="h-4 w-4 text-indigo-500 mr-2 mt-0.5 flex-shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                  <span>{{ rec.title }}</span>
                </li>
                <li v-if="entity.issues.length > 2" class="text-indigo-600 text-sm">
                  +{{ entity.issues.length - 2 }} more issues
                </li>
              </ul>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useContextsStore } from '../stores/contexts'
import { useConversationsStore } from '../stores/conversations'
import { useQualityStore, type BusinessEntity } from '../stores/quality'

const store = useQualityStore()
const conversationsStore = useConversationsStore()
const contextsStore = useContextsStore()
const router = useRouter()
const searchQuery = ref('')
const selectedEntity = ref<BusinessEntity | null>(null)

const filteredEntities = computed(() => {
  return store.entities.filter((entity: BusinessEntity) =>
    entity.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const getQualityColor = (score: number) => {
  if (score >= 90) return 'bg-green-500'
  if (score >= 70) return 'bg-yellow-500'
  return 'bg-red-500'
}

const formatDate = (dateString: string | null) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString()
}

const selectEntity = (entity: BusinessEntity) => {
  selectedEntity.value = entity
  if (entity.review_conversation_id) {
    router.push({ name: 'ChatPage', params: { id: entity.review_conversation_id.toString() } })
  }
}

const startAutoScan = async () => {
  try {
    if (!contextsStore.contextSelected) {
      throw new Error('No context selected')
    }
    const conversation = await conversationsStore.createConversation(
      contextsStore.contextSelected.id
    )
    await conversationsStore.sendMessage(
      conversation.id,
      'Can you explore the database, save to memory what you understood about the business, data structure,  and create missing business entities',
      'text'
    )
    router.push({ name: 'ChatPage', params: { id: conversation.id.toString() } })
  } catch (error) {
    console.error('Error starting auto scan:', error)
    // You might want to show an error message to the user here
  }
}

const startAnalysis = async (entity: BusinessEntity) => {
  try {
    if (!contextsStore.contextSelected) {
      throw new Error('No context selected')
    }
    const conversation = await conversationsStore.createConversation(
      contextsStore.contextSelected.id
    )
    await conversationsStore.sendMessage(
      conversation.id,
      `Verify quality of the business entity "${entity.name}".\nCreate issues if you find any.\nThen update the semantic catalog business entity report/quality score`,
      'text'
    )
    router.push({ name: 'ChatPage', params: { id: conversation.id.toString() } })
  } catch (error) {
    console.error('Error starting analysis:', error)
    // You might want to show an error message to the user here
  }
}

watch(searchQuery, () => {
  // Add any additional search logic if needed
})

onMounted(() => {
  store.fetchEntities()
})
</script>

<style scoped>
.overflow-y-auto {
  overflow-y: auto;
}
</style>
