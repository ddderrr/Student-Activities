// ชุดสีของปฏิทินกิจกรรม (สีตามประเภทกิจกรรม) ใช้ร่วมกันทุกหน้า (Dashboard แอดมิน / กิจกรรมของฉันของนักศึกษา)
// สีเดียวกันทุกเดือนเพราะขึ้นกับข้อมูลของกิจกรรมเท่านั้น ไม่ขึ้นกับลำดับ

// สีตามประเภทกิจกรรม (ตรงกับตัวเลือกในหน้าสร้างกิจกรรม)
// match ด้วยคำในชื่อประเภท รองรับข้อมูลเก่าที่เป็นภาษาอังกฤษ ไม่ตรงอะไรเลย (พิมพ์เองผ่าน "อื่นๆ") = other
export const ACTIVITY_TYPE_COLORS = [
  { key: 'academic', color: '#2563EB', words: ['วิชาการ', 'academic'] },
  { key: 'seminar', color: '#7C3AED', words: ['สัมมนา', 'seminar'] },
  { key: 'training', color: '#0891B2', words: ['อบรม', 'workshop', 'training'] },
  { key: 'volunteer', color: '#059669', words: ['จิตอาสา', 'อาสา', 'volunteer'] },
  { key: 'skill', color: '#D97706', words: ['พัฒนาทักษะ', 'skill'] },
  { key: 'recreation', color: '#DB2777', words: ['นันทนาการ', 'recreation', 'sport', 'กีฬา'] }
]
export const OTHER_TYPE_COLOR = { key: 'other', color: '#DC2626' }

export function activityTypeColor(type) {
  const text = String(type || '').trim().toLowerCase()
  return ACTIVITY_TYPE_COLORS.find((entry) => entry.words.some((word) => text.includes(word))) || OTHER_TYPE_COLOR
}
