import {
  ALL_BRANCHES_VALUE,
  FACULTY_ACTIVITIES_VALUE,
  MY_BRANCH_ONLY_VALUE
} from '../constants/branches.js'

// query ของ GET /api/activities ตามตัวเลือกใน BranchFilterSelect หน้า Activities
// includeFaculty: checkbox "รวมกิจกรรมส่วนกลาง" ของแอดมินกลาง มีผลเฉพาะตอนเลือกสาขา
export function activityListParams(selected, { includeFaculty = true } = {}) {
  const params = new URLSearchParams()
  if (selected === FACULTY_ACTIVITIES_VALUE) {
    params.set('faculty_only', 'true')
  } else if (selected === MY_BRANCH_ONLY_VALUE) {
    params.set('branch_only', 'true')
  } else if (selected !== ALL_BRANCHES_VALUE) {
    params.set('major', selected)
    if (!includeFaculty) params.set('branch_only', 'true')
  }
  return params
}
