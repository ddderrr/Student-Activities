import { test } from 'node:test'
import assert from 'node:assert/strict'
import { branchDisplayName } from '../src/utils/branchNames.js'
import { BRANCHES } from '../src/constants/branches.js'

test('English shows the English branch name', () => {
  assert.equal(branchDisplayName('เคมี', 'EN'), 'Chemistry')
  assert.equal(branchDisplayName('ชีวเคมีและชีวเคมีนวัตกรรม', 'EN'), 'Biochemistry and Biochemical Innovation')
  assert.equal(
    branchDisplayName('วิทยาศาสตร์สิ่งแวดล้อม (หลักสูตรนานาชาติ)', 'EN'),
    'Environmental Science (International Program)'
  )
  assert.equal(branchDisplayName('อัญมณีวิทยา', 'EN'), 'Gemology')
})

test('every branch in the list has an English name', () => {
  for (const branch of BRANCHES) {
    assert.notEqual(branchDisplayName(branch, 'EN'), branch, branch)
  }
})

test('Thai keeps the stored name', () => {
  assert.equal(branchDisplayName('เคมี', 'TH'), 'เคมี')
})

test('unknown or empty names are shown as they are', () => {
  assert.equal(branchDisplayName('ฟิสิกส์และวัสดุศาสตร์', 'EN'), 'ฟิสิกส์และวัสดุศาสตร์')
  assert.equal(branchDisplayName('', 'EN'), '')
  assert.equal(branchDisplayName(null, 'EN'), '')
  assert.equal(branchDisplayName(undefined, 'TH'), '')
})

test('surrounding spaces still match, but unknown names keep their original text', () => {
  assert.equal(branchDisplayName(' สถิติ ', 'EN'), 'Statistics')
  assert.equal(branchDisplayName(' ไม่มีในรายการ ', 'EN'), ' ไม่มีในรายการ ')
})
