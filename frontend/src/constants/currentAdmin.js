import { API_BASE } from '../config/api'

// session แอดมินหลัง login ที่หน้า /login (ดู constants/auth.js) เก็บ token ไว้ใน localStorage
// ทุกคำขอฝั่ง admin ส่ง token เป็น Authorization: Bearer ผ่าน adminFetch / adminHeaders

const STORAGE_KEY = 'adminSession'

export function getAdminSession() {
  try {
    const session = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
    return session?.email && session?.token ? session : null
  } catch {
    return null
  }
}

// token ว่าง = ใช้ token เดิม (เช่นอัปเดตข้อมูลจาก /api/admin/me)
export function setAdminSession(admin, token = getAdminSession()?.token) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      id: admin.id,
      email: admin.email,
      name: admin.name,
      major: admin.major,
      is_central: admin.is_central,
      token
    }))
  } catch {
    // เก็บไม่ได้ (เช่น private mode): รีเฟรชแล้วต้อง login ใหม่
  }
}

export function clearAdminSession() {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
}

export function adminHeaders(extra = {}) {
  const session = getAdminSession()

  return {
    ...(session ? { Authorization: `Bearer ${session.token}` } : {}),
    ...extra
  }
}

// fetch สำหรับ API ฝั่ง admin: แนบ token ให้ และถ้า backend ตอบ 401
// (token หมดอายุ / บัญชีถูกลบ) ให้กลับไปหน้า login
export async function adminFetch(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: adminHeaders(options.headers)
  })

  if (response.status === 401) {
    clearAdminSession()

    if (window.location.pathname !== '/login') {
      const redirect = encodeURIComponent(window.location.pathname + window.location.search)
      window.location.assign(`/login?reason=expired&redirect=${redirect}`)
    }
  }

  return response
}

// ตรวจกับ backend ว่า token ยังใช้ได้ (ยังไม่หมดอายุ และบัญชียังไม่ถูกลบ)
// คืน null ถ้าใช้ไม่ได้ / throw ถ้าต่อ backend ไม่ได้
export async function verifyAdminSession() {
  if (!getAdminSession()) return null

  const response = await fetch(`${API_BASE}/api/admin/me`, {
    headers: adminHeaders()
  })

  if (response.status === 401) {
    clearAdminSession()
    return null
  }

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const admin = await response.json()
  setAdminSession(admin)
  return admin
}

// ไฟล์หลักฐานต้องแนบ header จึงใช้ <img src> / <a href> ตรง ๆ ไม่ได้ ต้องโหลดเป็น blob URL
export async function fetchAdminFileUrl(url) {
  const response = await adminFetch(url)

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  return URL.createObjectURL(await response.blob())
}
