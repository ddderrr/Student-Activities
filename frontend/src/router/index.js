import { createRouter, createWebHistory } from 'vue-router'

import AdminStudentActivities from '../views/Admin/AdminStudentActivities.vue'
import AdminParticipantDetails from '../views/Admin/AdminParticipantDetails.vue'

const routes = [
  {
    path: '/admin/activities',
    component: AdminStudentActivities
  },

  {
    path: '/',
    redirect: '/admin/activities'
  }, 
  {
    path: '/admin/activities/:activityId/details',
    component: AdminParticipantDetails
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router