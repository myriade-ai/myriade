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
      <!--TODO: fix-->
      <BaseBuilder
        v-if="queryResults !== null"
        :context="querySQL"
        :count="queryCount"
        :data="queryResults"
        :visualisationParams="visualisationParams"
        @updateVisualisationParamsEvent="($event) => updateVisualisationParams($event)"
      ></BaseBuilder>
    </div>
  </div>
</template>

<script setup lang="ts">
import BaseBuilder from '@/components/BaseBuilder.vue'
import BaseQuery from '@/components/BaseQuery.vue'
import {
  queryResults,
  querySQL,
  queryError,
  queryCount,
  visualisationParams,
  updateVisualisationParams
} from '../stores/query'
import BaseAlert from '../components/BaseAlert.vue'
import DatabaseExplorer from '../components/DatabaseExplorer.vue'
</script>
