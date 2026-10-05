import { test } from 'node:test'
import assert from 'node:assert/strict'
import { skillDetail, populationProfile } from '../src/utils/skillProfiles.js'

test('source switching selects level, exposure and count together without converting null to zero', () => {
  const profiles = {
    major: { skills: { academics: { level: 5, exposure_hours: 2, activity_count: 1 } } },
    faculty: { skills: { academics: { level: 2, exposure_hours: 6, activity_count: 2 }, volunteerism: { level: 2, exposure_hours: 3, activity_count: 1 } } },
    external: { skills: { academics: { level: 4, exposure_hours: 4, activity_count: 1 } } }
  }
  for (const source of ['major', 'faculty', 'external']) {
    assert.deepEqual(skillDetail(profiles, source, 'academics'), profiles[source].skills.academics)
  }
  assert.deepEqual(skillDetail(profiles, 'faculty', 'volunteerism'), { level: 2, exposure_hours: 3, activity_count: 1 })
  assert.deepEqual(skillDetail(profiles, 'external', 'volunteerism'), { level: null, exposure_hours: 0, activity_count: 0 })
})

test('population filters select backend source averages and sample counts; External has none', () => {
  const api = {
    '["a","b"]': { faculty: { skills: { academics: 3 }, sampleCounts: { academics: 2 }, score: 3, evaluatedCount: 2 }, major: { skills: { academics: 5 }, sampleCounts: { academics: 1 }, score: 5, evaluatedCount: 1 } },
    '["a"]': { faculty: { skills: { academics: 2 }, sampleCounts: { academics: 1 }, score: 2, evaluatedCount: 1 } }
  }
  assert.equal(populationProfile(api, [{ id: 'b' }, { id: 'a' }], 'faculty').skills.academics, 3)
  assert.equal(populationProfile(api, [{ id: 'a' }], 'faculty').skills.academics, 2)
  assert.equal(populationProfile(api, [{ id: 'a' }, { id: 'b' }], 'major').sampleCounts.academics, 1)
  assert.deepEqual(populationProfile(api, [{ id: 'a' }], 'external').skills, {})
  assert.equal(populationProfile(api, [], 'faculty').score, null)
})
