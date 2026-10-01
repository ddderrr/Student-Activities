export const API_BASE = 'http://127.0.0.1:8000'

// ศูนย์ช่วยเหลือของนักศึกษา: ติดต่อทางอีเมล
export const HELP_CENTER_EMAIL = 'natthanon_t@cmu.ac.th'

// session นักศึกษาหลัง login ที่หน้า /login (ดู constants/auth.js) เก็บ token ไว้ใน localStorage
// ทุกคำขอฝั่งนักศึกษาส่ง token เป็น Authorization: Bearer ผ่าน studentHeaders
const STORAGE_KEY = 'studentSession'

export function getStudentSession() {
  try {
    const session = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
    return session?.student_id && session?.token ? session : null
  } catch {
    return null
  }
}

// token ว่าง = ใช้ token เดิม (เช่นอัปเดตข้อมูลจาก /api/student/me)
export function setStudentSession(student, token = getStudentSession()?.token) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      student_id: student.student_id,
      email: student.email,
      name: student.name,
      major: student.major,
      faculty: student.faculty,
      token
    }))
  } catch {
    // เก็บไม่ได้ (เช่น private mode): รีเฟรชแล้วต้อง login ใหม่
  }
}

export function clearStudentSession() {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
}

export function studentHeaders(extra = {}) {
  const session = getStudentSession()

  return {
    ...(session ? { Authorization: `Bearer ${session.token}` } : {}),
    ...extra
  }
}

// ตรวจกับ backend ว่า token ยังใช้ได้ คืน null ถ้าใช้ไม่ได้ / throw ถ้าต่อ backend ไม่ได้
export async function verifyStudentSession() {
  if (!getStudentSession()) return null

  const response = await fetch(`${API_BASE}/api/student/me`, {
    headers: studentHeaders()
  })

  if (response.status === 401) {
    clearStudentSession()
    return null
  }

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const student = await response.json()
  setStudentSession(student)
  return student
}

// ไฟล์หลักฐานต้องแนบ token จึงเปิดด้วย <a href> ตรง ๆ ไม่ได้: โหลดเป็น blob แล้วเปิดในแท็บใหม่
// เปิดแท็บก่อน await เพื่อไม่ให้ browser บล็อก popup
export async function openStudentFile(url) {
  const tab = window.open('', '_blank')

  try {
    const response = await fetch(url, { headers: studentHeaders() })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const blobUrl = URL.createObjectURL(await response.blob())

    if (tab) {
      tab.location.href = blobUrl
    } else {
      window.location.href = blobUrl
    }
  } catch (error) {
    tab?.close()
    throw error
  }
}

export const OTHER_CATEGORY_VALUE = 'อื่น ๆ'

export const EXTERNAL_ACTIVITY_CATEGORIES = [
  'จิตอาสา / บริการสังคม',
  'อบรม / Workshop',
  'สัมมนา / ประชุมวิชาการ',
  'การแข่งขัน',
  'ค่ายกิจกรรม',
  'ศิลปะและวัฒนธรรม',
  'กีฬาและสุขภาพ',
  OTHER_CATEGORY_VALUE
]

export const EXTERNAL_ROLE_OPTIONS = [
  { value: 'participant', label: 'Participant (ผู้เข้าร่วม)' },
  { value: 'organizer', label: 'Organizer (ผู้จัด / ทีมงาน)' }
]

export const EVIDENCE_MAX_BYTES = 5 * 1024 * 1024
export const EVIDENCE_MAX_FILES = 10
export const EVIDENCE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf']

export function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}
