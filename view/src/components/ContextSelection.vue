<template>
  <BaseButton
    v-if="databasesStore.hasOnlyPublicDatabases()"
    @click="router.push('/setup')"
    color="primary"
    class="inline-flex text-sm mr-2 h-10"
  >
    <div class="relative -ml-0.5 h-4 w-4"><DatabaseIcon /></div>
    <span class="hidden sm:inline ml-2">Add Database</span>
  </BaseButton>
  <div class="flex items-center">
    <BaseSelector
      :options="contextsStore.contexts"
      v-model="contextsStore.contextSelectedId"
      @update:modelValue="contextsStore.setSelectedContext"
      class="w-48 h-10"
      placeholder="Select context"
      :disabled="disabled"
    />
  </div>
</template>

<script setup lang="ts">
import BaseButton from '@/components/base/BaseButton.vue'
import BaseSelector from '@/components/base/BaseSelector.vue'
import DatabaseIcon from '@/components/icons/DatabaseIcon.vue'
import { useContextsStore } from '@/stores/contexts'
import { useDatabasesStore } from '@/stores/databases'

import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const databasesStore = useDatabasesStore()

defineProps<{
  disabled?: boolean
}>()

const contextsStore = useContextsStore()

onMounted(() => {
  contextsStore.initializeContexts()
})
</script>
