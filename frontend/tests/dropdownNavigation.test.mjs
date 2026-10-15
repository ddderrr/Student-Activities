import { test } from 'node:test'
import assert from 'node:assert/strict'
import { moveActiveIndex, shouldOpenUpward, typeaheadIndex } from '../src/utils/dropdownNavigation.js'

test('arrow keys move one step and stop at the ends (like a native select)', () => {
  assert.equal(moveActiveIndex(0, 'ArrowDown', 4), 1)
  assert.equal(moveActiveIndex(3, 'ArrowDown', 4), 3)
  assert.equal(moveActiveIndex(2, 'ArrowUp', 4), 1)
  assert.equal(moveActiveIndex(0, 'ArrowUp', 4), 0)
  assert.equal(moveActiveIndex(-1, 'ArrowDown', 4), 0)
})

test('Home/End jump to the first/last option, PageUp/PageDown move by 10', () => {
  assert.equal(moveActiveIndex(2, 'Home', 20), 0)
  assert.equal(moveActiveIndex(2, 'End', 20), 19)
  assert.equal(moveActiveIndex(2, 'PageDown', 20), 12)
  assert.equal(moveActiveIndex(15, 'PageDown', 20), 19)
  assert.equal(moveActiveIndex(5, 'PageUp', 20), 0)
})

test('opens below unless the menu does not fit and there is more room above', () => {
  // ช่องอยู่ด้านบนจอ: เปิดลง
  assert.equal(shouldOpenUpward({ top: 100, bottom: 142 }, 300, 900), false)
  // ช่องอยู่ใกล้ขอบล่าง: เปิดขึ้น
  assert.equal(shouldOpenUpward({ top: 800, bottom: 842 }, 300, 900), true)
  // ไม่พอทั้งสองทาง แต่ด้านล่างมีที่มากกว่า: เปิดลง
  assert.equal(shouldOpenUpward({ top: 200, bottom: 242 }, 500, 600), false)
})

test('typing a single character cycles through options starting with it', () => {
  const labels = ['ทุกสาขา', 'เคมี', 'เคมีอุตสาหกรรม', 'ฟิสิกส์', 'Faculty']
  assert.equal(typeaheadIndex(labels, 'เ', 0), 1)
  assert.equal(typeaheadIndex(labels, 'เ', 1), 2)
  assert.equal(typeaheadIndex(labels, 'เ', 2), 1)
  assert.equal(typeaheadIndex(labels, 'f', 0), 4)
  assert.equal(typeaheadIndex(labels, 'zz', 0), -1)
})

test('typing several characters keeps the current option while it still matches', () => {
  const labels = ['ทุกสาขา', 'เคมี', 'เคมีอุตสาหกรรม', 'ฟิสิกส์']
  assert.equal(typeaheadIndex(labels, 'เค', 1), 1)
  assert.equal(typeaheadIndex(labels, 'เคมีอ', 1), 2)
})
