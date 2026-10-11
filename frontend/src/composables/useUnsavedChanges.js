import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

/*
  เตือนก่อนออกจากหน้าเมื่อยังมีงานค้าง (เช่น กรอกฟอร์มสร้างกิจกรรมไปแล้วแต่ยังไม่บันทึก)
  isDirty: () => boolean  ตอนนี้มีข้อมูลที่ยังไม่บันทึกไหม

  - เปลี่ยนหน้าในเว็บ: รอให้ผู้ใช้เลือกใน UnsavedChangesDialog (open / stay / leave)
  - รีเฟรช / ปิดแท็บ: browser แสดงกล่องเตือนของตัวเอง (ข้อความกำหนดเองไม่ได้)
  - ไปหน้า login (กดออกจากระบบ / token หมดอายุ) ไม่ถาม: session ถูกล้างไปแล้ว อยู่ต่อก็ใช้งานไม่ได้
  - allowLeave(): เรียกก่อน router.push หลังบันทึกสำเร็จ จะได้ไม่ถามซ้ำ
*/
export function useUnsavedChanges(isDirty) {
  const pendingResolve = ref(null)
  let bypass = false

  onBeforeRouteLeave((to) => {
    if (bypass || to.name === 'Login' || !isDirty()) return true
    return new Promise((resolve) => {
      pendingResolve.value = resolve
    })
  })

  function finish(leave) {
    const resolve = pendingResolve.value
    pendingResolve.value = null
    resolve?.(leave)
  }

  function onBeforeUnload(event) {
    if (bypass || !isDirty()) return
    event.preventDefault()
    event.returnValue = ''
  }

  onMounted(() => window.addEventListener('beforeunload', onBeforeUnload))
  onBeforeUnmount(() => {
    window.removeEventListener('beforeunload', onBeforeUnload)
    finish(false)
  })

  return {
    open: computed(() => pendingResolve.value !== null),
    stay: () => finish(false),
    leave: () => finish(true),
    allowLeave: () => {
      bypass = true
    }
  }
}
