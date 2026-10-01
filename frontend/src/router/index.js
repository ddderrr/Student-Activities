import { createRouter, createWebHistory } from 'vue-router'

import { currentHome } from '../constants/auth'
import { verifyAdminSession } from '../constants/currentAdmin'
import { verifyStudentSession } from '../constants/currentStudent'

// =========================
// Login (หน้าเดียวสำหรับแอดมินและนักศึกษา)
// =========================

import Login from '../views/Login/Login.vue'


// =========================
// Admin
// =========================

import AdminStudentActivities from '../views/Admin/AdminStudentActivities.vue'
import AdminParticipantDetails from '../views/Admin/AdminParticipantDetails.vue'
import AdminCreateActivity from '../views/Admin/AdminCreateActivity.vue'
import AdminDashBoard from '../views/Admin/AdminDashBoard.vue'
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
    path: '/login',
    name: 'Login',
    component: Login
  },

  // หน้าแรก: login แล้วไปหน้าหลักของบทบาท ยังไม่ login ไปหน้า /login
  {
    path: '/',
    redirect: () => currentHome() || '/login'
  },

  // URL login เดิม (bookmark เก่า)
  { path: '/admin/login', redirect: '/login' },
  { path: '/student/login', redirect: '/login' },


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
    name: 'AdminDashBoard',
    component: AdminDashBoard
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
  // URL ไม่ถูกต้อง: กลับหน้าแรก (หน้าหลักของบทบาท หรือ /login)
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


// =========================
// Route guard
// /admin/* ต้อง login เป็นแอดมิน, /student/* ต้อง login เป็นนักศึกษา
// token หมดอายุ / บัญชีถูกลบ -> กลับหน้า /login พร้อมพากลับหน้าเดิมหลัง login
// =========================

const ROLE_AREAS = [
  { prefix: '/admin', verify: verifyAdminSession },
  { prefix: '/student', verify: verifyStudentSession }
]

router.beforeEach(async (to) => {
  const area = ROLE_AREAS.find(({ prefix }) => to.path === prefix || to.path.startsWith(`${prefix}/`))

  if (!area) return true

  try {
    if (!(await area.verify())) {
      return { name: 'Login', query: { redirect: to.fullPath } }
    }
  } catch {
    // ต่อ backend ไม่ได้: ให้เข้าหน้าได้ แต่ละหน้าแสดง error การเชื่อมต่อเอง
  }

  return true
})


export default router