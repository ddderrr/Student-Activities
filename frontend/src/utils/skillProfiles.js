// Select backend results; all weighting and population calculations stay in Python.
export function skillDetail(profiles, source, key) {
  return profiles?.[source]?.skills?.[key] ?? { level: null, exposure_hours: 0, activity_count: 0 }
}

export function populationProfile(profiles, students, source) {
  const key = JSON.stringify(students.map(student => student.id).sort())
  return profiles?.[key]?.[source] ?? { skills: {}, sampleCounts: {}, score: null, evaluatedCount: 0 }
}
