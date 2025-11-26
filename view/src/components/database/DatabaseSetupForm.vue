<template>
  <div class="space-y-6">
    <!-- Step 1: Database Type Selection -->
    <div v-if="currentStep === 0" class="space-y-6">
      <DatabaseTypeSelector
        v-model="selectedEngine"
        :included-types="['postgres', 'mysql', 'snowflake', 'bigquery', 'motherduck', 'oracle']"
        @update:model-value="onDatabaseTypeSelected"
      />
    </div>

    <!-- Step 2: Connection Details -->
    <div v-if="currentStep === 1 && selectedEngine" class="space-y-6">
      <div class="text-center">
        <h2 class="text-2xl font-bold text-foreground mb-2">Database Connection Details</h2>
        <p class="text-muted-foreground">
          Enter your {{ getDatabaseTypeName(selectedEngine) }} connection details to establish a
          secure connection.
        </p>
      </div>

      <DatabaseForm
        class="max-w-lg mx-auto"
        ref="databaseForm"
        mode="create"
        :engine="selectedEngine"
        @connection-tested="onConnectionTested"
        @saved="onDatabaseSaved"
      />
    </div>

    <!-- Navigation Buttons -->
    <div class="flex justify-between items-center mt-8 pt-6 border-t border-border">
      <Button v-if="currentStep > 0" @click="previousStep" variant="secondary">
        <ArrowLeftIcon class="w-4 h-4 mr-2" />
        Previous
      </Button>
      <div v-else></div>

      <Button size="lg" v-if="currentStep < 1" @click="nextStep" :disabled="!canProceedToNextStep">
        Continue
        <ArrowRightIcon class="w-4 h-4 ml-2" />
      </Button>

      <Button
        v-else
        :is-loading="isSaving"
        @click="saveDatabase"
        :disabled="!canProceedToNextStep || isSaving"
        size="lg"
      >
        <template #loading>Saving...</template>
        Complete Setup
        <CheckIcon class="w-4 h-4 ml-2" v-if="!isSaving" />
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button'
import { type Engine, getDatabaseTypeName } from '@/stores/databases'
import { ArrowLeftIcon, ArrowRightIcon } from '@heroicons/vue/24/outline'
import { CheckIcon } from '@heroicons/vue/24/solid'
import { computed, onMounted, ref, watch } from 'vue'
import DatabaseForm from './DatabaseForm.vue'
import DatabaseTypeSelector from './DatabaseTypeSelector.vue'

const emit = defineEmits<{
  'database-saved': [database: any]
  'step-changed': [step: number]
}>()

// State
const currentStep = ref(0)
const selectedEngine = ref<Engine | null>(null)
const isSaving = ref(false)
const connectionTested = ref(false)
const databaseForm = ref<InstanceType<typeof DatabaseForm> | null>(null)

// Computed properties
const canProceedToNextStep = computed(() => {
  switch (currentStep.value) {
    case 0:
      return selectedEngine.value !== null
    case 1:
      return connectionTested.value
    default:
      return false
  }
})

// Methods
const onDatabaseTypeSelected = (engine: Engine) => {
  selectedEngine.value = engine
  // Update the database form's engine
  if (databaseForm.value && databaseForm.value.database) {
    databaseForm.value.database.engine = engine
  }
}

const onConnectionTested = (success: boolean) => {
  connectionTested.value = success
}

const onDatabaseSaved = (database: any) => {
  emit('database-saved', database)
}

const nextStep = () => {
  if (currentStep.value < 1) {
    currentStep.value++
    emit('step-changed', currentStep.value)
  }
}

const previousStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
    connectionTested.value = false
    emit('step-changed', currentStep.value)
  }
}

const saveDatabase = async () => {
  if (!databaseForm.value) return

  isSaving.value = true
  try {
    await databaseForm.value.save()
  } finally {
    isSaving.value = false
  }
}

// Watch for engine changes and update the form
watch(selectedEngine, (newEngine) => {
  if (databaseForm.value && databaseForm.value.database) {
    databaseForm.value.database.engine = newEngine
  }
})

// Emit initial step on mount
onMounted(() => {
  emit('step-changed', currentStep.value)
})
</script>
