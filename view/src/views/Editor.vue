<template>
  <div class="grid grid-cols-12 gap-4 px-4 mx-auto py-4">
    <div class="col-span-3">
      <DatabaseExplorer></DatabaseExplorer>
    </div>
    <div class="col-span-9">
      <BaseQuery />
      <BaseAlert v-if="queryError">
        <template #title> There is an error in the SQL execution 😔 </template>
        {{ queryError }}
      </BaseAlert>
      <BaseTable v-if="queryResults !== null" :data="queryResults" :count="queryCount" />
    </div>
  </div>
</template>

<script setup lang="ts">
import BaseQuery from '@/components/BaseQuery.vue'
import { queryResults, queryError, queryCount } from '../stores/query'
import BaseAlert from '../components/BaseAlert.vue'
import BaseTable from '../components/BaseTable.vue'
import DatabaseExplorer from '../components/DatabaseExplorer.vue'
</script>
