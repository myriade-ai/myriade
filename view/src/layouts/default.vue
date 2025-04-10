<template>
  <div class="min-h-full">
    <Disclosure as="nav" class="bg-white border-b border-gray-200" v-slot="{ open }">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex text-xl font-bold">
            <div class="flex-shrink-0 flex items-center">
              <a href="/" class="flex items-center">
                <img src="/logo.svg" class="h-8 w-auto" />
                <span class="ml-2">Myriade</span>
              </a>
            </div>
            <div class="hidden sm:-my-px sm:ml-6 sm:flex sm:space-x-8">
              <router-link
                v-for="nav in navigation"
                :key="nav.name"
                :to="nav.href"
                :class="[
                  isRouteActive(nav.href)
                    ? 'border-blue-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700',
                  'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium'
                ]"
                :aria-current="isRouteActive(nav.href) ? 'page' : undefined"
              >
                {{ nav.name }}
              </router-link>
            </div>
          </div>
          <!-- Profile is hidden for now -->
          <!-- <div class="hidden sm:ml-6 sm:flex sm:items-center"> -->
          <div class="hidden">
            <!-- Profile dropdown -->
            <Menu as="div" class="ml-3 relative">
              <div>
                <MenuButton
                  class="max-w-xs bg-white flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <span class="sr-only">Open user menu</span>
                  <img class="h-8 w-8 rounded-full" :src="user?.pictureUrl" alt="" />
                </MenuButton>
              </div>
              <transition
                enter-active-class="transition ease-out duration-200"
                enter-from-class="transform opacity-0 scale-95"
                enter-to-class="transform opacity-100 scale-100"
                leave-active-class="transition ease-in duration-75"
                leave-from-class="transform opacity-100 scale-100"
                leave-to-class="transform opacity-0 scale-95"
              >
                <MenuItems
                  class="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5 focus:outline-none"
                >
                  <MenuItem
                    v-for="item in userNavigation"
                    :key="item.name"
                    @click="item.click()"
                    v-slot="{ active }"
                  >
                    <a
                      :class="[
                        active ? 'bg-gray-100' : '',
                        'block px-4 py-2 text-sm text-gray-700'
                      ]"
                    >
                      {{ item.name }}
                    </a>
                  </MenuItem>
                </MenuItems>
              </transition>
            </Menu>
          </div>
          <div class="-mr-2 flex items-center sm:hidden">
            <!-- Mobile menu button -->
            <DisclosureButton
              class="bg-white inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <span class="sr-only">Open main menu</span>
              <Bars3Icon v-if="!open" class="block h-6 w-6" aria-hidden="true" />
              <XMarkIcon v-else class="block h-6 w-6" aria-hidden="true" />
            </DisclosureButton>
          </div>
        </div>
      </div>

      <DisclosurePanel class="sm:hidden">
        <div class="pt-2 pb-3 space-y-1">
          <DisclosureButton
            v-for="item in navigation"
            :key="item.name"
            as="a"
            :href="item.href"
            :class="[
              item.href == currentPath
                ? 'bg-blue-50 border-blue-500 text-blue-700'
                : 'border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800',
              'block pl-3 pr-4 py-2 border-l-4 text-base font-medium'
            ]"
            :aria-current="item.href == currentPath ? 'page' : undefined"
          >
            {{ item.name }}
          </DisclosureButton>
        </div>
        <div class="pt-4 pb-3 border-t border-gray-200">
          <div class="flex items-center px-4">
            <div class="flex-shrink-0">
              <img class="h-10 w-10 rounded-full" :src="user?.pictureUrl" alt="" />
            </div>
            <div class="ml-3">
              <div class="text-base font-medium text-gray-800">
                {{ user?.name }}
              </div>
              <div class="text-sm font-medium text-gray-500">
                {{ user.email }}
              </div>
            </div>
          </div>
          <div class="mt-3 space-y-1">
            <DisclosureButton
              v-for="item in userNavigation"
              :key="item.name"
              as="button"
              :click="item.click"
              class="block px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
            >
              {{ item.name }}
            </DisclosureButton>
          </div>
        </div>
      </DisclosurePanel>
    </Disclosure>

    <div>
      <Suspense>
        <router-view />
      </Suspense>
    </div>
  </div>
</template>

<script setup lang="ts">
import { user } from '@/stores/auth'
import {
  Disclosure,
  DisclosureButton,
  DisclosurePanel,
  Menu,
  MenuButton,
  MenuItem,
  MenuItems
} from '@headlessui/vue'
import { Bars3Icon, XMarkIcon } from '@heroicons/vue/24/outline'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const currentPath = computed(() => route.path)

const isRouteActive = (navPath: string) => {
  return (
    navPath === currentPath.value ||
    (navPath === '/' && currentPath.value.startsWith('/chat')) ||
    (navPath === '/editor' &&
      (currentPath.value.startsWith('/editor') || currentPath.value.startsWith('/query')))
  )
}

const navigation = computed(() => [
  { name: 'Chat', href: '/' },
  { name: 'Editor', href: '/editor' },
  // Only show these items to admins
  ...(user.value?.isAdmin
    ? [
        { name: 'Databases', href: '/databases' },
        { name: 'Projects', href: '/projects' }
      ]
    : [])
])
</script>
