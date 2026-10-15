import { test } from 'node:test'
import assert from 'node:assert/strict'
import { importResultMessage, importRowStatus } from '../src/utils/participantImport.js'
import th from '../src/locales/th.js'
import en from '../src/locales/en.js'

test('a student already in the activity is "existing", even if other fields have issues', () => {
  const existing = new Set(['670510001'])
  assert.equal(importRowStatus({ student_id: ' 670510001 ' }, {}, existing), 'existing')
  assert.equal(importRowStatus({ student_id: '670510001' }, { email: 'bad' }, existing), 'existing')
})

test('other rows are "issue" when they have errors, otherwise "ready"', () => {
  const existing = new Set(['670510001'])
  assert.equal(importRowStatus({ student_id: '670510002' }, { email: 'bad' }, existing), 'issue')
  assert.equal(importRowStatus({ student_id: '670510002' }, {}, existing), 'ready')
})

test('result message reads "imported X, skipped Y duplicates"', () => {
  const labels = th.adminStudentActivities
  assert.equal(
    importResultMessage(labels, { imported_count: 3, duplicate_count: 1 }, 0),
    'นำเข้าสำเร็จ 3 คน ข้ามข้อมูลซ้ำ 1 คน'
  )
  assert.equal(importResultMessage(labels, { imported_count: 3, duplicate_count: 0 }, 0), 'นำเข้าสำเร็จ 3 คน')
  assert.equal(
    importResultMessage(labels, { imported_count: 2, duplicate_count: 1 }, 2),
    'นำเข้าสำเร็จ 2 คน ข้ามข้อมูลซ้ำ 1 คน ข้ามข้อมูลที่มีปัญหา 2 รายการ'
  )
  assert.equal(
    importResultMessage(en.adminStudentActivities, { imported_count: 3, duplicate_count: 1 }, 0),
    'Imported 3 people, skipped 1 already added'
  )
})

test('both languages label the "already in activity" status', () => {
  assert.equal(th.adminStudentActivities.existingStatusLabel, 'มีอยู่แล้ว')
  assert.equal(en.adminStudentActivities.existingStatusLabel, 'Already added')
})
