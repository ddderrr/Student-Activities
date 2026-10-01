export const API_BASE = 'http://127.0.0.1:8000'

// ยังไม่มีระบบ login นักศึกษา: ใช้ student ID จำลอง (สร้างไว้แล้วผ่าน Add Student ในกิจกรรม)
// เมื่อมีระบบ login จริง ให้เปลี่ยนมาอ่านจาก session แทน
export const MOCK_STUDENT_ID = '670510659'

// ศูนย์ช่วยเหลือของนักศึกษา: ติดต่อทางอีเมล
export const HELP_CENTER_EMAIL = 'natthanon_t@cmu.ac.th'

// โหมด bypass ให้เลือกอีเมลนักศึกษาทดสอบที่หน้า /student/login (เหมือนแอดมิน)
// backend รายชื่ออยู่ที่ backend/student_bypass.py เก็บ session ไว้ใน localStorage
// เมื่อมีระบบ login จริง ให้แก้ที่ไฟล์นี้ไฟล์เดียว (เก็บ/ส่ง token แทนอีเมล)
const STORAGE_KEY = 'studentSession'

export function getStudentSession() {
  try {
    const session = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
    return session?.email ? session : null
  } catch {
    return null
  }
}

export function setStudentSession(student) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      student_id: student.student_id,
      email: student.email,
      name: student.name,
      major: student.major,
      faculty: student.faculty
    }))
  } catch {
    // เก็บไม่ได้ (เช่น private mode) ก็ยังใช้หน้านี้ต่อได้ แต่รีเฟรชแล้วต้องเลือกใหม่
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

  if (session) {
    // นักศึกษาจำลองสาขาเดียวกันใช้อีเมลร่วมกัน: ส่ง student_id ไปด้วยเพื่อระบุตัวคน
    return {
      'X-Student-Email': session.email,
      ...(session.student_id ? { 'X-Student-Id': session.student_id } : {}),
      ...extra
    }
  }

  // ยังไม่ได้เลือก mock student จากหน้า login: fallback ไป student ID จำลองเดิม
  return {
    'X-Student-Id': MOCK_STUDENT_ID,
    ...extra
  }
}

// ตรวจกับ backend ว่าอีเมลที่เลือกไว้ยังใช้ได้ คืน null ถ้าใช้ไม่ได้ / throw ถ้าต่อ backend ไม่ได้
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

// หน้า login ฝั่งนักศึกษา (mock: อีเมล + รหัสผ่าน ดู backend/student_bypass.py)
// โยน error ที่มี .status ไว้แยก 404 (ไม่พบอีเมล) / 401 (รหัสผ่านผิด)
// ออกจากปัญหาต่อ backend ไม่ได้
export async function loginStudentWithPassword(email, password) {
  const response = await fetch(`${API_BASE}/api/student/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })

  if (!response.ok) {
    const error = new Error(`HTTP ${response.status}`)
    error.status = response.status
    throw error
  }

  return response.json()
}

// ไฟล์หลักฐานต้องแนบ X-Student-Id จึงเปิดด้วย <a href> ตรง ๆ ไม่ได้: โหลดเป็น blob แล้วเปิดในแท็บใหม่
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
