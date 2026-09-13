import { createRouter, createWebHistory } from 'vue-router'

// Login
import StudentLogin from '../views/Login/StudentLogin.vue'
import AdminLogin from '../views/Login/AdminLogin.vue'

// Admin
import AdminStudentActivities from '../views/Admin/AdminStudentActivities.vue'
import AdminParticipantDetails from '../views/Admin/AdminParticipantDetails.vue'
import AdminCreateActivity from '../views/Admin/AdminCreateActivity.vue'
import AdminDashboard from '../views/Admin/AdminDashboard.vue'
import AdminStudentSkills from '../views/Admin/AdminStudentSkills.vue'
import AdminApproval from '../views/Admin/AdminApproval.vue'


const routes = [

  // =========================
  // Login
  // =========================

  {
    path: '/',
    name: 'StudentLogin',
    component: StudentLogin
  },

  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: AdminLogin
  },


  // =========================
  // Admin
  // =========================

  {
    path: '/admin/dashboard',
    name: 'AdminDashboard',
    component: AdminDashboard
  },

  {
    path: '/admin/student-skills',
    name: 'AdminStudentSkills',
    component: AdminStudentSkills
  },

  {
    path: '/admin/activities',
    name: 'AdminActivities',
    component: AdminStudentActivities
  },

  {
    path: '/admin/activities/create',
    name: 'AdminCreateActivity',
    component: AdminCreateActivity
  },

  {
    path: '/admin/activities/:activityId/details',
    name: 'AdminParticipantDetails',
    component: AdminParticipantDetails
  },

  {
    path: '/admin/approvals',
    name: 'AdminApproval',
    component: AdminApproval
  }

]


const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router