<template>
  <SignedOut>
    <SignInButton />
  </SignedOut>
  <metainfo>
    <template v-slot:title="{ content }">{{ content }}</template>
  </metainfo>
  <SignedIn>
    <component :is="layout"> </component>
  </SignedIn>
</template>

<script lang="ts" setup>
import { computed, watch } from 'vue'
import { useMeta } from 'vue-meta'
import { useRoute } from 'vue-router'
import { SignedOut, SignedIn, SignInButton } from '@clerk/vue'
import { useAuth, useUser } from '@clerk/vue'
import axios from 'axios'
import { user } from '@/stores/client'

const { getToken } = useAuth()

// Add token to axios instance
axios.interceptors.request.use(async (config) => {
  const token = await getToken.value()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

const { user: userClerk } = useUser();

watch(
  () => userClerk.value,
  (newUserClerk) => {
    if (newUserClerk) {
      user.value = {
        id: newUserClerk.id,
        email: newUserClerk.emailAddresses[0].emailAddress,
        firstName: newUserClerk.firstName,
        lastName: newUserClerk.lastName,
        imageUrl: newUserClerk.imageUrl,
        isAdmin: newUserClerk.organizationMemberships[0].role === "org:admin",
      }
    }
  },
  { immediate: true } // This will run the watcher immediately after setup
)

useMeta({
  title: 'Ada',
  description: 'Explore your data with Ada!',
  htmlAttrs: { lang: 'en' }
})

const layout = computed<string>(() => {
  return `layout-${useRoute().meta.layout || 'default'}`
})
</script>
