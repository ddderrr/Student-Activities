// ตารางนักศึกษาในกิจกรรม: ผู้จัดก่อน แล้วผู้เข้าร่วม แต่ละกลุ่มเรียงตามรหัสนักศึกษา
const ROLE_ORDER = { organizer: 0, participant: 1 }

export function sortParticipantsByRole(students) {
  return [...students].sort((a, b) => {
    const roleDiff = (ROLE_ORDER[a.role] ?? 2) - (ROLE_ORDER[b.role] ?? 2)
    if (roleDiff) return roleDiff
    const idA = String(a.student_id)
    const idB = String(b.student_id)
    return idA < idB ? -1 : idA > idB ? 1 : 0
  })
}
