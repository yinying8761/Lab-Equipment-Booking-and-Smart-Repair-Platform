import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '工作台' } },
      { path: 'equipments', name: 'equipments', component: () => import('../views/EquipmentList.vue'), meta: { title: '设备台账' } },
      { path: 'reservations', name: 'reservations', component: () => import('../views/MyReservations.vue'), meta: { title: '我的预约' } },
      { path: 'repairs', name: 'repairs', component: () => import('../views/MyRepairs.vue'), meta: { title: '我的报修' } },
      { path: 'assistant', name: 'assistant', component: () => import('../views/AiAssistant.vue'), meta: { title: '智能助手' } },
      { path: 'admin/equipments', name: 'admin-equipments', component: () => import('../views/admin/AdminEquipment.vue'), meta: { title: '设备管理', admin: true } },
      { path: 'admin/reservations', name: 'admin-reservations', component: () => import('../views/admin/AdminReservations.vue'), meta: { title: '预约审核', admin: true } },
      { path: 'admin/repairs', name: 'admin-repairs', component: () => import('../views/admin/AdminRepairs.vue'), meta: { title: '工单处理', admin: true } },
      { path: 'admin/knowledge', name: 'admin-knowledge', component: () => import('../views/admin/AdminKnowledge.vue'), meta: { title: '知识库管理', admin: true } }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    return true
  }
  if (!auth.token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (!auth.user) {
    const user = await auth.restore()
    if (!user) return { path: '/login' }
  }
  if (to.meta.admin && !auth.isAdmin) {
    return { path: '/dashboard' }
  }
  document.title = `${to.meta.title || '实验室平台'} · LabCare`
  return true
})

export default router
