import { clearAdminSession, getAdminSession, setAdminSession } from './currentAdmin'
import { API_BASE, clearStudentSession, getStudentSession, setStudentSession } from './currentStudent'

// หน้า /login เดียวสำหรับทุกคน: backend หาแอดมินก่อน แล้วจึงนักศึกษา (POST /api/auth/login)
export const ADMIN_HOME = '/admin/dashboard'
export const STUDENT_HOME = '/student/activities'

// โยน error ที่มี .status: 404 = ไม่พบบัญชี, 401 = รหัสผ่านผิด, ไม่มี status = ต่อ backend ไม่ได้
export async function loginWithPassword(email, password) {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })

  if (!response.ok) {
    const error = new Error(`HTTP ${response.status}`)
    error.status = response.status
    throw error
  }

  const data = await response.json()

  // เข้าได้ทีละบทบาท: ล้าง session อีกฝั่งทิ้งเสมอ
  if (data.role === 'admin') {
    clearStudentSession()
    setAdminSession(data.admin, data.token)
    return { role: 'admin', home: ADMIN_HOME }
  }

  clearAdminSession()
  setStudentSession(data.student, data.token)
  return { role: 'student', home: STUDENT_HOME }
}

export function currentHome() {
  if (getAdminSession()) return ADMIN_HOME
  if (getStudentSession()) return STUDENT_HOME
  return null
}

export function logout() {
  clearAdminSession()
  clearStudentSession()
}
