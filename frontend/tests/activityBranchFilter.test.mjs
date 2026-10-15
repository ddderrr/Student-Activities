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
})

test('faculty option asks for faculty activities only', () => {
  assert.equal(activityListParams(FACULTY_ACTIVITIES_VALUE).toString(), 'faculty_only=true')
})

test('a branch shows only that branch, without faculty activities', () => {
  const params = activityListParams('เคมี')
  assert.equal(params.get('major'), 'เคมี')
  assert.equal(params.get('branch_only'), 'true')
  assert.equal(params.has('faculty_only'), false)
})

test('branch admin "my branch only" asks for branch_only without major', () => {
  assert.equal(activityListParams(MY_BRANCH_ONLY_VALUE).toString(), 'branch_only=true')
})
