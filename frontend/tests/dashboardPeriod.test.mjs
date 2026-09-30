import { test } from 'node:test'
import assert from 'node:assert/strict'

import { dashboardPeriodParams, selectedMonthNumbers } from '../src/utils/dashboardPeriod.js'

const ALL = '__all__'

test('no chart item selected -> no months, so the whole semester is used', () => {
  for (const period of ['MONTHLY', 'QUARTERLY']) {
    const months = selectedMonthNumbers({ hasSelectedChartItem: false, period, selectedItem: period === 'MONTHLY' ? 'SEP' : 'Q3' })
    assert.deepEqual(months, [])

    const params = dashboardPeriodParams({ year: 2026, semester: 'SEMESTER_2', monthNumbers: months, branch: ALL, allBranchesValue: ALL })
    assert.equal(params.has('months'), false)
    assert.equal(params.get('semester'), 'SEMESTER_2')
    assert.equal(params.get('year'), '2026')
  }
})

test('clicked month -> that month only', () => {
  const months = selectedMonthNumbers({ hasSelectedChartItem: true, period: 'MONTHLY', selectedItem: 'SEP' })
  assert.deepEqual(months, [9])
  assert.equal(
    dashboardPeriodParams({ year: 2026, semester: 'ALL', monthNumbers: months, branch: ALL, allBranchesValue: ALL }).get('months'),
    '9'
  )
})

test('clicked quarter -> its three months', () => {
  assert.deepEqual(selectedMonthNumbers({ hasSelectedChartItem: true, period: 'QUARTERLY', selectedItem: 'Q3' }), [7, 8, 9])
  assert.deepEqual(selectedMonthNumbers({ hasSelectedChartItem: true, period: 'QUARTERLY', selectedItem: 'Q9' }), [])
})

test('branch filter is sent only when a branch is chosen', () => {
  const base = { year: 2026, semester: 'ALL', monthNumbers: [], allBranchesValue: ALL }
  assert.equal(dashboardPeriodParams({ ...base, branch: ALL }).has('major'), false)
  assert.equal(dashboardPeriodParams({ ...base, branch: 'เคมี' }).get('major'), 'เคมี')
})
