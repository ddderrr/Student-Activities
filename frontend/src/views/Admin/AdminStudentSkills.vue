<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue'

import {
  Search,
  SlidersHorizontal,
  ChevronDown,
  CheckCircle,
  AlertTriangle,
  Check,
  X,
  Settings,
  Save,
  Users
} from 'lucide-vue-next'

import { useLanguage } from '../../composables/useLanguage'
import { adminFetch } from '../../constants/currentAdmin'
import BranchFilterSelect from '../../components/common/BranchFilterSelect.vue'
import { ALL_BRANCHES_VALUE } from '../../constants/branches'

const { t, currentLanguage } = useLanguage()
const API_BASE = 'http://localhost:8000'

/* =========================
   Skill definitions
   participant = skill จากการเป็นผู้เข้าร่วม, staff = skill จากการเป็นผู้จัด (organizer)
   key ต้องตรงกับ PARTICIPANT_SKILL_DEFINITIONS / STAFF_SKILL_DEFINITIONS ใน backend/main.py
========================= */
const SKILL_KEYS_BY_TRACK = {
  participant: [
    { key: 'arts_culture_traditions', label: 'Arts, Culture, and Traditions' },
    { key: 'volunteerism', label: 'Volunteerism' },
    { key: 'academics', label: 'Academics' },
    { key: 'internationalization', label: 'Internationalization' },
    { key: 'health_promotion', label: 'Health Promotion' },
    { key: 'nature_environmental_conservation', label: 'Nature & Environmental Conservation' }
  ],
  staff: [
    { key: 'creative_leadership', label: 'Creative Leadership' },
    { key: 'innovation', label: 'Innovation' },
    { key: 'entrepreneurship', label: 'Entrepreneurship' },
    { key: 'promote_equality', label: 'Promote Equality' },
    { key: 'academic', label: 'Academic' },
    { key: 'nature_environmental', label: 'Nature and Environmental' }
  ]
}

// skillTrack = โหมดที่เลือก (อาจยังโหลดอยู่), loadedTrack = โหมดของข้อมูลที่แสดงอยู่จริง
// benchmark และป้ายต่าง ๆ ใช้ loadedTrack เพื่อไม่ให้บันทึก/แสดงผิดชุดระหว่างกำลังสลับ
const skillTrack = ref('participant')
const loadedTrack = ref('participant')

// array เดียวที่ทั้งหน้าใช้ เปลี่ยนเนื้อหาตามโหมด (reactive จึงคำนวณใหม่ทุกที่อัตโนมัติ)
const skillKeys = reactive([...SKILL_KEYS_BY_TRACK.participant])

const skillDisplay = (label) => {
  // ใช้คำแปลเดิมได้ถ้ามี key ตรงกัน ไม่งั้นแสดง label จาก backend/domain ตรง ๆ
  const keyMap = {
    Leadership: 'leadership',
    'Critical Thinking': 'criticalThinking',
    Communication: 'communication',
    Teamwork: 'teamwork',
    Creativity: 'creativity',
    'Digital Literacy': 'digitalLiteracy',
    'Arts, Culture, and Traditions': 'skillArtsCultureTraditions',
    Volunteerism: 'skillVolunteerism',
    Academics: 'skillAcademics',
    Internationalization: 'skillInternationalization',
    'Health Promotion': 'skillHealthPromotion',
    'Nature & Environmental Conservation': 'skillNatureEnvironmentalConservation',
    'Creative Leadership': 'skillCreativeLeadership',
    Innovation: 'skillInnovation',
    Entrepreneurship: 'skillEntrepreneurship',
    'Promote Equality': 'skillPromoteEquality',
    Academic: 'skillAcademic',
    'Nature and Environmental': 'skillNatureEnvironmental'
  }

  const key = keyMap[label]
  return key ? t.value.adminStudentSkills[key] : label
}

/* =========================
   Radar labels
   label ยาวต้องตัดขึ้นบรรทัดใหม่ ไม่งั้น label ฝั่งซ้าย (text-anchor end)
   จะล้นออกนอก viewBox และโดนตัด
========================= */
const RADAR_LABEL_LINE_HEIGHT = 13
const RADAR_LABEL_MAX_CHARS = 14

const radarLabelPositions = [
  { x: 250, y: 25, anchor: 'middle', align: 'bottom' },
  { x: 395, y: 115, anchor: 'start', align: 'center' },
  { x: 395, y: 278, anchor: 'start', align: 'center' },
  { x: 250, y: 375, anchor: 'middle', align: 'top' },
  { x: 105, y: 278, anchor: 'end', align: 'center' },
  { x: 105, y: 115, anchor: 'end', align: 'center' }
]

// ภาษาไทยไม่เว้นวรรคระหว่างคำ จึงตัดคำด้วย Intl.Segmenter แทนการแยกด้วยช่องว่าง
const thaiWordSegmenter = typeof Intl !== 'undefined' && Intl.Segmenter
  ? new Intl.Segmenter('th', { granularity: 'word' })
  : null

const radarLabelWords = (text) => {
  if (/\s/.test(text) || !thaiWordSegmenter || text.length <= RADAR_LABEL_MAX_CHARS) {
    return { words: text.split(/\s+/), joiner: ' ' }
  }

  return {
    words: [...thaiWordSegmenter.segment(text)].map(part => part.segment),
    joiner: ''
  }
}

const wrapRadarLabel = (label) => {
  const lines = []
  const { words, joiner } = radarLabelWords(String(label))

  for (const word of words) {
    const last = lines[lines.length - 1]

    if (last && `${last}${joiner}${word}`.length <= RADAR_LABEL_MAX_CHARS) {
      lines[lines.length - 1] = `${last}${joiner}${word}`
    } else {
      lines.push(word)
    }
  }

  return lines
}

const radarLabels = computed(() =>
  radarLabelPositions.map((position, index) => {
    const lines = wrapRadarLabel(skillDisplay(skillKeys[index].label))
    const extraHeight = (lines.length - 1) * RADAR_LABEL_LINE_HEIGHT

    let firstDy = 0
    if (position.align === 'bottom') firstDy = -extraHeight
    if (position.align === 'center') firstDy = -extraHeight / 2

    return {
      ...position,
      key: skillKeys[index].key,
      lines,
      firstDy
    }
  })
)

/* =========================
   Loading / API data
========================= */
const loading = ref(false)
const error = ref('')
const students = ref([])
const totalFaculty = ref(0)
const availableYears = ref([])
// จำนวนนักศึกษาทั้งหมดแยกตาม { yearLevel, major } ใช้คำนวณ % เมื่อกรองชั้นปี/สาขา
const population = ref([])

/* =========================
   Reporting period: Year + optional Semester
========================= */
const selectedYear = ref(null)
const selectedPeriod = ref('ALL')
const yearOpen = ref(false)
const periodOpen = ref(false)
// filter สาขา สำหรับแอดมินกลางเท่านั้น (BranchFilterSelect ซ่อนตัวเองให้แอดมินสาขา)
const selectedBranch = ref(ALL_BRANCHES_VALUE)

const changeBranch = () => loadStudentSkills()

const periodOptions = computed(() => [
  { value: 'ALL', label: t.value.adminStudentSkills.periodAll },
  { value: 'SEMESTER_1', label: t.value.adminStudentSkills.periodSemester1 },
  { value: 'SEMESTER_2', label: t.value.adminStudentSkills.periodSemester2 }
])

const selectedPeriodLabel = computed(() =>
  periodOptions.value.find(option => option.value === selectedPeriod.value)?.label ||
  t.value.adminStudentSkills.periodAll
)

const selectYear = async (year) => {
  selectedYear.value = year
  yearOpen.value = false
  await loadStudentSkills()
}

const selectPeriod = async (period) => {
  selectedPeriod.value = period
  periodOpen.value = false
  await loadStudentSkills()
}

/* =========================
   Class year / Major filter (กรองข้อมูลทั้งหน้า)
========================= */
const ALL_OPTION = '__ALL__'
const selectedYearLevel = ref(ALL_OPTION)
const selectedMajor = ref(ALL_OPTION)

// ชั้นปีมาจาก backend (คำนวณจากรหัสนักศึกษา 2 หลักแรก)
// ปี 1-4 แยกกลุ่ม ส่วนปี 5 ขึ้นไปรวมเป็นกลุ่มเดียว
const yearLevelGroup = (level) => {
  if (level === null || level === undefined) return 'UNKNOWN'
  return level >= 5 ? '5+' : String(level)
}

const yearLevelLabel = (group) => {
  const labels = t.value.adminStudentSkills

  return {
    1: labels.yearLevel1,
    2: labels.yearLevel2,
    3: labels.yearLevel3,
    4: labels.yearLevel4,
    '5+': labels.yearLevel5Plus,
    UNKNOWN: labels.yearLevelUnknown
  }[group] ?? group
}

// ปี 1-4 แสดงเสมอ ส่วน "ปี 5 ขึ้นไป" / "ไม่ทราบ" แสดงเมื่อมีนักศึกษากลุ่มนั้น
const yearLevelOptions = computed(() => {
  const present = new Set(
    [...population.value, ...students.value].map(item => yearLevelGroup(item.yearLevel))
  )

  return ['1', '2', '3', '4', '5+', 'UNKNOWN']
    .filter(group => !['5+', 'UNKNOWN'].includes(group) || present.has(group))
    .map(group => ({ value: group, label: yearLevelLabel(group) }))
})

const majorOptions = computed(() => {
  const majors = new Set(
    [...population.value, ...students.value].map(item => item.major || '')
  )

  const named = [...majors]
    .filter(Boolean)
    .sort((a, b) => a.localeCompare(b, 'th'))
    .map(major => ({ value: major, label: major }))

  return majors.has('')
    ? [...named, { value: '', label: t.value.adminStudentSkills.majorNotSpecified }]
    : named
})

const matchesCohort = (item) =>
  (selectedYearLevel.value === ALL_OPTION || yearLevelGroup(item.yearLevel) === selectedYearLevel.value) &&
  (selectedMajor.value === ALL_OPTION || (item.major || '') === selectedMajor.value)

const cohortFilterActive = computed(() =>
  selectedYearLevel.value !== ALL_OPTION || selectedMajor.value !== ALL_OPTION
)

const cohortLabel = computed(() =>
  [
    selectedYearLevel.value !== ALL_OPTION ? yearLevelLabel(selectedYearLevel.value) : null,
    selectedMajor.value !== ALL_OPTION
      ? majorOptions.value.find(option => option.value === selectedMajor.value)?.label ?? selectedMajor.value
      : null
  ].filter(Boolean).join(' · ')
)

const clearCohortFilters = () => {
  selectedYearLevel.value = ALL_OPTION
  selectedMajor.value = ALL_OPTION
}

/* =========================
   Radar Legend
========================= */
const showActual = ref(true)
const showBenchmark = ref(true)

/* =========================
   Search / Filter
========================= */
const searchText = ref('')
const filterOpen = ref(false)
const selectedSkill = ref('All Skills')
const selectedScore = ref('All Scores')

const skillOptions = computed(() => [
  'All Skills',
  ...skillKeys.map((skill) => skill.label)
])

const scoreOptions = [
  'All Scores',
  '4.0 - 5.0',
  '3.0 - 3.9',
  'Below 3.0'
]

/* =========================
   Fetch real data
========================= */
// กันผลลัพธ์เก่ามาทับ เมื่อสลับโหมด/ปีเร็ว ๆ แล้ว response กลับมาไม่ตรงลำดับ
let latestLoadId = 0

