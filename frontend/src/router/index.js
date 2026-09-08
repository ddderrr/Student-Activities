import { createRouter, createWebHistory } from 'vue-router'

import AdminStudentActivities from '../views/Admin/AdminStudentActivities.vue'
import AdminParticipantDetails from '../views/Admin/AdminParticipantDetails.vue'
import AdminCreateActivity from '../views/Admin/AdminCreateActivity.vue'
import AdminApproval from '../views/Admin/AdminApproval.vue'
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
  },
  {
    path: '/admin/activities/create',
    component: AdminCreateActivity
  },
  {
    path: '/admin/approvals',
    component: AdminApproval
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router