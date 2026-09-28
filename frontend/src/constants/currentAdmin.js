import { API_BASE } from './currentStudent'

// ยังไม่มีระบบ login แอดมินจริง: โหมด bypass ให้เลือกอีเมลแอดมินทดสอบที่หน้า /admin/login
// (backend ต้องตั้ง ADMIN_BYPASS_ENABLED=true ใน .env รายชื่ออยู่ที่ backend/admin_accounts.py)
// เมื่อมีระบบ login จริง ให้แก้ที่ไฟล์นี้ไฟล์เดียว (เก็บ/ส่ง token แทนอีเมล) หน้าอื่นเรียกผ่าน adminFetch อยู่แล้ว

const STORAGE_KEY = 'adminSession'

export function getAdminSession() {
  try {
    const session = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
    return session?.email ? session : null
  } catch {
    return null
  }
}

export function setAdminSession(admin) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      email: admin.email,
      name: admin.name,
      major: admin.major,
      is_central: admin.is_central
    }))
  } catch {
    // เก็บไม่ได้ (เช่น private mode) ก็ยังใช้หน้านี้ต่อได้ แต่รีเฟรชแล้วต้องเลือกใหม่
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
    ...(session ? { 'X-Admin-Email': session.email } : {}),
    ...extra
  }
}

// fetch สำหรับ API ฝั่ง admin: แนบตัวตนแอดมินให้ และถ้า backend ตอบ 401
// (ไม่ได้เลือกอีเมล / bypass ปิด) ให้กลับไปหน้า login ซึ่งจะบอกสาเหตุเอง
export async function adminFetch(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: adminHeaders(options.headers)
  })

  if (response.status === 401) {
    clearAdminSession()

    if (window.location.pathname !== '/admin/login') {
      window.location.assign('/admin/login?reason=unauthorized')
    }
  }

  return response
}

export async function fetchAdminBypassStatus() {
  const response = await fetch(`${API_BASE}/api/admin/auth/bypass`)

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  return response.json()
}

// ตรวจกับ backend ว่าอีเมลที่เลือกไว้ยังใช้ได้ (bypass ยังเปิด และยังอยู่ในรายชื่อ)
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
