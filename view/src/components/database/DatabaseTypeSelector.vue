<template>
  <div>
    <!-- Card Layout (for setup funnel) -->
    <div class="space-y-4">
      <div class="text-center" v-if="showTitle">
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Select Your Database Type</h2>
        <p class="text-gray-600">
          Select the database you'd like to connect to start using Myriade's AI capabilities.
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
        <button
          v-for="dbType in availableTypes"
          :key="dbType.value"
          @click="selectType(dbType.value)"
          class="relative group p-6 bg-white border border-gray-200 rounded-lg hover:border-primary-500 hover:shadow-md transition-all duration-200 cursor-pointer"
          :class="{
            'border-primary-500 bg-primary-50': modelValue === dbType.value,
            'hover:bg-gray-50': modelValue !== dbType.value
          }"
        >
          <div class="flex flex-col items-center space-y-3">
            <div
              class="w-12 h-12 flex items-center justify-center rounded-lg"
              :class="dbType.iconBg"
            >
              <component :is="dbType.icon" class="w-6 h-6" :class="dbType.iconColor" />
            </div>
            <h3 class="text-sm font-medium text-gray-900">{{ dbType.name }}</h3>
            <p class="text-xs text-gray-500 text-center">{{ dbType.description }}</p>
          </div>
          <CheckCircleIcon
            v-if="modelValue === dbType.value"
            class="absolute top-2 right-2 w-5 h-5 text-primary-600"
          />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Engine } from '@/stores/databases'
import type { Component } from 'vue'
import {
  CheckCircleIcon,
  CircleStackIcon,
  CommandLineIcon,
  CubeIcon,
  TableCellsIcon
} from '@heroicons/vue/24/outline'
import { computed } from 'vue'

interface DatabaseType {
  value: Engine
  name: string
  description: string
  icon: Component
  iconBg: string
  iconColor: string
}

interface Props {
  modelValue: Engine | null
  showTitle?: boolean
  includedTypes?: Engine[]
}

const props = withDefaults(defineProps<Props>(), {
  showTitle: true,
  includedTypes: () => ['postgres', 'mysql', 'snowflake', 'sqlite', 'bigquery', 'motherduck', 'oracle']
})

const emit = defineEmits<{
  'update:modelValue': [value: Engine]
}>()

const allDatabaseTypes: DatabaseType[] = [
  {
    value: 'postgres',
    name: 'PostgreSQL',
    description: 'Popular open-source database',
    icon: CircleStackIcon,
    iconBg: 'bg-primary-100',
    iconColor: 'text-primary-600'
  },
  {
    value: 'mysql',
    name: 'MySQL',
    description: "World's most popular database",
    icon: TableCellsIcon,
    iconBg: 'bg-orange-100',
    iconColor: 'text-orange-600'
  },
  {
    value: 'snowflake',
    name: 'Snowflake',
    description: 'Cloud data platform',
    icon: CubeIcon,
    iconBg: 'bg-cyan-100',
    iconColor: 'text-cyan-600'
  },
  {
    value: 'sqlite',
    name: 'SQLite',
    description: 'Lightweight embedded database',
    icon: CircleStackIcon,
    iconBg: 'bg-gray-100',
    iconColor: 'text-gray-600'
  },
  {
    value: 'bigquery',
    name: 'BigQuery',
    description: "Google's data warehouse",
    icon: CommandLineIcon,
    iconBg: 'bg-green-100',
    iconColor: 'text-green-600'
  },
  {
    value: 'motherduck',
    name: 'MotherDuck',
    description: 'Serverless data warehouse',
    icon: CommandLineIcon,
    iconBg: 'bg-purple-100',
    iconColor: 'text-purple-600'
  },
  {
    value: 'oracle',
    name: 'Oracle',
    description: 'Enterprise database system',
    icon: CircleStackIcon,
    iconBg: 'bg-red-100',
    iconColor: 'text-red-600'
  }
]

const availableTypes = computed(() => {
  return allDatabaseTypes.filter((type) => props.includedTypes.includes(type.value))
})

const selectType = (value: Engine) => {
  emit('update:modelValue', value)
}
</script>
