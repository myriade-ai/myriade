import { authGuard } from '@/auth'
import Control from '@/components/Control.vue'
import { useQueryStore } from '@/stores/query'
import { createRouter, createWebHistory } from 'vue-router'

function loadView(view: string) {
  return () => import(`./views/${view}.vue`)
}

const website_routes = [
  {
    path: '/',
    name: 'Home',
    component: loadView('HomePage'),
    meta: { layout: 'empty' }
  }
]

const app_routes = [
  {
    path: '/',
    name: 'NewChat',
    redirect: '/chat/new'
  },
  {
    path: '/chat/:id',
    name: 'ChatPage',
    component: loadView('ChatPage')
  },
  {
    path: '/editor',
    name: 'Editor',
    component: loadView('Editor')
  },
  {
    path: '/upload',
    name: 'Upload',
    component: loadView('Upload')
  },
  {
    path: '/query/:id',
    name: 'Query',
    component: loadView('Editor'),
    beforeEnter: async (to) => {
      const { loadQuery } = useQueryStore()
      await loadQuery(to.params.id)
      return true
    }
  },
  {
    path: '/favorites',
    name: 'Favorites',
    component: loadView('Favorites')
  },
  {
    path: '/databases',
    name: 'DatabaseList',
    component: loadView('DatabaseList')
  },
  {
    path: '/databases/:id',
    name: 'DatabaseEdit',
    component: loadView('DatabaseEdit')
  },
  {
    path: '/issues',
    name: 'IssuesPage',
    component: loadView('Issues')
  },
  {
    path: '/privacy',
    name: 'PrivacyPage',
    component: loadView('PrivacyPage')
  },
  {
    path: '/projects',
    name: 'ProjectList',
    component: loadView('ProjectList')
  },
  {
    path: '/projects/:id',
    name: 'ProjectEdit',
    component: loadView('ProjectEdit')
  },
  {
    path: '/login',
    name: 'Login',
    component: loadView('Login'),
    meta: { requiresGuest: true, layout: 'empty' }
  },
  {
    path: '/user',
    name: 'User',
    component: loadView('User')
  },
  {
    path: '/control',
    name: 'Control',
    component: Control,
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: loadView('NotFound'),
    meta: { requiresGuest: true, layout: 'empty' }
  }
]

let router = null
// If env.APP == 'website', then the routes are homepage
// If env.APP == 'app', then the routes are the application routes
if (import.meta.env.VITE_APP === 'website') {
  router = createRouter({
    history: createWebHistory(),
    routes: website_routes
  })
} else {
  router = createRouter({
    history: createWebHistory(),
    routes: app_routes
  })
  router.beforeEach(authGuard)
}

export default router
