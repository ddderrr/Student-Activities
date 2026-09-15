import { createRouter, createWebHistory } from 'vue-router'

// =========================
// Login
// =========================

import StudentLogin from '../views/Login/StudentLogin.vue'
import AdminLogin from '../views/Login/AdminLogin.vue'


// =========================
// Admin
// =========================

import AdminStudentActivities from '../views/Admin/AdminStudentActivities.vue'
import AdminParticipantDetails from '../views/Admin/AdminParticipantDetails.vue'
import AdminCreateActivity from '../views/Admin/AdminCreateActivity.vue'
import AdminDashboard from '../views/Admin/AdminDashboard.vue'
import AdminStudentSkills from '../views/Admin/AdminStudentSkills.vue'
import AdminApproval from '../views/Admin/AdminApproval.vue'
import AdminSettings from '../views/Admin/AdminSettings.vue'


// =========================
// Student
// =========================

import StudentLayout from '../layouts/StudentLayout.vue'
import StudentActivities from '../views/Student/StudentActivities.vue'
import StudentSkills from '../views/Student/StudentSkills.vue'
import StudentExternalActivity from '../views/Student/StudentExternalActivity.vue'
import StudentTranscript from '../views/Student/StudentTranscript.vue'


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
  path: '/admin/settings',
  name: 'AdminSettings',
  component: AdminSettings
  },
  
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
  },


  // =========================
  // Student
  // =========================

  {
    path: '/student',
    component: StudentLayout,

    children: [

      // /student
      // ↓
      // /student/activities

      {
        path: '',
        redirect: '/student/activities'
      },


      // My Activities

      {
        path: 'activities',
        name: 'StudentActivities',
        component: StudentActivities
      },


      // My Skills

      {
        path: 'skills',
        name: 'StudentSkills',
        component: StudentSkills
      },


      // Add External Activity

      {
        path: 'external-activity',
        name: 'StudentExternalActivity',
        component: StudentExternalActivity
      },


      // Transcript

      {
        path: 'transcript',
        name: 'StudentTranscript',
        component: StudentTranscript
      }

    ]
  },


  // =========================
  // URL ไม่ถูกต้อง
  // กลับหน้า Login
  // =========================

  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }

]


const router = createRouter({
  history: createWebHistory(),
  routes
})


export default router