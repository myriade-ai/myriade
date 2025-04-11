<template>
  <div class="flex h-screen">
    <TransitionRoot as="template" :show="sidebarOpen">
      <Dialog class="relative z-50 lg:hidden" @close="sidebarOpen = false">
        <TransitionChild
          as="template"
          enter="transition-opacity ease-linear duration-300"
          enter-from="opacity-0"
          enter-to="opacity-100"
          leave="transition-opacity ease-linear duration-300"
          leave-from="opacity-100"
          leave-to="opacity-0"
        >
          <div class="fixed inset-0 bg-gray-900/80" />
        </TransitionChild>

        <div class="fixed inset-0 flex">
          <TransitionChild
            as="template"
            enter="transition ease-in-out duration-300 transform"
            enter-from="-translate-x-full"
            enter-to="translate-x-0"
            leave="transition ease-in-out duration-300 transform"
            leave-from="translate-x-0"
            leave-to="-translate-x-full"
          >
            <DialogPanel class="relative mr-16 flex w-full max-w-xs flex-1">
              <TransitionChild
                as="template"
                enter="ease-in-out duration-300"
                enter-from="opacity-0"
                enter-to="opacity-100"
                leave="ease-in-out duration-300"
                leave-from="opacity-100"
                leave-to="opacity-0"
              >
                <div class="absolute left-full top-0 flex w-16 justify-center pt-5">
                  <button type="button" class="-m-2.5 p-2.5" @click="sidebarOpen = false">
                    <span class="sr-only">Close sidebar</span>
                    <XMarkIcon class="h-6 w-6 text-white" aria-hidden="true" />
                  </button>
                </div>
              </TransitionChild>
              <!-- Sidebar component, swap this element with another sidebar if you like -->
              <div class="grow">
                <ConversationList class="h-full" />
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </Dialog>
    </TransitionRoot>

    <!-- Static sidebar for desktop -->
    <div class="hidden lg:flex lg:w-72 lg:flex-col">
      <!-- Sidebar component, swap this element with another sidebar if you like -->
      <div class="grow">
        <ConversationList class="h-screen" />
      </div>
    </div>
    <div class="w-full h-screen flex justify-center items-center px-2">
      <div class="flex flex-col h-screen w-full">
        <!-- only when swipe right can trigger the callback -->
        <!-- Dropdown to select the dabase to query -->
        <label class="block text-gray-700 text-sm font-bold mb-2" for="database"> Context </label>
        <!-- TODO: have name like 'Everest > Packages' ?? -->
        <BaseSelector
          :options="contextsStore.contexts"
          v-model="contextsStore.contextSelected"
          @update:modelValue="contextsStore.setSelectedContext"
          class="w-full"
          placeholder="Select a database"
          :disabled="conversationId"
        />
        <br />
        <Chat v-touch:swipe.right="onSwipe" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BaseSelector from '@/components/base/BaseSelector.vue'
import Chat from '@/components/Chat.vue'
import ConversationList from '@/components/ConversationList.vue'
import { useContextsStore } from '@/stores/contexts'
import { Dialog, DialogPanel, TransitionChild, TransitionRoot } from '@headlessui/vue'
import { XMarkIcon } from '@heroicons/vue/24/solid'
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
const sidebarOpen = ref(false)

const onSwipe = () => {
  sidebarOpen.value = true
}

const route = useRoute()

const contextsStore = useContextsStore()
await contextsStore.initializeContexts()
const conversationId = computed(() => {
  if (route.params.id === 'new') {
    return null
  }
  return Number(route.params.id)
})
</script>
