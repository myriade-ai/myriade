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
    <Select v-model="contextsStore.contextSelectedId">
      <SelectTrigger>
        <SelectValue placeholder="Select a context" class="w-42" />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          <SelectLabel>Contexts</SelectLabel>
          <SelectItem
            v-for="context in contextsStore.contexts"
            :key="context.id"
            :value="context.id"
          >
            {{ context.name }}
          </SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>
  </div>
</template>

<script setup lang="ts">
import BaseButton from '@/components/base/BaseButton.vue'
import DatabaseIcon from '@/components/icons/DatabaseIcon.vue'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import { useContextsStore } from '@/stores/contexts'
import { useDatabasesStore } from '@/stores/databases'

import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const databasesStore = useDatabasesStore()

const contextsStore = useContextsStore()

</script>
