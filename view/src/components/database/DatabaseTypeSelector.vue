<template>
  <div>
    <!-- Card Layout (for setup funnel) -->
    <div v-if="layout === 'cards'" class="space-y-4">
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
          class="relative group p-6 bg-white border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md transition-all duration-200 cursor-pointer"
          :class="{
            'border-blue-500 bg-blue-50': modelValue === dbType.value,
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
            class="absolute top-2 right-2 w-5 h-5 text-blue-600"
          />
        </button>
      </div>
    </div>

    <!-- Dropdown Layout (for edit form) -->
    <base-field v-else name="Engine">
      <div class="select">
        <select
          :value="modelValue"
          @change="selectType(($event.target as HTMLSelectElement).value)"
          class="block w-full max-w-lg rounded-md border-gray-300 shadow-xs focus:border-blue-500 focus:ring-blue-500 sm:max-w-xs sm:text-sm"
        >
          <option v-for="dbType in availableTypes" :key="dbType.value" :value="dbType.value">
            {{ dbType.name }}
          </option>
        </select>
      </div>
    </base-field>
  </div>
</template>

<script setup lang="ts">
import BaseField from '@/components/base/BaseField.vue'
import {
  CheckCircleIcon,
  CircleStackIcon,
  CommandLineIcon,
  CubeIcon,
  TableCellsIcon
} from '@heroicons/vue/24/outline'
import { computed } from 'vue'

interface DatabaseType {
  value: string
  name: string
  description: string
  icon: any
  iconBg: string
  iconColor: string
}

interface Props {
  modelValue: string
  layout?: 'cards' | 'dropdown'
  showTitle?: boolean
  includedTypes?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  layout: 'dropdown',
  showTitle: true,
  includedTypes: () => ['postgres', 'mysql', 'snowflake', 'sqlite', 'bigquery']
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const allDatabaseTypes: DatabaseType[] = [
  {
    value: 'postgres',
    name: 'PostgreSQL',
    description: 'Popular open-source database',
    icon: CircleStackIcon,
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600'
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
  }
]

const availableTypes = computed(() => {
  return allDatabaseTypes.filter((type) => props.includedTypes.includes(type.value))
})

const selectType = (value: string) => {
  emit('update:modelValue', value)
}
</script>
