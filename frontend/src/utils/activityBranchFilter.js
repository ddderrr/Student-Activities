import { ALL_BRANCHES_VALUE, FACULTY_ACTIVITIES_VALUE } from '../constants/branches.js'

// query ของ GET /api/activities ตามตัวเลือกใน BranchFilterSelect หน้า Activities
export function activityListParams(selected) {
  const params = new URLSearchParams()
  if (selected === FACULTY_ACTIVITIES_VALUE) {
    params.set('faculty_only', 'true')
  } else if (selected !== ALL_BRANCHES_VALUE) {
    params.set('major', selected)
  }
  return params
}