const loadStudentSkills = async () => {
  const loadId = ++latestLoadId
  loading.value = true
  error.value = ''

  try {
    const params = new URLSearchParams()
    if (selectedYear.value) params.set('year', selectedYear.value)
    params.set('semester', selectedPeriod.value)
    if (selectedBranch.value !== ALL_BRANCHES_VALUE) {
      params.set('major', selectedBranch.value)
    }
    params.set('track', skillTrack.value)

    const response = await adminFetch(`${API_BASE}/api/admin/student-skills?${params.toString()}`)
    const data = await response.json()

    if (loadId !== latestLoadId) return

    if (!response.ok) {
      throw new Error(data.detail || t.value.adminStudentSkills.loadErrorFallback)
    }

    // เปลี่ยนชุด skill พร้อมกับข้อมูลใหม่ ไม่ให้ key ของโหมดหนึ่งไปอ่านข้อมูลของอีกโหมด
    loadedTrack.value = data.track || skillTrack.value
    skillKeys.splice(0, skillKeys.length, ...SKILL_KEYS_BY_TRACK[loadedTrack.value])
    students.value = Array.isArray(data.students) ? data.students : []

    // หน้ารายละเอียดนักศึกษาที่เปิดค้างไว้ ให้ใช้ข้อมูลชุดใหม่ของคนเดิม (ถ้าไม่มีในชุดนี้ให้ปิด)
    if (selectedStudent.value) {
      selectedStudent.value = students.value.find(student => student.id === selectedStudent.value.id) || null
    }
    availableYears.value = Array.isArray(data.availableYears) ? data.availableYears : []
    totalFaculty.value = Number(data.totalFaculty || 0)
    population.value = Array.isArray(data.population) ? data.population : []

    // เปลี่ยนปีแล้วสาขา/ชั้นปีที่เลือกไว้อาจไม่มีแล้ว ให้กลับไปเป็น "ทั้งหมด"
    if (!yearLevelOptions.value.some(option => option.value === selectedYearLevel.value)) {
      selectedYearLevel.value = ALL_OPTION
    }
    if (!majorOptions.value.some(option => option.value === selectedMajor.value)) {
      selectedMajor.value = ALL_OPTION
    }

    if (!selectedYear.value || !availableYears.value.includes(Number(selectedYear.value))) {
      selectedYear.value = Number(data.defaultYear || data.selectedYear || availableYears.value[0])
    }

    selectedPeriod.value = data.selectedSemester || selectedPeriod.value

    if (Array.isArray(data.benchmarkScores) && data.benchmarkScores.length === 6) {
      benchmarkScores.value = data.benchmarkScores.map(score => Number(score) || 4)
    }
  } catch (err) {
    if (loadId !== latestLoadId) return
    console.error('Student Skills API Error:', err)
    error.value = err.message || t.value.adminStudentSkills.loadErrorFallback
    students.value = []
    // โหลดโหมดใหม่ไม่สำเร็จ: กลับไปที่โหมดของข้อมูลเดิม และให้กดเลือกซ้ำเพื่อลองใหม่ได้
    skillTrack.value = loadedTrack.value
  } finally {
    if (loadId === latestLoadId) loading.value = false
  }
}

const skillTrackOptions = computed(() => [
  { value: 'participant', label: t.value.adminStudentSkills.skillTrackParticipant },
  { value: 'staff', label: t.value.adminStudentSkills.skillTrackStaff }
])

const selectSkillTrack = async (track) => {
  if (track === skillTrack.value && track === loadedTrack.value) return

  skillTrack.value = track
  // ตัวกรอง "ทักษะเด่น" เป็นชื่อ skill ของอีกชุด จึงล้างทิ้ง
  selectedSkill.value = 'All Skills'
  await loadStudentSkills()
}

/* =========================
   Helpers
========================= */
const skillValueOf = (student, skillKey) => {
  const raw = student.skills?.[skillKey]

  // null / undefined = ยังไม่มีหลักฐานจากกิจกรรมที่นักศึกษาคนนี้เข้าร่วม
  if (raw === null || raw === undefined || raw === '') return null

  const value = Number(raw)
  return Number.isFinite(value) ? value : null
}

const averageOfSkills = (student) => {
  // เฉลี่ยเฉพาะ skill ที่นักศึกษาคนนี้มีข้อมูลจริงเท่านั้น
  const values = skillKeys
    .map(skill => skillValueOf(student, skill.key))
    .filter(value => value !== null)

  if (values.length === 0) return null
  return values.reduce((sum, value) => sum + value, 0) / values.length
}

const primarySkillOf = (student) => {
  const availableSkills = skillKeys
    .map(skill => ({
      ...skill,
      score: skillValueOf(student, skill.key)
    }))
    .filter(skill => skill.score !== null)
    .sort((a, b) => b.score - a.score)

  return availableSkills[0]?.label ?? null
}

const scoreMatchesFilter = (score) => {
  if (selectedScore.value === 'All Scores') return true
  if (score === null) return false
  if (selectedScore.value === '4.0 - 5.0') return score >= 4 && score <= 5
  if (selectedScore.value === '3.0 - 3.9') return score >= 3 && score < 4
  if (selectedScore.value === 'Below 3.0') return score < 3
  return true
}

/* =========================
   Selected period data
========================= */
// นักศึกษาในช่วงเวลาที่เลือก หลังกรองชั้นปี/สาขา (ใช้กับทุกส่วนของหน้า)
const semesterStudents = computed(() => students.value.filter(matchesCohort))

const studentsEvaluated = computed(() => semesterStudents.value.length)

// จำนวนนักศึกษาทั้งหมดในกลุ่มที่เลือก (รวมคนที่ยังไม่มีข้อมูล skill)
const studentPopulation = computed(() => {
  if (!population.value.length) return totalFaculty.value

  return population.value
    .filter(matchesCohort)
    .reduce((sum, item) => sum + Number(item.count || 0), 0)
})

const facultyPercentage = computed(() => {
  if (studentPopulation.value === 0) return '0.0'
  return Math.min(100, (studentsEvaluated.value / studentPopulation.value) * 100).toFixed(1)
})

const averageSkillScore = computed(() => {
  const studentAverages = semesterStudents.value
    .map(student => averageOfSkills(student))
    .filter(value => value !== null)

  if (studentAverages.length === 0) return null
  return (studentAverages.reduce((sum, value) => sum + value, 0) / studentAverages.length).toFixed(2)
})

const skillAveragesOf = (list) => {
  const result = {}
  skillKeys.forEach(skill => {
    const values = list
      .map(student => skillValueOf(student, skill.key))
      .filter(value => value !== null)

    result[skill.key] = values.length
      ? values.reduce((sum, value) => sum + value, 0) / values.length
      : null
  })
  return result
}

// ค่าเฉลี่ยของกลุ่มที่เลือก (radar หลัก, Top / Growth Area)
const facultySkillAverages = computed(() => skillAveragesOf(semesterStudents.value))

// ค่าเฉลี่ยทั้งคณะ (ไม่กรองชั้นปี/สาขา) ใช้เทียบในหน้ารายละเอียดนักศึกษา
const wholeFacultySkillAverages = computed(() => skillAveragesOf(students.value))

/* =========================
   Radar calculation
========================= */
const radarCenter = { x: 250, y: 195 }
const radarOuterPoints = [
  { x: 250, y: 45 },
  { x: 380, y: 120 },
  { x: 380, y: 270 },
  { x: 250, y: 345 },
  { x: 120, y: 270 },
  { x: 120, y: 120 }
]

