import { test } from 'node:test'
import assert from 'node:assert/strict'
import { validHours } from '../src/utils/activityHours.js'

test('new hours support decimals and reject invalid precision/range', () => {
  for (const value of [1, 1.5, '3.50', 6]) assert.equal(validHours(value), true)
  for (const value of ['', null, undefined, 0, -1, 'NaN', Infinity, 1.234, 100000000]) {
    assert.equal(validHours(value), false)
  }
})

test('existing zero hours remain editable', () => {
  assert.equal(validHours(0, true), true)
  assert.equal(validHours(-1, true), false)
})
