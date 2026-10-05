import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createServer } from 'vite'
import vue from '@vitejs/plugin-vue'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'

// Render the actual SFC templates with isolated API fixtures. Test-only injection
// happens in Vite's memory transform; application files and real data are untouched.
test('Student and Admin skill views switch complete profiles and preserve External no-comparison', async () => {
  globalThis.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} }
  const hydration = {
    name: 'test-skill-api-fixture', enforce: 'pre',
    transform(code, id) {
      if (!id.endsWith('.vue')) return
      let setup
      if (id.endsWith('/StudentSkills.vue')) setup = `
        const fixture = globalThis.__skillViewFixture;
        student.value = fixture.student; periods.value = { 'year-2026': fixture.period };
        selectedPeriod.value = 'year-2026'; comparison.value = fixture.source;
        apiSkillDefinitions.value = fixture.definitions; track.value = fixture.track || 'participant'; loading.value = false;
      `
      if (id.endsWith('/AdminStudentSkills.vue')) setup = `
        const fixture = globalThis.__skillViewFixture;
        students.value = [fixture.row]; selectedStudent.value = fixture.row;
        gapBasis.value = fixture.source.toUpperCase();
        populationProfiles.value = fixture.population; aggregateSource.value = fixture.aggregateSource;
        loadedTrack.value = fixture.track || 'participant';
        skillKeys.splice(0, skillKeys.length, ...SKILL_KEYS_BY_TRACK[loadedTrack.value]);
        selectedYear.value = 2026; loading.value = false;
      `
      if (setup) return code.replace('</script>', `${setup}\n</script>`)
    }
  }
  const server = await createServer({ configFile: false, plugins: [hydration, vue()],
    server: { middlewareMode: true, hmr: false, watch: null }, appType: 'custom',
    logLevel: 'error' })
  try {
    const keys = ['arts_culture_traditions', 'volunteerism', 'academics', 'internationalization', 'health_promotion', 'nature_environmental_conservation']
    const profiles = Object.fromEntries(['major', 'faculty', 'external'].map((source, index) => [source, {
      source, source_activity_hours: [2, 6, 4][index], skills: Object.fromEntries(keys.map(key => [key, {
        level: key === 'academics' || key === 'volunteerism' ? [5, 2, 4][index] : null,
        exposure_hours: key === 'academics' ? [2, 6, 4][index] : key === 'volunteerism' ? [2, 3, 4][index] : 0,
        activity_count: key === 'academics' ? [1, 2, 1][index] : key === 'volunteerism' ? 1 : 0
      }]))
    }]))
    const scores = source => Object.fromEntries(keys.map(key => [key, profiles[source].skills[key].level]))
    const hours = { total: 12, major: 2, faculty: 6, external: 4 }
    const comparisons = Object.fromEntries(['major', 'faculty', 'external'].map(source => [source, {
      skills: scores(source), average: source === 'external' ? null : scores(source)
    }]))
    const row = { id: '690519901', name: 'Example Student', major: 'Chemistry', yearLevel: 1,
      sourceProfiles: profiles, majorSkills: scores('major'), facultySkills: scores('faculty'), externalSkills: scores('external'),
      sourceSummaries: Object.fromEntries(['major', 'faculty', 'external'].map((source, index) => [source, { score: [5, 2, 4][index], primarySkill: 'academics' }])),
      activityCounts: { major: 1, faculty: 2, external: 1 }, hours, majorActivityAverage: scores('major') }
    const activities = ['major', 'faculty', 'external'].map((scope, index) => ({ scope, id: index,
      source: scope, title: `${scope} fixture activity`, skills: { academics: profiles[scope].skills.academics.level },
      activity_hours: profiles[scope].source_activity_hours, start_at: '2026-08-01', status: scope === 'external' ? 'approved' : 'completed' }))
    const fixture = { student: { first_name: 'Example', last_name: 'Student', major: 'Chemistry' }, row,
      period: { sourceProfiles: profiles, comparisons, hours, activities },
      definitions: keys.map(key => ({ key, label: key })),
      population: { '["690519901"]': { major: { skills: scores('major'), score: 5, evaluatedCount: 1 }, faculty: { skills: scores('faculty'), score: 2, evaluatedCount: 1 } } } }
    const language = await server.ssrLoadModule('/src/composables/useLanguage.js')
    const Student = (await server.ssrLoadModule('/src/views/Student/StudentSkills.vue')).default
    const Admin = (await server.ssrLoadModule('/src/views/Admin/AdminStudentSkills.vue')).default
    for (const lang of ['EN', 'TH']) {
      language.useLanguage().setLanguage(lang)
      for (const source of ['major', 'faculty', 'external']) {
        globalThis.__skillViewFixture = { ...fixture, source, aggregateSource: source === 'external' ? 'faculty' : source }
        const studentHtml = await renderToString(createSSRApp(Student))
        const adminHtml = await renderToString(createSSRApp(Admin))
        for (const html of [studentHtml, adminHtml]) {
          assert.match(html, /data-testid="hours-summary"/)
          assert.match(html, lang === 'TH' ? /ประสบการณ์ทักษะ/ : /Skill Exposure/)
          assert.match(html, lang === 'TH' ? /ไม่มีข้อมูลทักษะ/ : /No skill data/)
          assert.ok(!html.includes('External Avg'))
        }
        const modal = adminHtml.slice(adminHtml.indexOf('class="student-detail-modal"'))
        assert.equal((modal.match(/class="individual-skill-metrics"/g) || []).length, 6)
        assert.equal((studentHtml.match(/class="skill-detail-metrics"/g) || []).length, 6)
        assert.ok(studentHtml.includes(`${source} fixture activity`))
        for (const other of ['major', 'faculty', 'external'].filter(value => value !== source)) {
          assert.ok(!studentHtml.includes(`${other} fixture activity`))
        }
        if (source === 'external') {
          assert.ok(!studentHtml.includes('class="faculty-radar"'))
          assert.ok(!modal.includes('class="detail-panel skill-gap-panel"'))
          assert.ok(!modal.includes('class="average-caption"'))
        } else {
          assert.ok(studentHtml.includes('class="faculty-radar"'))
          assert.ok(modal.includes('class="detail-panel skill-gap-panel"'))
        }
        for (const html of [studentHtml, modal]) {
          const exposure = source === 'major' ? 2 : source === 'faculty' ? 6 : 4
          const count = source === 'faculty' ? 2 : 1
          const level = source === 'major' ? '5.00' : source === 'faculty' ? '2.00' : '4.00'
          assert.match(html, new RegExp(`<dd[^>]*>${exposure} `))
          assert.match(html, new RegExp(`<dd[^>]*>${count} (Activities|\u0e01\u0e34\u0e08\u0e01\u0e23\u0e23\u0e21)</dd>`))
          assert.ok(html.includes(level))
          assert.ok(!html.includes('0.00<span'))
          assert.equal((html.match(/<dt[ >]/g) || []).length, 12)
        }
        assert.match(studentHtml, new RegExp(`width:${source === 'major' ? 100 : source === 'faculty' ? 40 : 80}%`))

      }
    }
    language.useLanguage().setLanguage('EN')
    const staffKeys = ['creative_leadership', 'innovation', 'entrepreneurship', 'promote_equality', 'academic', 'nature_environmental']
    const remap = skills => Object.fromEntries(keys.map((key, index) => [staffKeys[index], skills[key]]))
    const staffProfiles = Object.fromEntries(Object.entries(profiles).map(([source, profile]) => [source, { ...profile, skills: remap(profile.skills) }]))
    const staffRow = { ...row, sourceProfiles: staffProfiles, majorSkills: remap(row.majorSkills), facultySkills: remap(row.facultySkills), externalSkills: remap(row.externalSkills) }
    for (const source of ['major', 'faculty', 'external']) {
      globalThis.__skillViewFixture = { ...fixture, source, track: 'staff', aggregateSource: 'faculty', row: staffRow,
        population: { '["690519901"]': { faculty: { skills: remap(scores('faculty')), score: 2, evaluatedCount: 1 }, major: { skills: remap(scores('major')), score: 5, evaluatedCount: 1 } } },
        definitions: staffKeys.map(key => ({ key, label: key })), period: { ...fixture.period, sourceProfiles: staffProfiles } }
      for (const component of [Student, Admin]) {
        const html = await renderToString(createSSRApp(component))
        assert.match(html, /Skill Exposure/)
        assert.match(html, /Staff|staff/)
        assert.ok(!html.includes('External Avg'))
      }
    }
    const emptyProfiles = { ...profiles, external: { ...profiles.external,
      skills: Object.fromEntries(keys.map(key => [key, { level: null, exposure_hours: 0, activity_count: 0 }])) } }
    globalThis.__skillViewFixture = { ...fixture, source: 'external', aggregateSource: 'faculty',
      row: { ...row, sourceProfiles: emptyProfiles }, period: { ...fixture.period, sourceProfiles: emptyProfiles } }
    for (const component of [Student, Admin]) {
      const html = await renderToString(createSSRApp(component))
      assert.match(html, /No approved external activity skill data yet/)
      assert.ok(!html.includes('External Avg'))
    }
  } finally {
    await server.close()
    delete globalThis.__skillViewFixture
    delete globalThis.localStorage
  }
})
