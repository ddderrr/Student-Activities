// ชื่อสาขาที่แสดงตามภาษา: ค่าที่ส่ง backend / เก็บในฐานข้อมูลยังเป็นชื่อภาษาไทยเสมอ แปลงเฉพาะตอนแสดง
// ชื่อที่ไม่อยู่ในรายการ (ข้อมูลเก่า เช่น "ฟิสิกส์และวัสดุศาสตร์") แสดงตามเดิม
// ชื่ออังกฤษต้องตรงกับ MAJOR_NAMES_EN ใน backend/transcript_i18n.py (Transcript PDF)

export const BRANCH_NAMES_EN = {
  'เคมี': 'Chemistry',
  'เคมีอุตสาหกรรม': 'Industrial Chemistry',
  'จุลชีววิทยา': 'Microbiology',
  'ชีวเคมีและชีวเคมีนวัตกรรม': 'Biochemistry and Biochemical Innovation',
  'ชีววิทยา': 'Biology',
  'ธรณีวิทยา': 'Geology',
  'ฟิสิกส์': 'Physics',
  'วัสดุศาสตร์': 'Materials Science',
  'สัตววิทยา': 'Zoology',
  'คณิตศาสตร์': 'Mathematics',
  'วิทยาการข้อมูล': 'Data Science',
  'วิทยาการคอมพิวเตอร์': 'Computer Science',
  'วิทยาศาสตร์สิ่งแวดล้อม (หลักสูตรนานาชาติ)': 'Environmental Science (International Program)',
  'สถิติ': 'Statistics',
  'อัญมณีวิทยา': 'Gemology'
}

// language: ค่าจาก useLanguage().currentLanguage ('TH' | 'EN')
export function branchDisplayName(name, language) {
  if (name === null || name === undefined) return ''
  if (language !== 'EN') return name
  return BRANCH_NAMES_EN[String(name).trim()] ?? name
}
