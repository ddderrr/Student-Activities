import { test } from 'node:test'
import assert from 'node:assert/strict'
import { activityListParams } from '../src/utils/activityBranchFilter.js'
import {
  ALL_BRANCHES_VALUE,
  FACULTY_ACTIVITIES_VALUE,
  MY_BRANCH_ONLY_VALUE
} from '../src/constants/branches.js'

test('all branches sends no filter', () => {
  assert.equal(activityListParams(ALL_BRANCHES_VALUE).toString(), '')
  assert.equal(activityListParams(ALL_BRANCHES_VALUE, { includeFaculty: false }).toString(), '')
})

test('faculty option asks for faculty activities only', () => {
  assert.equal(activityListParams(FACULTY_ACTIVITIES_VALUE).toString(), 'faculty_only=true')
})

test('a branch still sends major as before, including faculty activities by default', () => {
  assert.equal(activityListParams('เคมี').get('major'), 'เคมี')
  assert.equal(activityListParams('เคมี').has('faculty_only'), false)
  assert.equal(activityListParams('เคมี').has('branch_only'), false)
})

test('a branch without faculty activities adds branch_only', () => {
  const params = activityListParams('เคมี', { includeFaculty: false })
  assert.equal(params.get('major'), 'เคมี')
  assert.equal(params.get('branch_only'), 'true')
})

test('branch admin "my branch only" asks for branch_only without major', () => {
  assert.equal(activityListParams(MY_BRANCH_ONLY_VALUE).toString(), 'branch_only=true')
})
