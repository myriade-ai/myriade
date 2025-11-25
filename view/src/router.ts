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
    path: '/organization-restricted',
    name: 'OrganizationRestricted',
    component: loadView('OrganizationRestricted'),
    meta: { layout: 'empty', requiresGuest: true }
  },
  {
    path: '/setup',
    name: 'SetupFunnel',
    component: loadView('SetupFunnel'),
    meta: { layout: 'empty' }
  },
  {
    path: '/github/callback',
    name: 'GithubCallback',
    component: loadView('GithubCallback'),
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
    component: loadView('ChatPage'),
    meta: { requiresContext: true }
  },
  {
    path: '/editor',
    name: 'Editor',
    component: loadView('Editor'),
    meta: { requiresContext: true }
  },
  {
    path: '/query/:id',
    name: 'Query',
    component: loadView('Editor'),
    meta: { requiresContext: true },
    beforeEnter: async (to) => {
      const { loadQuery } = useQueryEditor()
      await loadQuery(Array.isArray(to.params.id) ? to.params.id[0] : to.params.id)
      return true
    }
  },
  {
    path: '/favorites',
    name: 'Favorites',
    component: loadView('Favorites'),
    meta: { requiresContext: true }
  },
  {
    path: '/databases',
    name: 'DatabaseList',
    component: loadView('DatabaseList'),
    meta: { requiresContext: true }
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
    component: loadView('DatabaseEdit'),
    meta: { requiresContext: true }
  },
  {
    path: '/issues',
    name: 'IssuesPage',
    component: loadView('Issues'),
    meta: { requiresContext: true }
  },
  {
    path: '/privacy',
    name: 'PrivacyPage',
    component: loadView('PrivacyPage')
  },
  {
    path: '/projects',
    name: 'ProjectList',
    component: loadView('ProjectList'),
    meta: { requiresContext: true }
  },
  {
    path: '/projects/:id',
    name: 'ProjectEdit',
    component: loadView('ProjectEdit'),
    meta: { requiresContext: true }
  },
  {
    path: '/control',
    name: 'Control',
    component: Control,
    meta: { requiresAuth: true, requiresContext: true }
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
    component: loadView('ProfilePage'),
    meta: { requiresContext: true }
  },
  {
    path: '/catalog/assets',
    name: 'AssetPage',
    component: loadView('AssetPage'),
    meta: { requiresContext: true }
  },
  {
    path: '/catalog/terms',
    name: 'TermPage',
    component: loadView('TermPage'),
    meta: { requiresContext: true }
  },
  {
    path: '/catalog/tags',
    name: 'AssetTagPage',
    component: loadView('AssetTagPage'),
    meta: { requiresContext: true }
  },
  {
    path: '/catalog/smart-scan',
    name: 'SmartScanPage',
    component: loadView('SmartScanPage'),
    meta: { requiresContext: true }
  },
  {
    path: '/documents',
    name: 'DocumentList',
    component: loadView('DocumentList'),
    meta: { requiresContext: true }
  },
  {
    path: '/documents/:id',
    name: 'DocumentView',
    component: loadView('DocumentView'),
    meta: { requiresContext: true }
  },
  {
    path: '/catalog/overview',
    name: 'CatalogOverview',
    component: loadView('CatalogDashboardPage'),
    meta: { requiresContext: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes: routes
})
router.beforeEach(authGuard)
router.beforeEach(redirectToWelcome)

// Initialize contexts for routes that require them
router.beforeEach(async (to) => {
  if (to.meta.requiresContext) {
    const contextsStore = useContextsStore()
    await contextsStore.initializeContexts()
  }
})

export default router