const buildRadarPoints = (scores) => {
  return scores.map((score, index) => {
    const safeScore = Math.max(0, Math.min(5, Number(score) || 0))
    const ratio = safeScore / 5
    const outer = radarOuterPoints[index]
    const x = radarCenter.x + (outer.x - radarCenter.x) * ratio
    const y = radarCenter.y + (outer.y - radarCenter.y) * ratio
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

const actualRadarPoints = computed(() =>
  buildRadarPoints(skillKeys.map(skill => facultySkillAverages.value[skill.key]))
)

const radarVertex = (score, index) => {
  const ratio = Math.max(0, Math.min(5, score)) / 5
  const outer = radarOuterPoints[index]

  return {
    x: radarCenter.x + (outer.x - radarCenter.x) * ratio,
    y: radarCenter.y + (outer.y - radarCenter.y) * ratio
  }
}

/* =========================
   Radar view: ภาพรวม / แยกชั้นปี / แยกสาขา / แยกสาขา × ชั้นปี
   แบบแยกกลุ่มวาดกลุ่มที่เลือกซ้อนบน radar หลัก สูงสุด 3 กลุ่มพร้อมกัน
   (เกิน 3 สีจะแยกกันไม่ออก โดยเฉพาะคนตาบอดสี) ตัวเลขทุกกลุ่มดูได้ในตาราง
========================= */
const radarView = ref('OVERALL')

const radarViewOptions = computed(() => [
  { value: 'OVERALL', label: t.value.adminStudentSkills.radarViewOverall },
  { value: 'YEAR', label: t.value.adminStudentSkills.radarViewByYear },
  { value: 'MAJOR', label: t.value.adminStudentSkills.radarViewByMajor },
  { value: 'MAJOR_YEAR', label: t.value.adminStudentSkills.radarViewByMajorYear }
])

const YEAR_GROUP_ORDER = ['1', '2', '3', '4', '5+', 'UNKNOWN']

const majorLabel = (major) => major || t.value.adminStudentSkills.majorNotSpecified

// เรียงสาขาตามตัวอักษร และให้ "ไม่ระบุสาขา" อยู่ท้ายสุด
const compareMajors = (a, b) => {
  if (a === b) return 0
  if (!a) return 1
  if (!b) return -1
  return a.localeCompare(b, 'th')
}

const skillShortLabel = (skillKey) => ({
  arts_culture_traditions: t.value.adminStudentSkills.skillShortArtsCultureTraditions,
  volunteerism: t.value.adminStudentSkills.skillShortVolunteerism,
  academics: t.value.adminStudentSkills.skillShortAcademics,
  internationalization: t.value.adminStudentSkills.skillShortInternationalization,
  health_promotion: t.value.adminStudentSkills.skillShortHealthPromotion,
  nature_environmental_conservation: t.value.adminStudentSkills.skillShortNatureEnvironmentalConservation,
  creative_leadership: t.value.adminStudentSkills.skillShortCreativeLeadership,
  innovation: t.value.adminStudentSkills.skillShortInnovation,
  entrepreneurship: t.value.adminStudentSkills.skillShortEntrepreneurship,
  promote_equality: t.value.adminStudentSkills.skillShortPromoteEquality,
  academic: t.value.adminStudentSkills.skillShortAcademic,
  nature_environmental: t.value.adminStudentSkills.skillShortNatureEnvironmental
}[skillKey])

// ใช้นักศึกษาหลังกรองชั้นปี/สาขาด้านบน เช่น กรองสาขาเคมี + ดูแยกชั้นปี = เคมีแต่ละชั้นปี
const radarGroups = computed(() => {
  if (radarView.value === 'OVERALL') return []

  const groups = new Map()

  for (const student of semesterStudents.value) {
    const year = yearLevelGroup(student.yearLevel)
    const major = student.major || ''
    const key = radarView.value === 'YEAR'
      ? year
      : radarView.value === 'MAJOR' ? major : `${major}|${year}`

    if (!groups.has(key)) groups.set(key, { key, year, major, students: [] })
    groups.get(key).students.push(student)
  }

  return [...groups.values()]
    .sort((a, b) =>
      (radarView.value === 'YEAR' ? 0 : compareMajors(a.major, b.major)) ||
      YEAR_GROUP_ORDER.indexOf(a.year) - YEAR_GROUP_ORDER.indexOf(b.year)
    )
    .map(group => {
      const averages = skillAveragesOf(group.students)
      const studentAverages = group.students
        .map(student => averageOfSkills(student))
        .filter(value => value !== null)

      let title = majorLabel(group.major)
      if (radarView.value === 'YEAR') title = yearLevelLabel(group.year)
      if (radarView.value === 'MAJOR_YEAR') title = `${majorLabel(group.major)} · ${yearLevelLabel(group.year)}`

      return {
        key: group.key,
        title,
        count: group.students.length,
        averages,
        average: studentAverages.length
          ? studentAverages.reduce((sum, value) => sum + value, 0) / studentAverages.length
          : null,
        points: buildRadarPoints(skillKeys.map(skill => averages[skill.key] ?? 0)),
        // จุดเฉพาะ skill ที่มีข้อมูล ใช้แสดงค่าเมื่อชี้เมาส์
        vertices: skillKeys
          .map((skill, index) => ({ skill, index, score: averages[skill.key] }))
          .filter(item => item.score !== null)
          .map(item => ({
            key: item.skill.key,
            label: skillDisplay(item.skill.label),
            score: item.score,
            ...radarVertex(item.score, item.index)
          }))
      }
    })
})

// สีตาม "กลุ่ม" ไม่ใช่ตามลำดับ: เอากลุ่มหนึ่งออก กลุ่มที่เหลือยังสีเดิม
// ชุดสีนี้ผ่านการตรวจสีสำหรับคนตาบอดสีแบบทุกคู่ รวมกับสีเขียวของ benchmark (#22a06b)
const RADAR_GROUP_LIMIT = 3
const RADAR_GROUP_COLORS = ['#2a78d6', '#eb6834', '#4a3aa7']

// key ของกลุ่มที่แสดงบน radar -> ช่องสี (0-2)
const groupSlots = ref({})

const selectDefaultRadarGroups = () => {
  const largest = [...radarGroups.value]
    .sort((a, b) => b.count - a.count)
    .slice(0, RADAR_GROUP_LIMIT)

  groupSlots.value = Object.fromEntries(largest.map((group, index) => [group.key, index]))
}

// เปลี่ยนมุมมอง: เริ่มจากกลุ่มที่มีนักศึกษามากที่สุด 3 กลุ่ม
watch(radarView, selectDefaultRadarGroups)

// ข้อมูล/ตัวกรองเปลี่ยน: เก็บกลุ่มที่ยังมีอยู่ไว้พร้อมสีเดิม
// JSON แยก [] กับ [''] (กลุ่ม "ไม่ระบุสาขา") ออกจากกันได้ ต่างจาก join
watch(
  () => JSON.stringify(radarGroups.value.map(group => group.key)),
  () => {
    const available = new Set(radarGroups.value.map(group => group.key))
    const kept = Object.entries(groupSlots.value).filter(([key]) => available.has(key))

    if (kept.length) {
      groupSlots.value = Object.fromEntries(kept)
    } else {
      selectDefaultRadarGroups()
    }
  }
)

const radarGroupLimitReached = computed(() =>
  Object.keys(groupSlots.value).length >= RADAR_GROUP_LIMIT
)

const groupColor = (key) => RADAR_GROUP_COLORS[groupSlots.value[key]]

const toggleRadarGroup = (key) => {
  const slots = { ...groupSlots.value }

  if (key in slots) {
    delete slots[key]
  } else {
    const used = new Set(Object.values(slots))
    const free = RADAR_GROUP_COLORS.findIndex((_color, slot) => !used.has(slot))
    if (free === -1) return
    slots[key] = free
  }

  groupSlots.value = slots
}

// วาดตามลำดับช่องสี ให้ซ้อนกันเหมือนเดิมทุกครั้ง
const selectedRadarGroups = computed(() =>
  radarGroups.value
    .filter(group => group.key in groupSlots.value)
    .sort((a, b) => groupSlots.value[a.key] - groupSlots.value[b.key])
    .map(group => ({ ...group, color: groupColor(group.key) }))
)

// tooltip ของแต่ละแกนแสดงค่าของทุกกลุ่มที่เลือก จุดที่ซ้อนกันจึงยังอ่านค่าได้ครบ
const radarAxisTooltips = computed(() =>
  Object.fromEntries(
    skillKeys.map(skill => [
      skill.key,
      `${skillDisplay(skill.label)} — ` + selectedRadarGroups.value
        .map(group => `${group.title} ${group.averages[skill.key] !== null ? group.averages[skill.key].toFixed(2) : '—'}`)
        .join(' · ')
    ])
  )
)

// Benchmark เริ่มต้น 4.0 / 5 ทุก skill
const benchmarkScores = ref([4, 4, 4, 4, 4, 4])
const benchmarkRadarPoints = computed(() => buildRadarPoints(benchmarkScores.value))

const benchmarkModalOpen = ref(false)
const benchmarkDraft = ref([4, 4, 4, 4, 4, 4])
const benchmarkSaving = ref(false)
const benchmarkError = ref('')

const openBenchmarkSettings = () => {
  // ระหว่างกำลังสลับโหมด ค่า benchmark ยังเป็นของโหมดเดิม จึงยังไม่ให้เปิด
  if (loading.value) return

  benchmarkDraft.value = [...benchmarkScores.value]
  benchmarkError.value = ''
  benchmarkModalOpen.value = true
}

// โหมดของข้อมูลเปลี่ยน (เช่นสลับโหมดขณะเปิดหน้าต่างค้างไว้) ปิดหน้าต่าง ไม่ให้บันทึกค่าของอีกชุด
watch(loadedTrack, () => {
  benchmarkModalOpen.value = false
})

const saveBenchmarkSettings = async () => {
  const values = benchmarkDraft.value.map(value => Number(value))
  if (values.some(value => !Number.isFinite(value) || value < 1 || value > 5)) {
    benchmarkError.value = t.value.adminStudentSkills.benchmarkRangeError
    return
  }

  // ใช้โหมดและ key ชุดเดียวกับที่แสดงในหน้าต่างตอนกดบันทึก
  const track = loadedTrack.value
  const scores = Object.fromEntries(skillKeys.map((skill, index) => [skill.key, values[index]]))

  benchmarkSaving.value = true
  benchmarkError.value = ''
  try {
    const response = await adminFetch(`${API_BASE}/api/admin/student-skills/benchmark?track=${track}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scores })
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || t.value.adminStudentSkills.saveBenchmarkErrorFallback)

    // สลับโหมดไประหว่างรอ: บันทึกลงชุดเดิมสำเร็จแล้ว แต่ไม่เอาค่ามาทับ benchmark ของชุดที่แสดงอยู่
    if (track !== loadedTrack.value) return

    benchmarkScores.value = data.benchmarkScores.map(Number)
    benchmarkDraft.value = [...benchmarkScores.value]
    benchmarkModalOpen.value = false
  } catch (err) {
    benchmarkError.value = err.message || t.value.adminStudentSkills.saveBenchmarkErrorFallback
  } finally {
    benchmarkSaving.value = false
  }
}

/* =========================
   Top / Growth Area
========================= */
// จัดอันดับเฉพาะ skill ที่มีข้อมูลจริง ไม่งั้น skill ที่ไม่มีข้อมูลจะกลายเป็น Growth Area เสมอ
const rankedFacultySkills = computed(() =>
  skillKeys
    .map(skill => ({
      ...skill,
      score: facultySkillAverages.value[skill.key]
    }))
    .filter(skill => skill.score !== null)
    .sort((a, b) => b.score - a.score)
)

const topArea = computed(() => rankedFacultySkills.value[0] ?? null)
const growthArea = computed(() => rankedFacultySkills.value.at(-1) ?? null)

const growthActionPlan = computed(() => {
  const area = growthArea.value?.key

  const plans = {
    arts_culture_traditions: t.value.adminStudentSkills.growthPlanArtsCultureTraditions,
    volunteerism: t.value.adminStudentSkills.growthPlanVolunteerism,
    academics: t.value.adminStudentSkills.growthPlanAcademics,
    internationalization: t.value.adminStudentSkills.growthPlanInternationalization,
    health_promotion: t.value.adminStudentSkills.growthPlanHealthPromotion,
    nature_environmental_conservation: t.value.adminStudentSkills.growthPlanNatureEnvironmentalConservation,
    creative_leadership: t.value.adminStudentSkills.growthPlanCreativeLeadership,
    innovation: t.value.adminStudentSkills.growthPlanInnovation,
    entrepreneurship: t.value.adminStudentSkills.growthPlanEntrepreneurship,
    promote_equality: t.value.adminStudentSkills.growthPlanPromoteEquality,
    academic: t.value.adminStudentSkills.growthPlanAcademic,
    nature_environmental: t.value.adminStudentSkills.growthPlanNatureEnvironmental
  }

  return plans[area] ?? '—'
})

/* =========================
   Search + Filter Result
========================= */
const filteredStudents = computed(() => {
  const keyword = searchText.value.trim().toLowerCase()

  return semesterStudents.value
    .map(student => ({
      ...student,
      score: averageOfSkills(student),
      primarySkill: primarySkillOf(student)
    }))
    .filter(student => {
      const matchesSearch = !keyword ||
        student.name.toLowerCase().includes(keyword) ||
        student.id.toString().toLowerCase().includes(keyword)

      const matchesSkill = selectedSkill.value === 'All Skills' ||
        student.primarySkill === selectedSkill.value

      const matchesScore = scoreMatchesFilter(student.score)

      return matchesSearch && matchesSkill && matchesScore
    })
})

/* =========================
   Individual Student Detail / Radar
========================= */
const selectedStudent = ref(null)
const imageErrors = ref({})

const selectedStudentRadarPoints = computed(() => {
  if (!selectedStudent.value) return buildRadarPoints([0, 0, 0, 0, 0, 0])

  return buildRadarPoints(
    // SVG polygon needs six coordinates; missing values use center only for drawing.
    // The score cards below display these values as N/A, never as 0.
    skillKeys.map(skill => skillValueOf(selectedStudent.value, skill.key) ?? 0)
  )
})

const selectedFacultyRadarPoints = computed(() =>
  buildRadarPoints(
    skillKeys.map(skill => wholeFacultySkillAverages.value[skill.key] ?? 0)
  )
)

// นักศึกษาทุกคนในสาขาเดียวกัน (ในปี/ภาคเรียนที่เลือก ไม่ขึ้นกับตัวกรองด้านบน) รวมคนที่เลือกด้วย
const selectedMajorStudents = computed(() => {
  if (!selectedStudent.value) return []

  const major = selectedStudent.value.major || ''
  return students.value.filter(student => (student.major || '') === major)
})

const selectedMajorAverages = computed(() => skillAveragesOf(selectedMajorStudents.value))

const selectedMajorRadarPoints = computed(() =>
  buildRadarPoints(
    skillKeys.map(skill => selectedMajorAverages.value[skill.key] ?? 0)
  )
)

const selectedMajorLabel = computed(() =>
  selectedStudent.value ? majorLabel(selectedStudent.value.major) : ''
)

// Skill Gap เทียบกับค่าเฉลี่ยสาขา (ค่าเริ่มต้น) หรือค่าเฉลี่ยคณะ
const gapBasis = ref('MAJOR')

const formatScore = (value) => (value === null || value === undefined ? '—' : value.toFixed(1))

const selectedStudentAverage = computed(() => {
  if (!selectedStudent.value) return null
  return averageOfSkills(selectedStudent.value)
})

const selectedStrongestSkill = computed(() => {
  if (!selectedStudent.value) return null

  return skillKeys
    .map(skill => ({
      ...skill,
      score: skillValueOf(selectedStudent.value, skill.key)
    }))
    .filter(skill => skill.score !== null)
    .sort((a, b) => b.score - a.score)[0] ?? null
})

const recommendationBySkill = computed(() => ({
  arts_culture_traditions: t.value.adminStudentSkills.recommendationArtsCultureTraditions,
  volunteerism: t.value.adminStudentSkills.recommendationVolunteerism,
  academics: t.value.adminStudentSkills.recommendationAcademics,
  internationalization: t.value.adminStudentSkills.recommendationInternationalization,
  health_promotion: t.value.adminStudentSkills.recommendationHealthPromotion,
  nature_environmental_conservation: t.value.adminStudentSkills.recommendationNatureEnvironmentalConservation,
  creative_leadership: t.value.adminStudentSkills.recommendationCreativeLeadership,
  innovation: t.value.adminStudentSkills.recommendationInnovation,
  entrepreneurship: t.value.adminStudentSkills.recommendationEntrepreneurship,
  promote_equality: t.value.adminStudentSkills.recommendationPromoteEquality,
  academic: t.value.adminStudentSkills.recommendationAcademic,
  nature_environmental: t.value.adminStudentSkills.recommendationNatureEnvironmental
}))

const selectedSkillGaps = computed(() => {
  if (!selectedStudent.value) return []

  const basisAverages = gapBasis.value === 'MAJOR'
    ? selectedMajorAverages.value
    : wholeFacultySkillAverages.value

  return skillKeys
    .map(skill => {
      const studentScore = skillValueOf(selectedStudent.value, skill.key)
      const compareScore = Number(basisAverages[skill.key] ?? 0)

      // ไม่มีข้อมูลของนักศึกษาคนนี้ = ไม่เอาไปสรุปว่าเป็น skill gap
      if (studentScore === null || compareScore <= 0) return null

      const difference = studentScore - compareScore
      const percentDifference = (difference / compareScore) * 100

      return {
        ...skill,
        studentScore,
        compareScore,
        difference,
        percentDifference,
        recommendation: recommendationBySkill.value[skill.key]
      }
    })
    .filter(skill => skill && skill.difference < -0.05)
    .sort((a, b) => a.difference - b.difference)
})

// แสดง Skill Gap ที่ต่ำกว่าค่าเฉลี่ยที่เลือกเทียบทั้งหมด
// ไม่ตัดเหลือแค่ 3 รายการ เพื่อให้ผู้ใช้เห็นครบทุก Skill ที่มีช่องว่าง
const selectedTopGaps = computed(() => selectedSkillGaps.value)

const selectedStudentPhoto = computed(() => {
  if (!selectedStudent.value) return ''
  return selectedStudent.value.image || `/images/students/${selectedStudent.value.id}.jpg`
})

const selectedInitials = computed(() => {
  const name = selectedStudent.value?.name?.trim() || ''
  if (!name) return 'ST'

  return name
    .split(/\s+/)
    .slice(0, 2)
    .map(part => part.charAt(0).toUpperCase())
    .join('')
})

const photoHasError = computed(() => {
  const id = selectedStudent.value?.id
  return id ? Boolean(imageErrors.value[id]) : false
})

const handlePhotoError = () => {
  const id = selectedStudent.value?.id
  if (!id) return

  imageErrors.value = {
    ...imageErrors.value,
    [id]: true
  }
}

const openStudentRadar = (student) => {
  selectedStudent.value = student
}

const closeStudentRadar = () => {
  selectedStudent.value = null
}

/* =========================
   Student Activity History Modal
========================= */
const activityHistoryStudent = ref(null)
const activityHistoryItems = ref([])
const activityHistoryLoading = ref(false)
const activityHistoryError = ref('')

const openActivityHistory = async (student) => {
  activityHistoryStudent.value = student
  activityHistoryItems.value = []
  activityHistoryError.value = ''
  activityHistoryLoading.value = true

  try {
    const response = await adminFetch(`${API_BASE}/api/admin/students/${student.id}/activities`)

    if (!response.ok) throw new Error(t.value.adminStudentSkills.activityHistoryError)

    const data = await response.json()
    activityHistoryItems.value = data.activities || []
  } catch (error) {
    activityHistoryError.value = error.message || t.value.adminStudentSkills.activityHistoryError
  } finally {
    activityHistoryLoading.value = false
  }
}

const closeActivityHistory = () => {
  activityHistoryStudent.value = null
  activityHistoryItems.value = []
  activityHistoryError.value = ''
}

function activityTypeLabel(source) {
  return source === 'external_activity'
    ? t.value.adminStudentSkills.activityTypeExternal
    : t.value.adminStudentSkills.activityTypeFaculty
}

function activityRoleLabel(role) {
  return role === 'organizer'
    ? t.value.adminStudentSkills.roleOrganizer
    : t.value.adminStudentSkills.roleParticipant
}

function activityStatusLabel(status) {
  if (status === 'approved') return t.value.adminStudentSkills.statusApproved
  if (status === 'rejected') return t.value.adminStudentSkills.statusRejected
  return t.value.adminStudentSkills.statusPending
}

function formatActivityDateShort(date, { withYear = true } = {}) {
  if (!date || Number.isNaN(date.getTime())) return '—'

  const options = { day: 'numeric', month: 'short' }
  if (withYear) options.year = 'numeric'

  return new Intl.DateTimeFormat(currentLanguage.value === 'TH' ? 'th-TH' : 'en-US', options).format(date)
}

// รูปแบบสั้น ๆ เช่น "17 Sep - 25 Sep 2026" (ตัดปีของวันเริ่มออกถ้าอยู่ปีเดียวกัน)
// เพื่อไม่ให้ column DATE กว้างเกินไปจนทับ column อื่นในตาราง
function activityDateRange(item) {
  const start = item.start_at ? new Date(item.start_at) : null
  const end = item.end_at ? new Date(item.end_at) : null

  const startValid = start && !Number.isNaN(start.getTime())
  const endValid = end && !Number.isNaN(end.getTime())

  if (!startValid && !endValid) return '—'
  if (!startValid || !endValid) return formatActivityDateShort(startValid ? start : end)

  if (start.toDateString() === end.toDateString()) {
    return formatActivityDateShort(start)
  }

  const sameYear = start.getFullYear() === end.getFullYear()
  const startLabel = formatActivityDateShort(start, { withYear: !sameYear })
  const endLabel = formatActivityDateShort(end, { withYear: true })

  return `${startLabel} - ${endLabel}`
}

const handleEscape = (event) => {
  if (event.key === 'Escape') {
    if (selectedStudent.value) closeStudentRadar()
    if (activityHistoryStudent.value) closeActivityHistory()
    if (benchmarkModalOpen.value) benchmarkModalOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleEscape)
  loadStudentSkills()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEscape)
})
</script>


<template>

  <div class="student-skills-page">

    <!-- =========================
         Header
    ========================== -->

    <div class="page-header">

      <div>
        <h1>{{ t.adminStudentSkills.title }}</h1>

        <p>
          {{ t.adminStudentSkills.subtitle }}
        </p>
      </div>

    </div>

    <section class="branch-filter-row">
      <BranchFilterSelect v-model="selectedBranch" @update:model-value="changeBranch" />
    </section>

    <div v-if="error" class="skills-api-error">
      {{ error }}
    </div>


    <!-- =========================
         Class year / Major filter (ใช้กับทั้งหน้า)
    ========================== -->

    <section class="cohort-bar">

      <div class="cohort-bar-title">
        <Users :size="16" />
        <span>{{ t.adminStudentSkills.cohortFilterTitle }}</span>
      </div>

      <!-- โหมด skill: ผู้เข้าร่วม / ผู้จัด (staff) ใช้กับทั้งหน้า -->
      <div class="skill-track-switch" role="group" :aria-label="t.adminStudentSkills.skillTrackLabel">
        <span>{{ t.adminStudentSkills.skillTrackLabel }}</span>
        <button
          v-for="option in skillTrackOptions"
          :key="option.value"
          type="button"
          :class="{ active: skillTrack === option.value }"
          :aria-pressed="skillTrack === option.value"
          :disabled="loading && skillTrack !== option.value"
          @click="selectSkillTrack(option.value)"
        >
          {{ option.label }}
        </button>
      </div>

      <label class="cohort-field">
        <span>{{ t.adminStudentSkills.yearLevelFilterLabel }}</span>
        <select v-model="selectedYearLevel">
          <option :value="ALL_OPTION">{{ t.adminStudentSkills.allYearLevels }}</option>
          <option
            v-for="option in yearLevelOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>
      </label>

      <label class="cohort-field">
        <span>{{ t.adminStudentSkills.majorFilterLabel }}</span>
        <select v-model="selectedMajor">
          <option :value="ALL_OPTION">{{ t.adminStudentSkills.allMajors }}</option>
          <option
            v-for="option in majorOptions"
            :key="option.value || '__none__'"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>
      </label>

      <button
        v-if="cohortFilterActive"
        class="cohort-clear"
        type="button"
        @click="clearCohortFilters"
      >
        <X :size="13" />
        {{ t.adminStudentSkills.clearCohortFilters }}
      </button>

      <span class="cohort-hint">{{ t.adminStudentSkills.yearLevelHint }}</span>

      <p v-if="loadedTrack === 'staff'" class="skill-track-hint">
        {{ t.adminStudentSkills.skillTrackStaffHint }}
      </p>

    </section>


    <!-- =========================
         Summary Cards
    ========================== -->

    <section class="summary-grid">

      <!-- Average Skill Score -->

      <div class="summary-card">

        <div class="summary-icon blue">
          <CheckCircle :size="20" />
        </div>

        <div class="summary-info">

          <span class="summary-label">
            {{ t.adminStudentSkills.averageSkillScore }}
          </span>

          <strong class="summary-value">
            {{ averageSkillScore ?? '—' }}
            <small>/ 5.0</small>
          </strong>

          <span class="summary-sub">
            {{ selectedPeriod === 'ALL' ? `${t.adminStudentSkills.yearLabel} ${selectedYear}` : `${selectedPeriodLabel} / ${selectedYear}` }}
          </span>

        </div>

      </div>


      <!-- Students Evaluated -->

      <div class="summary-card">

        <div class="summary-icon gray">
          <CheckCircle :size="20" />
        </div>

        <div class="summary-info">

          <span class="summary-label">
            {{ t.adminStudentSkills.studentsEvaluated }}
          </span>

          <strong class="summary-value">
            {{ studentsEvaluated ?? '—' }}
          </strong>

          <span class="summary-sub">
            {{ facultyPercentage ?? '—' }}% {{ cohortFilterActive ? `${t.adminStudentSkills.ofSelectedGroup} (${studentPopulation})` : t.adminStudentSkills.ofTotalFaculty }}
          </span>

        </div>

      </div>

    </section>


    <!-- =========================
         Main Skill Section
    ========================== -->

    <section class="skill-layout">


      <!-- =========================
           Radar Chart
      ========================== -->

      <div class="card radar-card">

        <div class="card-header">

          <div class="radar-title">
            <h2>{{ t.adminStudentSkills.facultyRadar }}</h2>
            <span v-if="loadedTrack === 'staff'" class="cohort-chip track-chip">{{ t.adminStudentSkills.skillTrackStaff }}</span>
            <span v-if="cohortFilterActive" class="cohort-chip">{{ cohortLabel }}</span>
          </div>

          <div class="report-controls">
            <div class="semester-dropdown">
              <button class="semester-select" @click="yearOpen = !yearOpen; periodOpen = false">
                {{ t.adminStudentSkills.yearLabel }} {{ selectedYear }}
                <ChevronDown :size="14" />
              </button>
              <div v-if="yearOpen" class="semester-menu">
                <button
                  v-for="year in availableYears"
                  :key="year"
                  class="semester-option"
                  :class="{ selected: year === selectedYear }"
                  @click="selectYear(year)"
                >
                  <span>{{ year }}</span><Check v-if="year === selectedYear" :size="13" />
                </button>
              </div>
            </div>

            <div class="semester-dropdown">
              <button class="semester-select" @click="periodOpen = !periodOpen; yearOpen = false">
                {{ selectedPeriodLabel }}
                <ChevronDown :size="14" />
              </button>
              <div v-if="periodOpen" class="semester-menu period-menu">
                <button
                  v-for="option in periodOptions"
                  :key="option.value"
                  class="semester-option"
                  :class="{ selected: option.value === selectedPeriod }"
                  @click="selectPeriod(option.value)"
                >
                  <span>{{ option.label }}</span><Check v-if="option.value === selectedPeriod" :size="13" />
                </button>
              </div>
            </div>

            <button class="benchmark-settings-button" type="button" :disabled="loading" @click="openBenchmarkSettings">
              <Settings :size="14" /> {{ t.adminStudentSkills.benchmarkButton }}
            </button>
          </div>

        </div>

        <!-- View: ภาพรวม / แยกกลุ่ม -->

        <div class="radar-view-switch" role="group" :aria-label="t.adminStudentSkills.radarViewLabel">
          <span class="radar-view-label">{{ t.adminStudentSkills.radarViewLabel }}</span>
          <button
            v-for="option in radarViewOptions"
            :key="option.value"
            type="button"
            class="radar-view-option"
            :class="{ active: radarView === option.value }"
            :aria-pressed="radarView === option.value"
            @click="radarView = option.value"
          >
            {{ option.label }}
          </button>
        </div>

        <!-- Radar -->

        <div class="radar-container">

          <svg
               class="radar"
               viewBox="0 0 500 400"
               >
               <!-- =========================
                    6-Sided Radar Grid
               ========================== -->
               <!-- Radar scale: center = 0, rings = 1, 2, 3, 4, 5 -->
               <polygon points="250,165 276,180 276,210 250,225 224,210 224,180" class="radar-grid" />
               <polygon points="250,135 302,165 302,225 250,255 198,225 198,165" class="radar-grid" />
               <polygon points="250,105 328,150 328,240 250,285 172,240 172,150" class="radar-grid" />
               <polygon points="250,75 354,135 354,255 250,315 146,255 146,135" class="radar-grid" />
               <polygon points="250,45 380,120 380,270 250,345 120,270 120,120" class="radar-grid" />


               <!-- =========================
                    Axis Lines
               ========================== -->

               <!-- Top -->
               <line
               x1="250"
               y1="195"
               x2="250"
               y2="45"
               class="radar-axis"
               />

               <!-- Top Right -->
               <line
               x1="250"
               y1="195"
               x2="380"
               y2="120"
               class="radar-axis"
               />

               <!-- Bottom Right -->
               <line
               x1="250"
               y1="195"
               x2="380"
               y2="270"
               class="radar-axis"
               />

               <!-- Bottom -->
               <line
               x1="250"
               y1="195"
               x2="250"
               y2="345"
               class="radar-axis"
               />

               <!-- Bottom Left -->
               <line
               x1="250"
               y1="195"
               x2="120"
               y2="270"
               class="radar-axis"
               />

               <!-- Top Left -->
               <line
               x1="250"
               y1="195"
               x2="120"
               y2="120"
               class="radar-axis"
               />


               <!-- =========================
                    {{ t.adminStudentSkills.actualProficiency }}
                    ยังไม่มีข้อมูล
               ========================== -->

               <polygon
               v-if="radarView === 'OVERALL' && showActual"
               :points="actualRadarPoints"
               class="radar-area actual-area"
               />

               <!-- แยกกลุ่ม: 1 รูปต่อกลุ่มที่เลือก (สูงสุด 3) สีตามกลุ่ม -->
               <template v-if="radarView !== 'OVERALL'">
                 <polygon
                   v-for="group in selectedRadarGroups"
                   :key="`area-${group.key}`"
                   :points="group.points"
                   class="group-area"
                   :style="{ stroke: group.color, fill: group.color }"
                 />
               </template>


               <!-- =========================
                    {{ t.adminStudentSkills.benchmarkLevel }}
                    ยังไม่มีข้อมูล
               ========================== -->

               <polygon
               v-if="showBenchmark"
               :points="benchmarkRadarPoints"
               class="benchmark-area"
               />

               <!-- จุดของแต่ละกลุ่ม: ชี้เมาส์เพื่อดูค่า
                    วงรับเมาส์ (ใหญ่) ของทุกกลุ่มอยู่ใต้จุดที่มองเห็นทั้งหมด
                    ชี้ที่จุดไหนจึงได้ค่าของจุดนั้นเสมอ แม้จุดของหลายกลุ่มอยู่ใกล้กัน -->
               <template v-if="radarView !== 'OVERALL'">
                 <g
                   v-for="group in selectedRadarGroups"
                   :key="`hits-${group.key}`"
                 >
                   <circle
                     v-for="vertex in group.vertices"
                     :key="vertex.key"
                     :cx="vertex.x"
                     :cy="vertex.y"
                     r="12"
                     class="group-point-hit"
                   >
                     <title>{{ radarAxisTooltips[vertex.key] }}</title>
                   </circle>
                 </g>

                 <g
                   v-for="group in selectedRadarGroups"
                   :key="`points-${group.key}`"
                 >
                   <circle
                     v-for="vertex in group.vertices"
                     :key="vertex.key"
                     :cx="vertex.x"
                     :cy="vertex.y"
                     r="4.5"
                     class="group-point"
                     :style="{ fill: group.color }"
                   >
                     <title>{{ radarAxisTooltips[vertex.key] }}</title>
                   </circle>
                 </g>
               </template>


               <!-- Center -->
               <circle
               cx="250"
               cy="195"
               r="3"
               class="radar-point"
               />


               <!-- =========================
                    Labels
               ========================== -->

               <text
               v-for="label in radarLabels"
               :key="label.key"
               :x="label.x"
               :y="label.y"
               :text-anchor="label.anchor"
               class="radar-label"
               >
               <tspan
                    v-for="(line, lineIndex) in label.lines"
                    :key="lineIndex"
                    :x="label.x"
                    :dy="lineIndex === 0 ? label.firstDy : RADAR_LABEL_LINE_HEIGHT"
               >{{ line }}</tspan>
               </text>

          </svg>

        </div>


        <!-- Legend -->

        <div v-if="radarView !== 'OVERALL'" class="radar-group-legend">

          <p v-if="!radarGroups.length" class="radar-group-hint">
            {{ t.adminStudentSkills.noStudentData }}
          </p>

          <template v-else>
            <p class="radar-group-hint">{{ t.adminStudentSkills.radarGroupHint }}</p>

            <div class="radar-group-chips">
              <button
                v-for="group in radarGroups"
                :key="group.key"
                type="button"
                class="radar-group-chip"
                :class="{ selected: group.key in groupSlots }"
                :disabled="!(group.key in groupSlots) && radarGroupLimitReached"
                :aria-pressed="group.key in groupSlots"
                @click="toggleRadarGroup(group.key)"
              >
                <span
                  class="radar-group-swatch"
                  :style="group.key in groupSlots ? { background: groupColor(group.key) } : null"
                ></span>
                {{ group.title }}
                <small>({{ group.count }})</small>
              </button>
            </div>
          </template>

          <button
            class="legend-button"
            :class="{ inactive: !showBenchmark }"
            @click="showBenchmark = !showBenchmark"
          >
            <span class="legend-dot benchmark" :class="{ inactive: !showBenchmark }"></span>
            {{ t.adminStudentSkills.benchmarkLevel }}
          </button>

          <!-- ตารางตัวเลขของทุกกลุ่ม (ดูค่าจริงได้โดยไม่ต้องชี้เมาส์) -->
          <details v-if="radarGroups.length" class="radar-table-view">
            <summary>{{ t.adminStudentSkills.showGroupTable }}</summary>

            <div class="radar-table-scroll">
              <table class="radar-group-table">
                <thead>
                  <tr>
                    <th>{{ t.adminStudentSkills.groupColumn }}</th>
                    <th>{{ t.adminStudentSkills.studentsColumn }}</th>
                    <th
                      v-for="skill in skillKeys"
                      :key="skill.key"
                      :title="skillDisplay(skill.label)"
                    >
                      {{ skillShortLabel(skill.key) }}
                    </th>
                    <th>{{ t.adminStudentSkills.avgShort }}</th>
                  </tr>
                </thead>

                <tbody>
                  <tr v-for="group in radarGroups" :key="group.key">
                    <td class="group-name">
                      <span
                        v-if="group.key in groupSlots"
                        class="radar-group-swatch"
                        :style="{ background: groupColor(group.key) }"
                      ></span>
                      {{ group.title }}
                    </td>
                    <td>{{ group.count }}</td>
                    <td v-for="skill in skillKeys" :key="skill.key">
                      {{ group.averages[skill.key] !== null ? group.averages[skill.key].toFixed(2) : '—' }}
                    </td>
                    <td><strong>{{ group.average !== null ? group.average.toFixed(2) : '—' }}</strong></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </details>

        </div>

        <div v-else class="radar-legend">

               <button
               class="legend-button"
               :class="{ inactive: !showActual }"
               @click="showActual = !showActual"
               >
               <span class="legend-dot actual" :class="{ inactive: !showActual }"></span>
               {{ t.adminStudentSkills.actualProficiency }}
               </button>

               <button
               class="legend-button"
               :class="{ inactive: !showBenchmark }"
               @click="showBenchmark = !showBenchmark"
               >
               <span class="legend-dot benchmark" :class="{ inactive: !showBenchmark }"></span>
               {{ t.adminStudentSkills.benchmarkLevel }}
               </button>

          </div>

      </div>


      <!-- =========================
           Right Information
      ========================== -->

      <div class="side-information">


        <!-- Top Area -->

        <div class="card info-card top-area">

          <div class="info-title">

            <CheckCircle :size="18" />

            <span>
              {{ t.adminStudentSkills.topArea }}: {{ topArea ? skillDisplay(topArea.label).toUpperCase() : t.adminStudentSkills.notAvailable }}
            </span>

          </div>

          <p>
            {{ cohortFilterActive ? t.adminStudentSkills.groupAverage : t.adminStudentSkills.facultyAverage }}: {{ topArea ? topArea.score.toFixed(2) : t.adminStudentSkills.notAvailable }}<template v-if="topArea"> / 5.0</template>
          </p>


          <div class="info-item">

            <CheckCircle :size="13" />

            <span>
              {{ t.adminStudentSkills.highestScore }}: {{ topArea ? topArea.score.toFixed(2) : t.adminStudentSkills.notAvailable }}
            </span>

          </div>


          <div class="info-item">

            <CheckCircle :size="13" />

            <span>
              {{ t.adminStudentSkills.studentsEvaluated }}: {{ studentsEvaluated }}
            </span>

          </div>

        </div>


        <!-- Growth Area -->

        <div class="card info-card growth-area">

          <div class="info-title">

            <AlertTriangle :size="18" />

            <span>
              {{ t.adminStudentSkills.growthArea }}
            </span>

          </div>

          <p>
            {{ growthArea ? skillDisplay(growthArea.label) : t.adminStudentSkills.notAvailable }}
            <span v-if="growthArea"> — {{ growthArea.score.toFixed(2) }} / 5.0</span>
          </p>


          <div class="action-plan">

            <strong>
              {{ t.adminStudentSkills.actionPlan }}
            </strong>

            <span>
              {{ growthActionPlan }}
            </span>

          </div>

        </div>

      </div>

    </section>


    <!-- =========================
         Individual Skills
    ========================== -->

    <section class="card students-card">

      <div class="students-header">

        <h2>{{ t.adminStudentSkills.individualSkills }}</h2>


        <div class="table-tools">

          <!-- Search -->

          <div class="search-box">

            <Search :size="14" />

            <input
              v-model="searchText"
              type="text"
              :placeholder="t.adminStudentSkills.searchPlaceholder"
            />

          </div>


          <!-- Filter -->

          <div class="filter-wrapper">

               <button
               class="filter-button"
               @click="filterOpen = !filterOpen"
               >

               <SlidersHorizontal :size="16" />

               </button>


               <div
               v-if="filterOpen"
               class="filter-panel"
               >

               <div class="filter-title">
                    {{ t.adminStudentSkills.filterStudents }}
               </div>


               <label>
                    {{ t.adminStudentSkills.primarySkill }}
               </label>

               <select v-model="selectedSkill">

                    <option
                    v-for="skill in skillOptions"
                    :key="skill"
                    :value="skill"
                    >
                    {{ skill === 'All Skills' ? t.adminStudentSkills.allSkills : skillDisplay(skill) }}
                    </option>

               </select>


               <label>
                    {{ t.adminStudentSkills.scoreAverage }}
               </label>

               <select v-model="selectedScore">

                    <option
                    v-for="score in scoreOptions"
                    :key="score"
                    :value="score"
                    >
                    {{ score === 'All Scores' ? t.adminStudentSkills.allScores : score === 'Below 3.0' ? t.adminStudentSkills.belowScore3 : score }}
                    </option>

               </select>

               </div>

          </div>

        </div>

      </div>


      <!-- Table -->

      <div class="table-wrapper">

        <table>

          <thead>

            <tr>

              <th>
                {{ t.adminStudentSkills.studentName }}
              </th>

              <th>
                {{ t.adminStudentSkills.studentId }}
              </th>

              <th>
                {{ t.adminStudentSkills.yearLevelColumn }}
              </th>

              <th>
                {{ t.adminStudentSkills.major }}
              </th>

              <th>
                {{ t.adminStudentSkills.primarySkill }}
              </th>

              <th>
                {{ t.adminStudentSkills.scoreAvg }}
              </th>

              <th>
                {{ t.adminStudentSkills.activitiesAttended }}
              </th>

              <th>
                {{ t.adminStudentSkills.action }}
              </th>

            </tr>

          </thead>


          <tbody>

            <tr v-if="filteredStudents.length === 0">

              <td
                colspan="8"
                class="empty-row"
              >
                {{ t.adminStudentSkills.noStudentData }}
              </td>

            </tr>

          <!-- กรองหลัง ID -->
            <tr
               v-for="student in filteredStudents" 
               :key="student.id"
               >

              <td>
                {{ student.name }}
              </td>

              <td>
                {{ student.id }}
              </td>

              <td>
                {{ yearLevelLabel(yearLevelGroup(student.yearLevel)) }}
              </td>

              <td>
                {{ student.major || '—' }}
              </td>

              <td>
                {{ student.primarySkill ? skillDisplay(student.primarySkill) : t.adminStudentSkills.notAvailable }}
              </td>

              <td>
                {{ student.score !== null ? student.score.toFixed(2) : t.adminStudentSkills.notAvailable }}
              </td>

              <td>
                <strong>{{ student.activityCount ?? 0 }}</strong> {{ t.adminStudentSkills.activitiesUnit }}
              </td>

              <td>

                <div class="action-buttons">

                  <button
                    class="radar-button"
                    @click="openStudentRadar(student)"
                  >
                    {{ t.adminStudentSkills.viewRadar }}
                  </button>

                  <button
                    class="activities-button"
                    @click="openActivityHistory(student)"
                  >
                    {{ t.adminStudentSkills.viewActivities }}
                  </button>

                </div>

              </td>

            </tr>

          </tbody>

        </table>

      </div>

    </section>

    <!-- Benchmark Settings -->
    <div v-if="benchmarkModalOpen" class="modal-backdrop" @click.self="benchmarkModalOpen = false">
      <div class="benchmark-modal">
        <div class="benchmark-modal-header">
          <div>
            <h3>{{ t.adminStudentSkills.benchmarkModalTitle }}</h3>
            <p>
              {{ t.adminStudentSkills.benchmarkModalSubtitle }}
              <strong class="benchmark-track">({{ loadedTrack === 'staff' ? t.adminStudentSkills.skillTrackStaff : t.adminStudentSkills.skillTrackParticipant }})</strong>
            </p>
          </div>
          <button class="detail-close" type="button" @click="benchmarkModalOpen = false"><X :size="20" /></button>
        </div>

        <div class="benchmark-form">
          <label v-for="(skill, index) in skillKeys" :key="skill.key" class="benchmark-field">
            <span>{{ skillDisplay(skill.label) }}</span>
            <div class="benchmark-input-wrap">
              <input v-model.number="benchmarkDraft[index]" type="number" min="1" max="5" step="0.1" />
              <small>/ 5.0</small>
            </div>
          </label>
        </div>

        <div v-if="benchmarkError" class="benchmark-error">{{ benchmarkError }}</div>
        <div class="benchmark-actions">
          <button class="benchmark-cancel" type="button" @click="benchmarkModalOpen = false">{{ t.adminStudentSkills.cancel }}</button>
          <button class="benchmark-save" type="button" :disabled="benchmarkSaving" @click="saveBenchmarkSettings">
            <Save :size="15" /> {{ benchmarkSaving ? t.adminStudentSkills.savingBenchmark : t.adminStudentSkills.saveBenchmark }}
          </button>
        </div>
      </div>
    </div>

    <!-- =========================
         Individual Student Detail Modal
    ========================== -->
    <div
      v-if="selectedStudent"
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      :aria-label="`${t.adminStudentSkills.studentDetailAriaLabel} ${selectedStudent.name}`"
      @click.self="closeStudentRadar"
    >
      <div class="student-detail-modal">

        <!-- Header -->
        <header class="detail-header">
          <div class="student-identity">
            <div class="student-avatar">
              <img
                v-if="!photoHasError"
                :src="selectedStudentPhoto"
                :alt="selectedStudent.name"
                @error="handlePhotoError"
              />
              <span v-else>{{ selectedInitials }}</span>
            </div>

            <div class="student-identity-text">
              <h3>{{ selectedStudent.name }}</h3>
              <div class="student-meta-row">
                <span class="student-meta-chip">{{ t.adminStudentSkills.idLabel }}: {{ selectedStudent.id }}</span>
                <span class="student-meta-chip">{{ yearLevelLabel(yearLevelGroup(selectedStudent.yearLevel)) }}</span>
                <span class="student-meta-chip">{{ t.adminStudentSkills.major }}: {{ selectedStudent.major || '—' }}</span>
                <span class="student-meta-chip">{{ selectedStudent.periodLabel || selectedStudent.semester }}</span>
                <span class="student-meta-chip">{{ t.adminStudentSkills.joinedPrefix }} {{ selectedStudent.activityCount ?? 0 }} {{ t.adminStudentSkills.activitiesUnit }}</span>
              </div>
            </div>
          </div>

          <button
            class="detail-close"
            type="button"
            :aria-label="t.adminStudentSkills.closeStudentDetails"
            @click="closeStudentRadar"
          >
            <X :size="20" />
          </button>
        </header>

        <div class="detail-content-grid">

          <!-- Left: Radar -->
          <section class="detail-panel radar-detail-panel">
            <div class="detail-section-heading">
              <div>
                <h4>{{ t.adminStudentSkills.skillAnalysis }}</h4>
                <p>{{ t.adminStudentSkills.skillAnalysisSub }}</p>
              </div>

              <div class="detail-legend">
                <span><i class="legend-swatch student"></i> {{ t.adminStudentSkills.student }}</span>
                <span :title="selectedMajorLabel">
                  <i class="legend-swatch major"></i>
                  {{ t.adminStudentSkills.majorAvgShort }} ({{ selectedMajorStudents.length }})
                </span>
                <span><i class="legend-swatch faculty"></i> {{ t.adminStudentSkills.facultyAvgShort }}</span>
              </div>
            </div>

            <div class="detail-radar-wrap">
              <svg class="detail-radar" viewBox="0 0 500 400">
                <!-- Radar scale: center = 0, rings = 1, 2, 3, 4, 5 -->
                <polygon points="250,165 276,180 276,210 250,225 224,210 224,180" class="radar-grid" />
                <polygon points="250,135 302,165 302,225 250,255 198,225 198,165" class="radar-grid" />
                <polygon points="250,105 328,150 328,240 250,285 172,240 172,150" class="radar-grid" />
                <polygon points="250,75 354,135 354,255 250,315 146,255 146,135" class="radar-grid" />
                <polygon points="250,45 380,120 380,270 250,345 120,270 120,120" class="radar-grid" />

                <line x1="250" y1="195" x2="250" y2="45" class="radar-axis" />
                <line x1="250" y1="195" x2="380" y2="120" class="radar-axis" />
                <line x1="250" y1="195" x2="380" y2="270" class="radar-axis" />
                <line x1="250" y1="195" x2="250" y2="345" class="radar-axis" />
                <line x1="250" y1="195" x2="120" y2="270" class="radar-axis" />
                <line x1="250" y1="195" x2="120" y2="120" class="radar-axis" />

                <polygon :points="selectedFacultyRadarPoints" class="student-faculty-area" />
                <polygon :points="selectedMajorRadarPoints" class="student-major-area" />
                <polygon :points="selectedStudentRadarPoints" class="student-profile-area" />

                <text
                  v-for="label in radarLabels"
                  :key="label.key"
                  :x="label.x"
                  :y="label.y"
                  :text-anchor="label.anchor"
                  class="radar-label"
                >
                  <tspan
                    v-for="(line, lineIndex) in label.lines"
                    :key="lineIndex"
                    :x="label.x"
                    :dy="lineIndex === 0 ? label.firstDy : RADAR_LABEL_LINE_HEIGHT"
                  >{{ line }}</tspan>
                </text>
              </svg>
            </div>

            <div class="student-score-grid">
              <div
                v-for="skill in skillKeys"
                :key="skill.key"
                class="student-score-item"
              >
                <div class="score-item-text">
                  <span>{{ skillDisplay(skill.label) }}</span>
                  <small>
                    <i class="legend-swatch major"></i>{{ formatScore(selectedMajorAverages[skill.key]) }}
                    <i class="legend-swatch faculty"></i>{{ formatScore(wholeFacultySkillAverages[skill.key]) }}
                  </small>
                </div>
                <strong>{{ skillValueOf(selectedStudent, skill.key) !== null ? skillValueOf(selectedStudent, skill.key).toFixed(1) : t.adminStudentSkills.notAvailable }}</strong>
              </div>
            </div>
          </section>

          <!-- Right -->
          <aside class="detail-side-column">
            <section class="strongest-skill-card">
              <div class="strongest-label">{{ t.adminStudentSkills.strongestSkill }}</div>
              <h4>{{ selectedStrongestSkill ? skillDisplay(selectedStrongestSkill.label) : '—' }}</h4>
              <p>
                {{ t.adminStudentSkills.studentScore }}:
                <strong>{{ selectedStrongestSkill ? selectedStrongestSkill.score.toFixed(1) : '—' }}</strong>
                / 5.0
              </p>
              <p class="average-caption">
                {{ t.adminStudentSkills.overallAverage }}: {{ selectedStudentAverage !== null ? selectedStudentAverage.toFixed(2) : t.adminStudentSkills.notAvailable }}<template v-if="selectedStudentAverage !== null"> / 5.0</template>
              </p>
            </section>

            <section class="detail-panel skill-gap-panel">
              <div class="gap-heading">
                <h4>{{ t.adminStudentSkills.skillGapAnalysis }}</h4>
                <p>{{ gapBasis === 'MAJOR' ? t.adminStudentSkills.skillGapSubMajor : t.adminStudentSkills.skillGapSub }}</p>
              </div>

              <div class="gap-basis-switch" role="group" :aria-label="t.adminStudentSkills.gapCompareLabel">
                <span>{{ t.adminStudentSkills.gapCompareLabel }}</span>
                <button
                  type="button"
                  :class="{ active: gapBasis === 'MAJOR' }"
                  :aria-pressed="gapBasis === 'MAJOR'"
                  @click="gapBasis = 'MAJOR'"
                >
                  {{ t.adminStudentSkills.gapCompareMajor }}
                </button>
                <button
                  type="button"
                  :class="{ active: gapBasis === 'FACULTY' }"
                  :aria-pressed="gapBasis === 'FACULTY'"
                  @click="gapBasis = 'FACULTY'"
                >
                  {{ t.adminStudentSkills.gapCompareFaculty }}
                </button>
              </div>

              <div v-if="selectedTopGaps.length" class="gap-list">
                <article
                  v-for="gap in selectedTopGaps"
                  :key="gap.key"
                  class="gap-card"
                  :class="{ critical: gap.difference <= -0.5 }"
                >
                  <div class="gap-card-header">
                    <div>
                      <strong>{{ skillDisplay(gap.label) }}</strong>
                      <span>
                        {{ Math.abs(gap.percentDifference).toFixed(0) }}% {{ gapBasis === 'MAJOR' ? t.adminStudentSkills.belowMajorAverage : t.adminStudentSkills.belowFacultyAverage }}
                      </span>
                    </div>
                    <AlertTriangle v-if="gap.difference <= -0.5" :size="16" />
                    <CheckCircle v-else :size="16" />
                  </div>

                  <div class="gap-comparison">
                    <span>{{ t.adminStudentSkills.student }} {{ gap.studentScore.toFixed(1) }}</span>
                    <span>{{ gapBasis === 'MAJOR' ? t.adminStudentSkills.major : t.adminStudentSkills.faculty }} {{ gap.compareScore.toFixed(1) }}</span>
                  </div>

                  <div class="gap-recommendation">
                    <strong>{{ t.adminStudentSkills.recommendation }}</strong>
                    <span>{{ gap.recommendation }}</span>
                  </div>
                </article>
              </div>

              <div v-else class="no-gap-state">
                <CheckCircle :size="22" />
                <strong>{{ t.adminStudentSkills.noSignificantGaps }}</strong>
                <span>{{ gapBasis === 'MAJOR' ? t.adminStudentSkills.noGapSubMajor : t.adminStudentSkills.noGapSub }}</span>
              </div>
            </section>
          </aside>
        </div>
      </div>
    </div>

    <!-- =========================
         Student Activity History Modal
    ========================== -->
    <div
      v-if="activityHistoryStudent"
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      :aria-label="`${t.adminStudentSkills.activityHistoryAriaLabel} ${activityHistoryStudent.name}`"
      @click.self="closeActivityHistory"
    >
      <div class="activity-history-modal">
        <header class="activity-history-header">
          <div>
            <h3>{{ t.adminStudentSkills.activityHistoryTitle }}</h3>
            <p class="activity-history-subtitle">
              {{ activityHistoryStudent.name }} · {{ activityHistoryStudent.id }}
            </p>
          </div>

          <button
            class="detail-close"
            type="button"
            :aria-label="t.adminStudentSkills.closeActivityHistory"
            @click="closeActivityHistory"
          >
            <X :size="20" />
          </button>
        </header>

        <div v-if="activityHistoryLoading" class="activity-history-state">
          {{ t.adminStudentSkills.activityHistoryLoading }}
        </div>

        <div v-else-if="activityHistoryError" class="activity-history-state error">
          <AlertTriangle :size="18" />
          {{ activityHistoryError }}
        </div>

        <div v-else-if="activityHistoryItems.length === 0" class="activity-history-state">
          {{ t.adminStudentSkills.noActivityHistory }}
        </div>

        <div v-else class="activity-history-table-wrapper">
          <table class="activity-history-table">
            <thead>
              <tr>
                <th>{{ t.adminStudentSkills.activityNameColumn }}</th>
                <th>{{ t.adminStudentSkills.activityTypeColumn }}</th>
                <th>{{ t.adminStudentSkills.activityDateColumn }}</th>
                <th>{{ t.adminStudentSkills.activityRoleColumn }}</th>
                <th>{{ t.adminStudentSkills.activityStatusColumn }}</th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="item in activityHistoryItems"
                :key="`${item.source}-${item.id}`"
              >
                <td>{{ item.title }}</td>
                <td>{{ activityTypeLabel(item.source) }}</td>
                <td>{{ activityDateRange(item) }}</td>
                <td>{{ activityRoleLabel(item.role) }}</td>
                <td>
                  <span class="status-pill" :class="item.status">
                    {{ activityStatusLabel(item.status) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

  </div>

</template>


<style scoped>

/* =========================
   Page
========================= */

.student-skills-page {
  min-height: 100vh;

  padding: 28px 32px;

  background: #f7f8fc;
}


/* =========================
   Header
========================= */

.page-header {
  margin-bottom: 22px;
}

.branch-filter-row {
  max-width: 260px;
  margin-bottom: 22px;
}

.page-header h1 {
  margin: 0;

  font-size: 25px;
  font-weight: 800;

  color: #1d3268;
}

.page-header p {
  margin: 6px 0 0;

  font-size: 16px;

  color: #8da0bd;
}


/* =========================
   Summary
========================= */

/* =========================
   Class year / Major filter
========================= */

.cohort-bar {
  margin-bottom: 18px;
  padding: 12px 16px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 16px;
  border: 1px solid #e0e7f0;
  border-radius: 12px;
  background: #fff;
}

.cohort-bar-title {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #1d3268;
  font-size: 13px;
  font-weight: 800;
}

.cohort-field {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #66758c;
  font-size: 12px;
  font-weight: 700;
}

.cohort-field select {
  min-width: 150px;
  height: 32px;
  padding: 0 10px;
  border: 1px solid #d4dbe7;
  border-radius: 7px;
  outline: none;
  background: #fff;
  color: #1d3268;
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.cohort-field select:focus {
  border-color: #76aaf1;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

.cohort-clear {
  height: 30px;
  padding: 0 10px;
  border: 0;
  border-radius: 7px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: #f1f4f9;
  color: #55708f;
  font: inherit;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.cohort-clear:hover {
  background: #e6ecf5;
}

.cohort-hint {
  margin-left: auto;
  color: #94a1b1;
  font-size: 10px;
}

.skill-track-switch {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #66758c;
  font-size: 12px;
  font-weight: 700;
}

.skill-track-switch button {
  height: 32px;
  padding: 0 12px;
  border: 1px solid #d4dbe7;
  border-radius: 999px;
  background: #fff;
  color: #47566e;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.skill-track-switch button:not(:disabled):hover {
  background: #f3f6ff;
}

.skill-track-switch button.active {
  border-color: #3264ed;
  background: #eef3ff;
  color: #1d3f9e;
}

.skill-track-switch button:disabled {
  opacity: 0.55;
  cursor: wait;
}

.skill-track-hint {
  width: 100%;
  margin: 0;
  color: #6f5bd3;
  font-size: 11px;
  font-weight: 600;
}

.track-chip {
  background: #efeaff;
  color: #6744c4;
}

.benchmark-track {
  color: #315de6;
}

.radar-title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.cohort-chip {
  padding: 4px 9px;
  border-radius: 999px;
  background: #eaf2ff;
  color: #1264d8;
  font-size: 11px;
  font-weight: 700;
}

.summary-grid {
  display: grid;

  grid-template-columns:
    repeat(2, minmax(0, 1fr));

  gap: 18px;
}


.summary-card {
  min-height: 105px;

  padding: 18px;

  display: flex;

  align-items: center;

  gap: 16px;

  background: white;

  border: 1px solid #edf0f5;

  border-radius: 14px;

  box-shadow:
    0 2px 8px rgba(30, 60, 100, 0.04);
}


.summary-icon {
  width: 34px;
  height: 34px;

  flex-shrink: 0;

  display: flex;

  align-items: center;
  justify-content: center;

  border-radius: 9px;
}


.summary-icon.blue {
  color: #315de6;

  background: #eaf0ff;
}


.summary-icon.gray {
  color: #666;

  background: #f1f1f1;
}


.summary-info {
  display: flex;

  flex-direction: column;
}


.summary-label {
  font-size: 11px;

  font-weight: 700;

  letter-spacing: 0.5px;

  color: #8998ad;
}


.summary-value {
  margin-top: 3px;

  font-size: 22px;

  color: #18356f;
}


.summary-value small {
  font-size: 13px;

  font-weight: 600;
}


.summary-sub {
  margin-top: 3px;

  font-size: 11px;

  color: #8998ad;
}


/* =========================
   Main Layout
========================= */

.skill-layout {
  display: grid;

  grid-template-columns:
    minmax(0, 1.55fr)
    minmax(250px, 1fr);

  gap: 14px;

  margin-top: 14px;
}


/* =========================
   Card
========================= */

.card {
  background: white;

  border: 1px solid #dfe4ed;

  border-radius: 8px;

  box-shadow:
    0 1px 4px rgba(30, 60, 100, 0.03);
}


/* =========================
   Card Header
========================= */

.card-header {
  padding: 10px 14px;

  display: flex;

  align-items: center;

  justify-content: space-between;
}


.card-header h2 {
  margin: 0;

  font-size: 16px;

  font-weight: 800;

  color: #1d3268;
}


.semester-select {
  padding: 4px 8px;

  display: flex;

  align-items: center;

  gap: 5px;

  border: 1px solid #d4dbe7;

  border-radius: 4px;

  background: white;

  color: #4f5f76;

  font-size: 11px;

  cursor: pointer;
}

.semester-dropdown {
  position: relative;
}


.semester-menu {
  position: absolute;

  top: calc(100% + 5px);

  right: 0;

  width: 150px;

  padding: 5px;

  background: white;

  border: 1px solid #dfe4ed;

  border-radius: 6px;

  box-shadow:
    0 5px 15px rgba(30, 60, 100, 0.12);

  z-index: 20;
}


.semester-option {
  width: 100%;

  padding: 7px 8px;

  display: flex;

  align-items: center;

  justify-content: space-between;

  border: none;

  border-radius: 4px;

  background: transparent;

  color: #52627a;

  font-size: 11px;

  text-align: left;

  cursor: pointer;
}


.semester-option:hover {
  background: #f3f6ff;
}


.semester-option.selected {
  color: #3264ed;

  background: #f0f4ff;

  font-weight: 700;
}


/* =========================
   Radar
========================= */

/* =========================
   Radar view switch + small multiples
========================= */

.radar-view-switch {
  padding: 0 14px 10px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.radar-view-label {
  margin-right: 2px;
  color: #66758c;
  font-size: 11px;
  font-weight: 700;
}

.radar-view-option {
  padding: 5px 10px;
  border: 1px solid #d4dbe7;
  border-radius: 999px;
  background: #fff;
  color: #47566e;
  font: inherit;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.radar-view-option:hover {
  background: #f3f6ff;
}

.radar-view-option.active {
  border-color: #3264ed;
  background: #eef3ff;
  color: #1d3f9e;
}

/* กลุ่มบน radar หลัก: เส้น 2px + พื้นจาง ๆ ให้เห็นรูปที่ซ้อนกัน */
.group-area {
  fill-opacity: 0.08;
  stroke-width: 2;
}

.group-point-hit {
  fill: transparent;
  cursor: default;
}

.group-point {
  stroke: #fff;
  stroke-width: 2;
  cursor: default;
}

/* ไม่ให้ตารางตัวเลข (min-width 680px) ดันการ์ดให้กว้างเกินคอลัมน์ในจอแคบ */
.radar-card {
  min-width: 0;
}

.radar-group-legend {
  padding: 0 14px 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.radar-group-hint {
  margin: 0;
  color: #7f8ca2;
  font-size: 11px;
  text-align: center;
}

.radar-group-chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
}

.radar-group-chip {
  padding: 5px 10px;
  border: 1px solid #d4dbe7;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #fff;
  color: #6b7a90;
  font: inherit;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.radar-group-chip small {
  color: #94a1b1;
  font-size: 10px;
  font-weight: 600;
}

.radar-group-chip:not(:disabled):hover {
  background: #f3f6ff;
}

.radar-group-chip.selected {
  border-color: #b9c8e6;
  background: #f5f8ff;
  color: #1d3268;
}

.radar-group-chip:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.radar-group-swatch {
  width: 10px;
  height: 10px;
  flex-shrink: 0;
  border: 1.5px solid #c5ccd8;
  border-radius: 50%;
  display: inline-block;
}

.radar-group-chip.selected .radar-group-swatch,
.group-name .radar-group-swatch {
  border: 0;
}

.group-name .radar-group-swatch {
  margin-right: 6px;
  vertical-align: -1px;
}
.radar-table-view {
  align-self: stretch;
  margin: 4px 0 0;
  border: 1px solid #e3e8f0;
  border-radius: 8px;
}

.radar-table-view summary {
  padding: 8px 12px;
  color: #315de6;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.radar-table-scroll {
  overflow-x: auto;
}

/* ไม่ใช้ table-layout: fixed ของตารางหลัก ไม่งั้นทุก column กว้างเท่ากันจนชื่อกลุ่มล้นทับตัวเลข */
.radar-group-table {
  min-width: 680px;
  table-layout: auto;
}

.radar-group-table th,
.radar-group-table td {
  padding: 8px 10px;
  white-space: nowrap;
}

.radar-group-table .group-name {
  min-width: 160px;
  color: #1d3268;
  font-weight: 700;
  white-space: normal;
  overflow-wrap: anywhere;
}

.radar-container {
  height: 350px;

  display: flex;

  align-items: center;

  justify-content: center;
}


.radar {
  width: 100%;

  max-width: 400px;

  height: 330px;
}


.radar-grid {
  fill: none;

  stroke: #cdd7e8;

  stroke-width: 1;

  stroke-dasharray: 4 4;
}


.radar-axis {
  stroke: #cdd7e8;

  stroke-width: 1;
}


.radar-area {
  fill: #dbe8ff;

  fill-opacity: 0.55;

  stroke: #3264ed;

  stroke-width: 2;
}


.radar-point {
  fill: #3264ed;
}


.radar-label {
  font-size: 11px;

  font-weight: 700;

  fill: #182c58;
}


/* =========================
   Legend
========================= */

.radar-legend {
  padding: 0 0 16px;

  display: flex;

  justify-content: center;

  gap: 18px;

  font-size: 11px;

  color: #7f8ca2;
}


.legend-button {
  border: none;

  background: transparent;

  display: flex;

  align-items: center;

  gap: 5px;

  padding: 0;

  font-size: 11px;

  color: #7f8ca2;

  cursor: pointer;
}

.legend-button:hover {
  color: #3264ed;
}

.legend-button.inactive {
  color: #a6afbd;
}


.legend-dot {
  width: 8px;
  height: 8px;

  border-radius: 50%;
}


.legend-dot.actual {
  background: #3264ed;
}


.legend-dot.benchmark {
  background: #22a06b;
}


.legend-dot.actual.inactive,
.legend-dot.benchmark.inactive {
  background: #c5ccd8;
}


/* =========================
   Side Information
========================= */

.side-information {
  display: flex;

  flex-direction: column;

  gap: 14px;
}


.info-card {
  padding: 18px;

  flex: 1;
}


.info-title {
  display: flex;

  align-items: center;

  gap: 8px;

  font-size: 10px;

  font-weight: 800;

  color: #17356e;
}


.top-area .info-title svg {
  color: #00a88f;
}


.growth-area .info-title svg {
  color: #f2a400;
}


.info-card p {
  margin: 14px 0;

  font-size: 11px;

  line-height: 1.6;

  color: #65738a;
}


.info-item {
  margin-top: 8px;

  padding: 7px 8px;

  display: flex;

  align-items: center;

  gap: 6px;

  background: #f7f8fc;

  border-radius: 4px;

  font-size: 11px;

  color: #53627a;
}


.info-item svg {
  color: #00a88f;
}


.action-plan {
  margin-top: 14px;

  padding: 10px;

  display: flex;

  flex-direction: column;

  gap: 5px;

  background: #fff9e9;

  border: 1px solid #f1d77e;

  border-radius: 5px;

  font-size: 11px;

  color: #a86400;
}


/* =========================
   Students Table
========================= */

.students-card {
  margin-top: 14px;
  overflow: visible;
}


.students-header {
  padding: 10px 14px;

  display: flex;

  align-items: center;

  justify-content: space-between;
}


.students-header h2 {
  margin: 0;

  font-size: 16px;

  color: #17356e;
}


.table-tools {
  display: flex;

  gap: 8px;
}


.search-box {
  width: 200px;
  height: 32px;

  padding: 0 10px;

  display: flex;
  align-items: center;
  gap: 7px;

  border: 1px solid #d7deea;
  border-radius: 6px;

  background: #ffffff;

  color: #8190a7;
}


.search-box input {
  width: 100%;
  height: 100%;

  border: none;
  outline: none;

  background: #ffffff !important;
  color: #4e5e75;

  font-size: 12px;
  font-family: inherit;
}

.search-box input::placeholder {
  color: #9aa8bb;
  opacity: 1;
}


.filter-button {
  width: 29px;
  height: 27px;

  display: flex;

  align-items: center;
  justify-content: center;

  border: 1px solid #d7deea;

  border-radius: 4px;

  background: white;

  color: #596980;

  cursor: pointer;
}


/* =========================
   Table
========================= */

.table-wrapper {
  max-height: 280px;

  overflow-y: scroll;
  overflow-x: auto;
}

thead {
  background: #eef1fb;

  position: sticky;

  top: 0;

  z-index: 2;
}

table {
  width: 100%;

  border-collapse: collapse;

  table-layout: fixed;
}

/* 8 columns: เลื่อนแนวนอนได้เมื่อจอแคบ แทนที่ข้อความจะทับกัน */
.table-wrapper table {
  min-width: 980px;
}


th {
  padding: 9px 16px;

  text-align: left;

  font-size: 11px;

  font-weight: 800;

  color: #4e5870;
}


td {
  padding: 10px 16px;

  border-top: 1px solid #e4e8ef;

  font-size: 11px;

  color: #47566e;
}


.empty-row {
  height: 80px;

  text-align: center;

  color: #a1adbf;
}


.radar-button {
  padding: 5px 12px;

  border: 1px solid #cdd8ed;

  border-radius: 4px;

  background: white;

  color: #3264ed;

  font-size: 11px;

  cursor: pointer;
}


.radar-button:hover {
  background: #f3f6ff;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.activities-button {
  padding: 5px 12px;

  border: 1px solid #cdeed8;

  border-radius: 4px;

  background: white;

  color: #17945a;

  font-size: 11px;

  cursor: pointer;
}

.activities-button:hover {
  background: #f0fbf5;
}

/* =========================
   Activity History Modal
========================= */

.activity-history-modal {
  width: min(760px, 96vw);
  max-height: 88vh;
  overflow: auto;
  background: #fff;
  border: 1px solid #dce4f0;
  border-radius: 14px;
  box-shadow: 0 24px 60px rgba(24, 45, 80, 0.24);
}

.activity-history-header {
  position: sticky;
  top: 0;
  z-index: 4;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 18px 20px;
  background: rgba(255, 255, 255, 0.96);
  border-bottom: 1px solid #e5eaf2;
  backdrop-filter: blur(8px);
}

.activity-history-header h3 {
  margin: 0;
  color: #1d3268;
  font-size: 18px;
}

.activity-history-subtitle {
  margin: 4px 0 0;
  color: #8da0bd;
  font-size: 13px;
}

.activity-history-state {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 40px 20px;
  justify-content: center;
  color: #7c8aa0;
  font-size: 14px;
}

.activity-history-state.error {
  color: #c8402f;
}

.activity-history-table-wrapper {
  padding: 12px 20px 20px;
  overflow-x: auto;
}

/* กำหนด table-layout/width เอง (ไม่พึ่ง selector `table` ตัวรวมของ
   ตาราง student list ด้านบน) เพื่อคุมความกว้างแต่ละคอลัมน์ให้แน่นอน
   และป้องกันข้อความ column DATE/ROLE ทับกันเหมือนตอน nowrap+fixed */
.activity-history-table {
  width: 100%;
  min-width: 640px;
  border-collapse: collapse;
  table-layout: fixed;
}

.activity-history-table th,
.activity-history-table td {
  white-space: normal;
  overflow-wrap: break-word;
  word-break: break-word;
}

.activity-history-table th {
  text-align: left;
  padding: 10px 12px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: #8da0bd;
  border-bottom: 1px solid #e5eaf2;
}

.activity-history-table td {
  padding: 12px;
  font-size: 13px;
  color: #33415c;
  border-bottom: 1px solid #eef1f7;
  vertical-align: top;
}

.activity-history-table th:nth-child(1),
.activity-history-table td:nth-child(1) {
  width: 30%;
}

.activity-history-table th:nth-child(2),
.activity-history-table td:nth-child(2) {
  width: 18%;
}

.activity-history-table th:nth-child(3),
.activity-history-table td:nth-child(3) {
  width: 20%;
}

.activity-history-table th:nth-child(4),
.activity-history-table td:nth-child(4) {
  width: 14%;
}

.activity-history-table th:nth-child(5),
.activity-history-table td:nth-child(5) {
  width: 18%;
}

.status-pill {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.status-pill.approved {
  background: #e3f9ee;
  color: #17945a;
}

.status-pill.pending {
  background: #fff4e0;
  color: #b4740a;
}

.status-pill.rejected {
  background: #fde9e8;
  color: #c8402f;
}


/* =========================
   Responsive
========================= */

@media (max-width: 900px) {

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .skill-layout {
    grid-template-columns: 1fr;
  }

}


@media (max-width: 600px) {

  .student-skills-page {
    padding: 20px 15px;
  }

  .cohort-field {
    width: 100%;
    justify-content: space-between;
  }

  .cohort-field select {
    flex: 1;
    min-width: 0;
  }

  .cohort-hint {
    margin-left: 0;
  }

  .students-header {
    align-items: flex-start;

    flex-direction: column;

    gap: 12px;
  }

  .search-box {
    width: 200px;
  }

}

.legend-item {
  display: flex;

  align-items: center;

  gap: 5px;

  border: none;

  background: transparent;

  font-size: 11px;

  color: #7f8ca2;

  cursor: pointer;
}

.legend-item:hover {
  color: #3264ed;
}

.legend-item.disabled {
  opacity: 0.35;
}

.filter-wrapper {
  position: relative;
}


.filter-panel {
  position: absolute;

  top: calc(100% + 6px);

  right: 0;

  width: 190px;

  padding: 12px;

  background: white;

  border: 1px solid #dfe4ed;

  border-radius: 6px;

  box-shadow:
    0 5px 15px rgba(30, 60, 100, 0.12);

  z-index: 20;
}


.filter-title {
  margin-bottom: 10px;

  font-size: 10px;

  font-weight: 800;

  color: #17356e;
}


.filter-panel label {
  display: block;

  margin: 8px 0 4px;

  font-size: 11px;

  color: #65738a;
}


.filter-panel select {
  width: 100%;

  height: 27px;

  padding: 0 6px;

  border: 1px solid #d7deea;

  border-radius: 4px;

  background: white;

  color: #53627a;

  font-size: 11px;

  outline: none;
}



/* =========================
   Dynamic Radar / Student Detail Modal
========================= */
.benchmark-area {
  fill: rgba(34, 160, 107, 0.10);
  stroke: #22a06b;
  stroke-width: 2;
  stroke-dasharray: 5 4;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(18, 31, 56, 0.48);
  backdrop-filter: blur(2px);
}

.student-detail-modal {
  width: min(1050px, 96vw);
  max-height: 92vh;
  overflow: auto;
  background: #fff;
  border: 1px solid #dce4f0;
  border-radius: 14px;
  box-shadow: 0 24px 60px rgba(24, 45, 80, 0.24);
}

.detail-header {
  position: sticky;
  top: 0;
  z-index: 4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 16px 18px;
  background: rgba(255, 255, 255, 0.96);
  border-bottom: 1px solid #e5eaf2;
  backdrop-filter: blur(8px);
}

.student-identity {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.student-avatar {
  width: 50px;
  height: 50px;
  flex: 0 0 50px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #d8e4ff;
  border-radius: 10px;
  background: #edf3ff;
  color: #2f5fd0;
  font-size: 16px;
  font-weight: 800;
}

.student-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.student-identity-text {
  min-width: 0;
}

.student-identity-text h3 {
  margin: 0 0 6px;
  font-size: 21px;
  line-height: 1.2;
  color: #142f64;
}

.student-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.student-meta-chip {
  padding: 4px 7px;
  border-radius: 4px;
  background: #eef4ff;
  color: #315db9;
  font-size: 13px;
  font-weight: 700;
}

.detail-close {
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #d7deea;
  border-radius: 7px;
  background: #fff;
  color: #596980;
  cursor: pointer;
}

.detail-close:hover {
  background: #f4f7fc;
  color: #244fa8;
}

.detail-content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(300px, 1fr);
  gap: 16px;
  padding: 16px;
}

.detail-panel {
  background: #fff;
  border: 1px solid #dfe5ef;
  border-radius: 10px;
}

.radar-detail-panel {
  min-width: 0;
  padding: 16px;
}

.detail-section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.detail-section-heading h4,
.gap-heading h4 {
  margin: 0;
  font-size: 18px;
  color: #17356e;
}

.detail-section-heading p,
.gap-heading p {
  margin: 5px 0 0;
  font-size: 13px;
  line-height: 1.5;
  color: #8794a8;
}

.detail-legend {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 700;
  color: #455a78;
}

.detail-legend span {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-swatch {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.legend-swatch.student {
  background: #37c978;
}

.legend-swatch.faculty {
  background: #2367d1;
}

/* ค่าเฉลี่ยสาขา: ส้ม ผ่านการตรวจสีทุกคู่กับเขียว (นักศึกษา) และน้ำเงิน (คณะ) */
.legend-swatch.major {
  background: #eb6834;
}

.detail-radar-wrap {
  min-height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 0;
}

.detail-radar {
  width: 100%;
  max-width: 520px;
  height: 350px;
}

.student-profile-area {
  fill: rgba(55, 201, 120, 0.25);
  stroke: #37c978;
  stroke-width: 2.3;
}

.student-faculty-area {
  fill: rgba(35, 103, 209, 0.10);
  stroke: #2367d1;
  stroke-width: 2;
}

.student-major-area {
  fill: rgba(235, 104, 52, 0.08);
  stroke: #eb6834;
  stroke-width: 2;
}

.score-item-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.score-item-text small {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #7f8ca2;
  font-size: 11px;
}

.score-item-text small .legend-swatch {
  width: 7px;
  height: 7px;
  margin-left: 4px;
}

.score-item-text small .legend-swatch:first-child {
  margin-left: 0;
}

.gap-basis-switch {
  margin: 10px 0 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #66758c;
  font-size: 12px;
  font-weight: 700;
}

.gap-basis-switch button {
  padding: 4px 10px;
  border: 1px solid #d4dbe7;
  border-radius: 999px;
  background: #fff;
  color: #47566e;
  font: inherit;
  font-size: 11px;
  cursor: pointer;
}

.gap-basis-switch button.active {
  border-color: #3264ed;
  background: #eef3ff;
  color: #1d3f9e;
}

.student-score-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.student-score-item {
  padding: 9px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border: 1px solid #e4e8ef;
  border-radius: 6px;
  background: #fbfcff;
  font-size: 13px;
  color: #53627a;
}

.student-score-item strong {
  color: #17356e;
}

.detail-side-column {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.strongest-skill-card {
  padding: 17px;
  border: 1px solid #8edfac;
  border-radius: 10px;
  background: #eafff1;
}

.strongest-label {
  margin-bottom: 5px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: .45px;
  color: #278451;
}

.strongest-skill-card h4 {
  margin: 0;
  font-size: 20px;
  color: #17356e;
}

.strongest-skill-card p {
  margin: 8px 0 0;
  font-size: 13px;
  color: #587066;
}

.strongest-skill-card .average-caption {
  color: #73847b;
}

.skill-gap-panel {
  padding: 16px;
}

.gap-heading {
  margin-bottom: 12px;
}

.gap-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.gap-card {
  padding: 11px;
  border: 1px solid #d9e2f3;
  border-radius: 7px;
  background: #f4f7ff;
}

.gap-card.critical {
  border-color: #efb9b9;
  background: #fff6f6;
}

.gap-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  color: #314360;
}

.gap-card-header > div {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.gap-card-header strong {
  font-size: 13px;
  color: #20385f;
}

.gap-card-header span {
  font-size: 13px;
  color: #c04b4b;
}

.gap-comparison {
  margin-top: 7px;
  display: flex;
  gap: 8px;
  font-size: 13px;
  color: #607089;
}

.gap-comparison span {
  padding: 3px 6px;
  border-radius: 4px;
  background: rgba(255,255,255,.8);
}

.gap-recommendation {
  margin-top: 9px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  border: 1px solid rgba(214, 222, 236, .9);
  border-radius: 5px;
  background: rgba(255,255,255,.82);
  font-size: 13px;
  line-height: 1.45;
  color: #647086;
}

.gap-recommendation strong {
  color: #41516d;
}

.no-gap-state {
  min-height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 18px;
  text-align: center;
  color: #26a567;
}

.no-gap-state strong {
  font-size: 14px;
  color: #24563e;
}

.no-gap-state span {
  max-width: 260px;
  font-size: 13px;
  line-height: 1.5;
  color: #78879b;
}

@media (max-width: 900px) {
  .student-detail-modal {
    width: min(760px, 96vw);
  }

  .detail-content-grid {
    grid-template-columns: 1fr;
  }

  .detail-side-column {
    display: grid;
    grid-template-columns: 1fr 1.25fr;
  }
}

@media (max-width: 650px) {
  .modal-backdrop {
    align-items: flex-start;
    padding: 10px;
  }

  .student-detail-modal {
    width: 100%;
    max-height: calc(100vh - 20px);
    border-radius: 10px;
  }

  .detail-header {
    align-items: flex-start;
    padding: 12px;
  }

  .student-avatar {
    width: 44px;
    height: 44px;
    flex-basis: 44px;
  }

  .student-identity-text h3 {
    font-size: 15px;
  }

  .detail-content-grid {
    padding: 10px;
  }

  .detail-section-heading {
    flex-direction: column;
  }

  .detail-legend {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .detail-radar-wrap {
    min-height: 300px;
  }

  .detail-radar {
    height: 300px;
  }

  .student-score-grid {
    grid-template-columns: 1fr 1fr;
  }

  .detail-side-column {
    display: flex;
  }
}



.skills-api-error {
  margin-bottom: 14px;
  padding: 10px 12px;
  border: 1px solid #fecaca;
  border-radius: 9px;
  background: #fff7f7;
  color: #b42318;
  font-size: 12px;
}
.report-controls { display:flex; align-items:center; gap:8px; flex-wrap:wrap; justify-content:flex-end; }
.period-menu { width: 205px; }
.benchmark-settings-button { padding:5px 9px; display:flex; align-items:center; gap:5px; border:1px solid #d4dbe7; border-radius:5px; background:#fff; color:#315de6; font-size:11px; font-weight:700; cursor:pointer; }
.benchmark-settings-button:hover { background:#f3f6ff; }
.benchmark-settings-button:disabled { opacity:.55; cursor:wait; }
.benchmark-modal { width:min(620px, 94vw); max-height:90vh; overflow:auto; background:#fff; border-radius:14px; box-shadow:0 20px 60px rgba(20,35,70,.2); }
.benchmark-modal-header { padding:18px 20px; display:flex; justify-content:space-between; gap:16px; border-bottom:1px solid #edf0f5; }
.benchmark-modal-header h3 { margin:0; color:#1d3268; font-size:18px; }
.benchmark-modal-header p { margin:5px 0 0; color:#7f8ca2; font-size:12px; }
.benchmark-form { padding:18px 20px; display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.benchmark-field { padding:10px 12px; border:1px solid #e3e8f0; border-radius:8px; display:flex; align-items:center; justify-content:space-between; gap:12px; color:#314360; font-size:12px; }
.benchmark-input-wrap { display:flex; align-items:center; gap:5px; flex-shrink:0; }
.benchmark-input-wrap input {
  width:68px;
  padding:6px 7px;
  border:1px solid #cfd7e5;
  border-radius:5px;
  background:#ffffff;
  color:#111827;
  font-weight:700;
  color-scheme:light;
}
.benchmark-input-wrap input:focus {
  background:#ffffff;
  color:#111827;
  border-color:#315de6;
  outline:none;
  box-shadow:0 0 0 2px rgba(49,93,230,.12);
}
.benchmark-input-wrap small { color:#8998ad; }
.benchmark-error { margin:0 20px 12px; padding:8px 10px; border-radius:6px; background:#fff2f2; color:#b42318; font-size:12px; }
.benchmark-actions { padding:0 20px 18px; display:flex; justify-content:flex-end; gap:8px; }
.benchmark-cancel, .benchmark-save { padding:8px 12px; border-radius:6px; font-size:12px; cursor:pointer; }
.benchmark-cancel { border:1px solid #d4dbe7; background:#fff; color:#52627a; }
.benchmark-save { border:none; background:#315de6; color:#fff; display:flex; align-items:center; gap:6px; font-weight:700; }
.benchmark-save:disabled { opacity:.6; cursor:not-allowed; }
@media (max-width:650px) { .benchmark-form { grid-template-columns:1fr; } .report-controls { justify-content:flex-start; } }

</style>