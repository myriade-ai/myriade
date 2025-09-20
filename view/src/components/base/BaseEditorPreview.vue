<template>
  <div>
    <div class="flex justify-between items-center mb-2">
      <!-- Query favorite button -->
      <button
        v-if="props.queryId"
        class="text-primary-500 hover:text-primary-700 flex items-center"
        title="Save query to workspace"
        @click="toggleQueryFavorite"
      >
        <StarIconSolid v-if="isQueryFavorite" class="h-4 w-4 text-yellow-500" />
        <StarIcon v-else class="h-4 w-4" />
        <span class="ml-1 hidden lg:inline">{{ isQueryFavorite ? 'saved' : 'save' }}</span>
      </button>
      
      <!-- Query cancel button -->
      <button
        v-if="props.queryId && queriesStore.canBeCancelled(props.queryId)"
        class="text-red-500 hover:text-red-700 flex items-center"
        title="Cancel running query"
        @click="handleCancelQuery"
        :disabled="isCancelling"
      >
        <XMarkIcon class="h-4 w-4" />
        <span class="ml-1 hidden lg:inline">{{ isCancelling ? 'Cancelling...' : 'Cancel' }}</span>
      </button>
    </div>
    
    <BaseEditor :modelValue="sqlQuery" :readOnly="true" />
    <BaseTable :data="rows" :count="count" />
  </div>
</template>

<script lang="ts" setup>
import BaseEditor from '@/components/base/BaseEditor.vue'
import BaseTable from '@/components/base/BaseTable.vue'
import axios from '@/plugins/axios'
import { useQueryEditor } from '@/composables/useQueryEditor'
import { useQueriesStore } from '@/stores/queries'
import { StarIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import { StarIcon as StarIconSolid } from '@heroicons/vue/24/solid'
import { defineProps, onMounted, ref } from 'vue'
const { fetchQuery, fetchQueryResults } = useQueryEditor()
const queriesStore = useQueriesStore()

const props = defineProps({
  queryId: String,
  databaseId: String
})

const rows = ref([])
const count = ref(0)
const sqlQuery = ref('')
const isQueryFavorite = ref(false)
const isCancelling = ref(false)

onMounted(async () => {
  try {
    const query = await fetchQuery(props.queryId)
    isQueryFavorite.value = query.is_favorite
    sqlQuery.value = query.sql
    const result = await fetchQueryResults(props.queryId)
    rows.value = result.rows
    count.value = result.count
  } catch (error) {
    console.error('Error fetching data:', error)
  }
})

// TODO: switch to store when Query Store will be cleaned
const toggleQueryFavorite = async () => {
  try {
    const response = await axios.post(`/api/query/${props.queryId}/favorite`)
    isQueryFavorite.value = response.data.is_favorite
  } catch (error) {
    console.error('Error toggling query favorite status:', error)
  }
}

const handleCancelQuery = async () => {
  if (!props.queryId) return
  
  try {
    isCancelling.value = true
    const success = await queriesStore.cancelQuery(props.queryId)
    if (!success) {
      console.error('Failed to cancel query')
    }
  } catch (error) {
    console.error('Error cancelling query:', error)
  } finally {
    isCancelling.value = false
  }
}
</script>
