<template>
  <div>
    <!-- Query favorite button -->
    <button
      v-if="props.queryId"
      class="text-blue-500 hover:text-blue-700 flex items-center float-right"
      title="Save query to workspace"
      @click="toggleQueryFavorite"
    >
      <StarIconSolid v-if="isQueryFavorite" class="h-4 w-4 text-yellow-500" />
      <StarIcon v-else class="h-4 w-4" />
      <span class="ml-1 hidden lg:inline">{{ isQueryFavorite ? 'saved' : 'save' }}</span>
    </button>
    <BaseEditor :modelValue="sqlQuery" :readOnly="true" />
    <BaseTable :data="rows" :count="count" />
  </div>
</template>

<script lang="ts" setup>
import BaseEditor from '@/components/base/BaseEditor.vue'
import BaseTable from '@/components/base/BaseTable.vue'
import axios from '@/plugins/axios'
import { useQueryStore } from '@/stores/query'
import { StarIcon } from '@heroicons/vue/24/outline'
import { StarIcon as StarIconSolid } from '@heroicons/vue/24/solid'
import { defineProps, onMounted, ref } from 'vue'
const { fetchQuery, fetchQueryResults } = useQueryStore()

const props = defineProps({
  queryId: String,
  databaseId: String
})

const rows = ref([])
const count = ref(0)
const sqlQuery = ref('')
const isQueryFavorite = ref(false)

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
</script>
