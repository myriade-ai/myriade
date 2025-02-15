import { ref } from 'vue'

// Initialize Clerk with your Clerk Publishable Key
type User = {
  id: string | null
  email: string | null
  firstName: string | null
  lastName: string | null
  imageUrl: string | null
  isAdmin: boolean
}

export const user = ref<User>({
  id: null,
  email: null,
  firstName: null,
  lastName: null,
  imageUrl: null,
  isAdmin: false,
})
