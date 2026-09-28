export const API_BASE = 'http://127.0.0.1:8000'

// ยังไม่มีระบบ login นักศึกษา: ใช้ student ID จำลอง (สร้างไว้แล้วผ่าน Add Student ในกิจกรรม)
// เมื่อมีระบบ login จริง ให้เปลี่ยนมาอ่านจาก session แทน
export const MOCK_STUDENT_ID = '670510659'

// ศูนย์ช่วยเหลือของนักศึกษา: ติดต่อทางอีเมล
export const HELP_CENTER_EMAIL = 'natthanon_t@cmu.ac.th'

export function studentHeaders(extra = {}) {
  return {
    'X-Student-Id': MOCK_STUDENT_ID,
    ...extra
  }
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
