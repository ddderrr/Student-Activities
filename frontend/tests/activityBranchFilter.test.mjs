import { test } from 'node:test'
import assert from 'node:assert/strict'
import { activityListParams } from '../src/utils/activityBranchFilter.js'
import { ALL_BRANCHES_VALUE, FACULTY_ACTIVITIES_VALUE } from '../src/constants/branches.js'

test('all branches sends no filter', () => {
  assert.equal(activityListParams(ALL_BRANCHES_VALUE).toString(), '')
})

test('faculty option asks for faculty activities only', () => {
  assert.equal(activityListParams(FACULTY_ACTIVITIES_VALUE).toString(), 'faculty_only=true')
})

test('a branch still sends major as before', () => {
  assert.equal(activityListParams('เคมี').get('major'), 'เคมี')
  assert.equal(activityListParams('เคมี').has('faculty_only'), false)
})
