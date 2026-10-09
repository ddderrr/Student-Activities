// วันที่ใน API เป็นเวลาไทยแบบไม่มี timezone ("2026-10-05T09:00:00" หรือ "2026-10-05")
// แปลงเป็น Date เที่ยงคืนของวันนั้น (เวลาเครื่อง) ใช้วางกิจกรรมลงปฏิทินรายวัน
export function dayOf(value) {
  const [year, month, day] = String(value).slice(0, 10).split('-').map(Number)
  return new Date(year, month - 1, day)
}

// ผ่านมาแล้ว: มีเวลา = เลยเวลาสิ้นสุดจริง, มีแค่วันที่ = เลยวันนั้นไปแล้วทั้งวัน
export function isPast(endValue, now = new Date()) {
  const text = String(endValue)
  if (text.length <= 10 || text.slice(11, 19) === '00:00:00') {
    const end = dayOf(text)
    return new Date(end.getFullYear(), end.getMonth(), end.getDate() + 1) <= now
  }
  return new Date(text.slice(0, 19)) < now
}
