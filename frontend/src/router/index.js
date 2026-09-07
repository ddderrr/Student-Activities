import { createRouter, createWebHistory } from 'vue-router'

import AdminStudentActivities from '../views/Admin/AdminStudentActivities.vue'

const routes = [
  {
    path: '/admin/activities',
    component: AdminStudentActivities
  },

  {
    path: '/',
    redirect: '/admin/activities'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router