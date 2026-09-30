// ช่วงเวลาของหน้า Dashboard: ใช้ร่วมกันทั้ง KPI (/api/admin/dashboard) และกราฟ
// Skill Distribution (/api/admin/dashboard/skill-distribution) ให้เปลี่ยนตามกันเสมอ
//
// - ยังไม่คลิกกราฟ Activity Growth: ไม่ส่ง months -> backend ใช้ทั้งภาคเรียนที่เลือก
// - คลิกเดือน/ไตรมาสแล้ว: ส่ง months ของเดือน/ไตรมาสนั้น

export const MONTH_LABELS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

// เดือน/ไตรมาสที่ผู้ใช้คลิกใน Activity Growth chart แปลงเป็นเลขเดือน (1-12)
export function selectedMonthNumbers({ hasSelectedChartItem, period, selectedItem }) {
  if (!hasSelectedChartItem) return []

  if (period === 'MONTHLY') {
    const index = MONTH_LABELS.indexOf(selectedItem)
    return index === -1 ? [] : [index + 1]
  }

  const quarterNumber = Number(String(selectedItem).replace('Q', ''))
  if (!Number.isInteger(quarterNumber) || quarterNumber < 1 || quarterNumber > 4) return []

  const firstMonth = (quarterNumber - 1) * 3 + 1
  return [firstMonth, firstMonth + 1, firstMonth + 2]
}

export function dashboardPeriodParams({ year, semester, monthNumbers, branch, allBranchesValue }) {
  const params = new URLSearchParams({
    year: String(year),
    semester
  })

  if (monthNumbers.length) {
    params.set('months', monthNumbers.join(','))
  }

  if (branch !== allBranchesValue) {
    params.set('major', branch)
  }

  return params
}
