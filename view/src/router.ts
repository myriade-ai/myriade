import { createWebHistory, createRouter } from 'vue-router'
import { authenticate, user } from './stores/client'
import { loadQuery } from './stores/query'
import { useDatabases } from './stores/databases'
import Editor from './views/Editor.vue'
import DatabaseList from './views/DatabaseList.vue'
import Upload from './views/Upload.vue'
import Chat from './views/ChatPage.vue'
import ProjectList from './views/ProjectList.vue'

function loadView(view: string) {
  return () => import(`./views/${view}.vue`)
}

const { fetchDatabases } = useDatabases()

const routes = [
  {
    path: '/',
    name: 'Chat',
    component: Chat
  },
  {
    path: '/chat/:id',
    name: 'ChatById',
    component: Chat
  },
  {
    path: '/query',
    name: 'Editor',
    component: Editor
  },
  {
    path: '/upload',
    name: 'Upload',
    component: Upload
  },
  {
    path: '/query/:id',
    name: 'Query',
    component: Editor,
    beforeEnter: async (to) => {
      await loadQuery(to.params.id)
      return true
    }
  },
  {
    path: '/databases',
    name: 'DatabaseList',
    component: DatabaseList
  },
  {
    path: '/databases/:id',
    name: 'DatabaseEdit',
    component: loadView('DatabaseEdit')
  },
  {
    path: '/projects',
    name: 'ProjectList',
    component: ProjectList
  },
  {
    path: '/projects/:id',
    name: 'ProjectEdit',
    component: loadView('ProjectEdit')
  }
]

const router = createRouter({
  //history: createWebHistory(import.meta.env.BASE_URL),
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  await authenticate()
  
  // Admin-only routes
  const adminRoutes = ['/databases', '/projects']
  if (adminRoutes.some(route => to.path.startsWith(route)) && !user.value?.isAdmin) {
    next('/')
    return
  }
  
  await fetchDatabases({ refresh: false })
  next()
})

export default router
