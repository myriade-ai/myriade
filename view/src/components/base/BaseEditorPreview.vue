<template>
  <div>
    <!-- Query favorite button -->
    <div class="-mr-2">
      <Button
        v-if="props.queryId"
        class="flex items-center float-right"
        title="Save query to workspace"
        variant="ghost"
        size="icon"
        @click="toggleQueryFavorite"
      >
        <Star :class="isQueryFavorite ? 'text-yellow-500 fill-yellow-500' : ''" />
      </Button>
    </div>
    <BaseEditor :modelValue="sqlQuery" :readOnly="true" />
    <DataTable :data="rows" :count="count" class="mt-4" />
  </div>
</template>

<script lang="ts" setup>
import BaseEditor from '@/components/base/BaseEditor.vue'
import DataTable from '@/components/DataTable.vue'
import { useQueryEditor } from '@/composables/useQueryEditor'
import axios from '@/plugins/axios'
import { Star } from 'lucide-vue-next'
import { onMounted, ref } from 'vue'
import { Button } from '../ui/button'
const { fetchQuery, fetchQueryResults } = useQueryEditor()

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
    const query = await fetchQuery(props.queryId!)
    isQueryFavorite.value = query.is_favorite
    sqlQuery.value = query.sql
    const result = await fetchQueryResults(props.queryId!)
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
