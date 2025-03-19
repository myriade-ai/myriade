import { authGuard } from '@/auth'
import Login from '@/views/Login.vue'
import User from '@/views/User.vue'
import { createRouter, createWebHistory } from 'vue-router'
import { loadQuery } from './stores/query'
import Chat from './views/ChatPage.vue'
import DatabaseList from './views/DatabaseList.vue'
import Editor from './views/Editor.vue'
import ProjectList from './views/ProjectList.vue'
import Upload from './views/Upload.vue'

function loadView(view: string) {
  return () => import(`./views/${view}.vue`)
}

const routes = [
  {
    path: '/',
    redirect: '/chat/new'
  },
  {
    path: '/chat/:id',
    name: 'Chat',
    component: Chat
  },
  {
    path: '/editor',
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