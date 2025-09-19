import { authGuard, redirectToWelcome } from '@/auth'
import Control from '@/components/Control.vue'
import { useQueryEditor } from '@/composables/useQueryEditor'
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useContextsStore } from './stores/contexts'

function loadView(view: string) {
  return () => import(`./views/${view}.vue`)
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'NewChat',
    redirect: '/chat/new'
  },
  {
    path: '/welcome',
    name: 'Welcome',
    component: loadView('WelcomePage'),
    meta: { layout: 'empty' }
  },
  {
    path: '/login',
    name: 'Login',
    component: loadView('Login'),
    meta: { layout: 'empty', requiresGuest: true }
  },
  {
    path: '/setup',
    name: 'SetupFunnel',
    component: loadView('SetupFunnel'),
    meta: { layout: 'empty' }
  },
  {
    path: '/subscribe',
    name: 'Subscribe',
    component: loadView('Subscribe'),
    meta: { layout: 'empty' }
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
    path: '/query/:id',
    name: 'Query',
    component: loadView('Editor'),
    beforeEnter: async (to) => {
      const { loadQuery } = useQueryEditor()
      await loadQuery(Array.isArray(to.params.id) ? to.params.id[0] : to.params.id)
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
    path: '/databases/new',
    name: 'DatabaseNew',
    component: loadView('SetupFunnel'),
    meta: { layout: 'empty' }
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
    component: loadView('ProjectEdit'),
    beforeEnter: async () => {
      const contextsStore = useContextsStore()
      await contextsStore.initializeContexts()
      return true
    }
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
  },
  {
    path: '/profile',
    name: 'Profile',
    component: loadView('ProfilePage')
  },
  {
    path: '/catalog',
    name: 'CatalogPage',
    component: loadView('CatalogPage')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes: routes
})
router.beforeEach(authGuard)
router.beforeEach(redirectToWelcome)

export default router
