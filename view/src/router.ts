import { createWebHistory, createRouter } from 'vue-router'
import { loadQuery } from './stores/query'
import Editor from './views/Editor.vue'
import DatabaseList from './views/DatabaseList.vue'
import Upload from './views/Upload.vue'
import Chat from './views/ChatPage.vue'
import ProjectList from './views/ProjectList.vue'
import Login from '@/views/Login.vue'
import User from '@/views/User.vue'
import { authGuard } from '@/auth'

function loadView(view: string) {
  return () => import(`./views/${view}.vue`)
}

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
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresGuest: true }
  },
  {
    path: '/user',
    name: 'User',
    component: User
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(authGuard)

export default router
