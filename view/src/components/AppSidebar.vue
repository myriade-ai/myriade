<script setup lang="ts">
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar
} from '@/components/ui/sidebar'
import { user, logout } from '@/stores/auth'
import { useContextsStore } from '@/stores/contexts'
import { useConversationsStore } from '@/stores/conversations'
import {
  CalendarCog,
  DatabaseZap,
  FilePenLine,
  FolderHeart,
  HatGlasses,
  Inbox,
  LogOut,
  ShieldCheck,
  SquarePen,
  UserRoundPen
} from 'lucide-vue-next'
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const items: { title: string; url: string; icon: typeof SquarePen; disabled?: boolean }[] = [
  {
    title: 'Control',
    url: '/control',
    icon: ShieldCheck,
    disabled: true
  },
  {
    title: 'Issues',
    url: '/issues',
    icon: Inbox,
    disabled: true
  },
  {
    title: 'Projects',
    url: '/projects',
    icon: CalendarCog
  },
  {
    title: 'Favorites',
    url: '/favorites',
    icon: FolderHeart
  },
  {
    title: 'Editor',
    url: '/editor',
    icon: FilePenLine
  }
]

const store = useConversationsStore()
const contextsStore = useContextsStore()

const projects = computed(() => contextsStore.contexts.filter((c) => c.type === 'project'))
const databases = computed(() => contextsStore.contexts.filter((c) => c.type === 'database'))

const sortedGroup = computed(() => {
  return store.sortedUserConversations
})
const route = useRoute()
const isActive = (id: string) => {
  return route.params.id === id
}
const userInfo = computed(() => {
  if (!user.value?.firstName || !user.value?.lastName) return { userInitials: '??', fullName: '??' }
  return {
    userInitials: `${user.value.firstName[0]}${user.value.lastName[0]}`.toUpperCase(),
    fullName: `${user.value.firstName} ${user.value.lastName}`
  }
})
const userInitials = computed(() => userInfo.value.userInitials)
const fullName = computed(() => userInfo.value.fullName)
const { isMobile } = useSidebar()
</script>

<template>
  <Sidebar>
    <SidebarHeader>
      <div class="shrink-0 flex items-center mb-2 mt-2">
        <router-link to="/" class="flex items-center">
          <img src="/logo.svg?v=3" class="h-8 w-auto hidden sm:inline" />
          <img src="/icon.svg?v=3" class="h-8 w-auto sm:hidden" />
        </router-link>
      </div>
      <Select v-model="contextsStore.contextSelectedId">
        <SelectTrigger class="w-full bg-white">
          <SelectValue placeholder="Contexts" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectLabel>Projects</SelectLabel>
            <SelectItem v-for="context in projects" :key="context.id" :value="context.id">
              {{ context.name }}
            </SelectItem>
          </SelectGroup>
          <SelectGroup>
            <SelectLabel>Databases</SelectLabel>
            <SelectItem v-for="context in databases" :key="context.id" :value="context.id">
              {{ context.name }}
            </SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
    </SidebarHeader>
    <SidebarContent>
      <SidebarGroup>
        <SidebarGroupLabel>Myriad</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton
                asChild
                class="bg-primary text-white hover:text-white hover:bg-primary/70"
              >
                <RouterLink to="chat/new">
                  <SquarePen class="size-4" />
                  <span class="">New chat</span>
                </RouterLink>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem
              v-for="item in items.filter(({ disabled }) => !disabled)"
              :key="item.title"
            >
              <SidebarMenuButton asChild>
                <RouterLink :to="item.url">
                  <component :is="item.icon" />
                  <span class="text-primary">{{ item.title }}</span>
                </RouterLink>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
      <SidebarGroup>
        <SidebarGroupLabel>Chats</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem v-for="conversation in sortedGroup" :key="conversation.id">
              <SidebarMenuButton asChild :isActive="isActive(conversation.id)">
                <RouterLink :to="`/chat/${conversation.id}`">
                  <span class="text-primary">{{ conversation.name }}</span>
                </RouterLink>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarContent>
    <SidebarFooter>
      <SidebarMenu>
        <SidebarMenuItem>
          <DropdownMenu>
            <DropdownMenuTrigger as-child>
              <SidebarMenuButton
                size="lg"
                class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
              >
                <Avatar class="h-8 w-8 rounded-lg">
                  <AvatarImage :src="user.profilePictureUrl ?? ''" :alt="fullName" />
                  <AvatarFallback class="rounded-lg bg-primary text-white">
                    {{ userInitials }}
                  </AvatarFallback>
                </Avatar>
                <div class="grid flex-1 text-left text-sm leading-tight">
                  <span class="truncate font-semibold">{{ fullName }}</span>
                  <span class="truncate text-xs">{{ user.email }}</span>
                </div>
                <ChevronsUpDown class="ml-auto size-4" />
              </SidebarMenuButton>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              class="w-[--reka-dropdown-menu-trigger-width] min-w-56 rounded-lg"
              :side="isMobile ? 'bottom' : 'right'"
              align="end"
              :side-offset="4"
            >
              <DropdownMenuLabel class="p-0 font-normal">
                <div class="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                  <Avatar class="h-8 w-8 rounded-lg">
                    <AvatarImage :src="user.profilePictureUrl ?? ''" :alt="fullName" />
                    <AvatarFallback class="rounded-lg"> {{ userInitials }} </AvatarFallback>
                  </Avatar>
                  <div class="grid flex-1 text-left text-sm leading-tight">
                    <span class="truncate font-semibold">{{ fullName }}</span>
                    <span class="truncate text-xs">{{ user.email }}</span>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuGroup>
                <DropdownMenuItem asChild>
                  <RouterLink to="/profile"> <UserRoundPen /><span>Profile</span></RouterLink>
                </DropdownMenuItem>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuGroup>
                <DropdownMenuItem asChild>
                  <RouterLink to="/databases"> <DatabaseZap /><span>Databases</span></RouterLink>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <RouterLink to="/privacy"> <HatGlasses /><span>Zk Protection</span></RouterLink>
                </DropdownMenuItem>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <button @click="logout" class="w-full flex items-center">
                  <LogOut />
                  <span>Log out</span>
                </button>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarFooter>
  </Sidebar>
</template>
