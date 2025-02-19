<template>
  <div>
    <h1>Auth Success</h1>
    <p>{{ user.email }}</p>
    {{ user }}
    <button @click="logout">Logout</button>
  </div>
</template>

<script setup lang="ts">
import { fetchUser, user, logout } from '@/stores/auth'
import { onMounted } from 'vue'

onMounted(async () => {
  await fetchUser()
})
</script>
