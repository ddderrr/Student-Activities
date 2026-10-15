// ตารางตรวจสอบก่อนนำเข้าผู้ร่วมกิจกรรม (AdminStudentActivities.vue)

// existing = อยู่ในกิจกรรมนี้แล้ว (ข้าม ไม่นับเป็นปัญหา), issue = ข้อมูลมีปัญหา, ready = พร้อมนำเข้า
export function importRowStatus(student, errors, existingIds) {
  if (existingIds.has(String(student.student_id ?? '').trim())) return 'existing'
  return Object.keys(errors || {}).length ? 'issue' : 'ready'
}

// ข้อความแจ้งผลด้านบนหน้าหลังนำเข้าเสร็จ เช่น "นำเข้าสำเร็จ 3 คน ข้ามข้อมูลซ้ำ 1 คน"
export function importResultMessage(labels, result, skippedIssueCount) {
  let message = labels.importSuccessMessage.replace('{count}', result.imported_count)
  if (result.duplicate_count) {
    message += labels.importSuccessDuplicateSuffix.replace('{count}', result.duplicate_count)
  }
  if (skippedIssueCount) {
    message += labels.importSuccessIssueSuffix.replace('{count}', skippedIssueCount)
  }
  return message
}
