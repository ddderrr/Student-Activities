import {
  ALL_BRANCHES_VALUE,
  FACULTY_ACTIVITIES_VALUE,
  MY_BRANCH_ONLY_VALUE
} from '../constants/branches.js'

// query ของ GET /api/activities ตามตัวเลือกใน BranchFilterSelect หน้า Activities
// แอดมินกลางเลือกสาขา = เฉพาะกิจกรรมของสาขานั้น ไม่รวมส่วนกลาง (ดูส่วนกลางได้จาก FACULTY_ACTIVITIES_VALUE)
export function activityListParams(selected) {
  const params = new URLSearchParams()
  if (selected === FACULTY_ACTIVITIES_VALUE) {
    params.set('faculty_only', 'true')
  } else if (selected === MY_BRANCH_ONLY_VALUE) {
    params.set('branch_only', 'true')
  } else if (selected !== ALL_BRANCHES_VALUE) {
    params.set('major', selected)
    params.set('branch_only', 'true')
  }
  return params
}
