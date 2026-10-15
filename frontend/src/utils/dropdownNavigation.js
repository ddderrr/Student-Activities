// ตรรกะของ SelectDropdown.vue (แยกไว้ทดสอบได้โดยไม่ต้องมี DOM)

const PAGE_STEP = 10

// ลูกศร/Home/End/PageUp/PageDown: เลื่อนรายการที่ไฮไลต์ หยุดที่ต้น/ท้าย ไม่วน (เหมือน select ปกติ)
export function moveActiveIndex(current, key, count) {
  if (count <= 0) return -1
  const last = count - 1
  const from = current < 0 ? -1 : current
  const next = {
    ArrowDown: from + 1,
    ArrowUp: from - 1,
    Home: 0,
    End: last,
    PageDown: from + PAGE_STEP,
    PageUp: from - PAGE_STEP
  }[key]
  if (next === undefined) return current
  return Math.min(Math.max(next, 0), last)
}

// เปิดลงด้านล่างเสมอ ยกเว้นด้านล่างไม่พอและด้านบนมีที่มากกว่า
export function shouldOpenUpward(rect, menuHeight, viewportHeight, gap = 6) {
  const spaceBelow = viewportHeight - rect.bottom - gap
  const spaceAbove = rect.top - gap
  return spaceBelow < menuHeight && spaceAbove > spaceBelow
}

// พิมพ์ตัวอักษรเพื่อกระโดดไปรายการ: ตัวเดียว = วนไปรายการถัดไปที่ขึ้นต้นด้วยตัวนั้น
// หลายตัว (พิมพ์ต่อกันเร็ว ๆ) = เริ่มหาจากรายการปัจจุบัน คืน -1 ถ้าไม่พบ
export function typeaheadIndex(labels, query, current) {
  const needle = query.toLocaleLowerCase()
  if (!needle || !labels.length) return -1
  const start = [...needle].length === 1 ? current + 1 : Math.max(current, 0)
  for (let offset = 0; offset < labels.length; offset++) {
    const index = (start + offset) % labels.length
    if (String(labels[index]).toLocaleLowerCase().startsWith(needle)) return index
  }
  return -1
}
