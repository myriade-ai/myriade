<template>
  <div class="grid grid-cols-12 gap-4 px-4 mx-auto py-4">
    <div class="col-span-3">
      <DatabaseExplorer></DatabaseExplorer>
    </div>
    <div class="col-span-9">
      <BaseQuery />
      <BaseAlert v-if="queryStore.queryError">
        <template #title> There is an error in the SQL execution 😔 </template>
        {{ queryStore.queryError }}
      </BaseAlert>
      <BaseTable
        v-if="queryStore.queryResults !== null"
        :data="queryStore.queryResults"
        :count="queryStore.queryCount"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import BaseAlert from '@/components/base/BaseAlert.vue'
import BaseQuery from '@/components/base/BaseQuery.vue'
import BaseTable from '@/components/base/BaseTable.vue'
import DatabaseExplorer from '@/components/DatabaseExplorer.vue'
import { useQueryStore } from '@/stores/query'

const queryStore = useQueryStore()
</script>
