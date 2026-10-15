import { test } from 'node:test'
import assert from 'node:assert/strict'
import { sortParticipantsByRole } from '../src/utils/participantOrder.js'

test('organizers come first, each group sorted by student id', () => {
  const students = [
    { student_id: '670510003', role: 'participant' },
    { student_id: '670510004', role: 'organizer' },
    { student_id: '670510001', role: 'participant' },
    { student_id: '670510002', role: 'organizer' }
  ]

  assert.deepEqual(
    sortParticipantsByRole(students).map((s) => s.student_id),
    ['670510002', '670510004', '670510001', '670510003']
  )
  assert.equal(students[0].student_id, '670510003', 'does not mutate input')
})
