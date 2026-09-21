<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

import {
  Search,
  SlidersHorizontal,
  ChevronDown,
  CheckCircle,
  AlertTriangle,
  Check,
  X,
  Settings,
  Save
} from 'lucide-vue-next'

import { useLanguage } from '../../composables/useLanguage'

const { t } = useLanguage()
const API_BASE = 'http://localhost:8000'

/* =========================
   Skill definitions
   ดึงคะแนนจริงจาก participant skill ของกิจกรรม
========================= */
const skillKeys = [
  { key: 'arts_culture_traditions', label: 'Arts, Culture, and Traditions' },
  { key: 'volunteerism', label: 'Volunteerism' },
  { key: 'academics', label: 'Academics' },
  { key: 'internationalization', label: 'Internationalization' },
  { key: 'health_promotion', label: 'Health Promotion' },
  { key: 'nature_environmental_conservation', label: 'Nature & Environmental Conservation' }
]

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
    'Nature & Environmental Conservation': 'skillNatureEnvironmentalConservation'
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

const wrapRadarLabel = (label) => {
  const lines = []

  for (const word of String(label).split(/\s+/)) {
    const last = lines[lines.length - 1]

    if (last && `${last} ${word}`.length <= RADAR_LABEL_MAX_CHARS) {
      lines[lines.length - 1] = `${last} ${word}`
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

/* =========================
   Reporting period: Year + optional Semester
========================= */
const selectedYear = ref(null)
const selectedPeriod = ref('ALL')
const yearOpen = ref(false)
const periodOpen = ref(false)

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

const skillOptions = [
  'All Skills',
  ...skillKeys.map((skill) => skill.label)
]

const scoreOptions = [
  'All Scores',
  '4.0 - 5.0',
  '3.0 - 3.9',
  'Below 3.0'
]

/* =========================
   Fetch real data
========================= */
const loadStudentSkills = async () => {
  loading.value = true
  error.value = ''

  try {
    const params = new URLSearchParams()
    if (selectedYear.value) params.set('year', selectedYear.value)
    params.set('semester', selectedPeriod.value)

    const response = await fetch(`${API_BASE}/api/admin/student-skills?${params.toString()}`)
    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || t.value.adminStudentSkills.loadErrorFallback)
    }

    students.value = Array.isArray(data.students) ? data.students : []
    availableYears.value = Array.isArray(data.availableYears) ? data.availableYears : []
    totalFaculty.value = Number(data.totalFaculty || 0)

    if (!selectedYear.value || !availableYears.value.includes(Number(selectedYear.value))) {
      selectedYear.value = Number(data.defaultYear || data.selectedYear || availableYears.value[0])
    }

    selectedPeriod.value = data.selectedSemester || selectedPeriod.value

    if (Array.isArray(data.benchmarkScores) && data.benchmarkScores.length === 6) {
      benchmarkScores.value = data.benchmarkScores.map(score => Number(score) || 4)
    }
  } catch (err) {
    console.error('Student Skills API Error:', err)
    error.value = err.message || t.value.adminStudentSkills.loadErrorFallback
    students.value = []
  } finally {
    loading.value = false
  }
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
const semesterStudents = computed(() => students.value)

const studentsEvaluated = computed(() => semesterStudents.value.length)

const facultyPercentage = computed(() => {
  if (totalFaculty.value === 0) return '0.0'
  return ((studentsEvaluated.value / totalFaculty.value) * 100).toFixed(1)
})

const averageSkillScore = computed(() => {
  const studentAverages = semesterStudents.value
    .map(student => averageOfSkills(student))
    .filter(value => value !== null)

  if (studentAverages.length === 0) return null
  return (studentAverages.reduce((sum, value) => sum + value, 0) / studentAverages.length).toFixed(2)
})

const facultySkillAverages = computed(() => {
  const result = {}
  skillKeys.forEach(skill => {
    const values = semesterStudents.value
      .map(student => skillValueOf(student, skill.key))
      .filter(value => value !== null)

    result[skill.key] = values.length
      ? values.reduce((sum, value) => sum + value, 0) / values.length
      : null
  })
  return result
})

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

// Benchmark เริ่มต้น 4.0 / 5 ทุก skill
const benchmarkScores = ref([4, 4, 4, 4, 4, 4])
const benchmarkRadarPoints = computed(() => buildRadarPoints(benchmarkScores.value))

const benchmarkModalOpen = ref(false)
const benchmarkDraft = ref([4, 4, 4, 4, 4, 4])
const benchmarkSaving = ref(false)
const benchmarkError = ref('')

const openBenchmarkSettings = () => {
  benchmarkDraft.value = [...benchmarkScores.value]
  benchmarkError.value = ''
  benchmarkModalOpen.value = true
}

const saveBenchmarkSettings = async () => {
  const values = benchmarkDraft.value.map(value => Number(value))
  if (values.some(value => !Number.isFinite(value) || value < 1 || value > 5)) {
    benchmarkError.value = t.value.adminStudentSkills.benchmarkRangeError
    return
  }

  benchmarkSaving.value = true
  benchmarkError.value = ''
  try {
    const scores = Object.fromEntries(skillKeys.map((skill, index) => [skill.key, values[index]]))
    const response = await fetch(`${API_BASE}/api/admin/student-skills/benchmark`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scores })
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || t.value.adminStudentSkills.saveBenchmarkErrorFallback)

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
    nature_environmental_conservation: t.value.adminStudentSkills.growthPlanNatureEnvironmentalConservation
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
    skillKeys.map(skill => facultySkillAverages.value[skill.key] ?? 0)
  )
)

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
  nature_environmental_conservation: t.value.adminStudentSkills.recommendationNatureEnvironmentalConservation
}))

const selectedSkillGaps = computed(() => {
  if (!selectedStudent.value) return []

  return skillKeys
    .map(skill => {
      const studentScore = skillValueOf(selectedStudent.value, skill.key)
      const facultyScore = Number(facultySkillAverages.value[skill.key] ?? 0)

      // ไม่มีข้อมูลของนักศึกษาคนนี้ = ไม่เอาไปสรุปว่าเป็น skill gap
      if (studentScore === null || facultyScore <= 0) return null

      const difference = studentScore - facultyScore
      const percentDifference = (difference / facultyScore) * 100

      return {
        ...skill,
        studentScore,
        facultyScore,
        difference,
        percentDifference,
        recommendation: recommendationBySkill.value[skill.key]
      }
    })
    .filter(skill => skill && skill.difference < -0.05)
    .sort((a, b) => a.difference - b.difference)
})

// แสดง Skill Gap ที่ต่ำกว่าค่าเฉลี่ยคณะทั้งหมด
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

const handleEscape = (event) => {
  if (event.key === 'Escape') {
    if (selectedStudent.value) closeStudentRadar()
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

    <div v-if="error" class="skills-api-error">
      {{ error }}
    </div>


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
            {{ facultyPercentage ?? '—' }}% {{ t.adminStudentSkills.ofTotalFaculty }}
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

          <div>
            <h2>{{ t.adminStudentSkills.facultyRadar }}</h2>
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

            <button class="benchmark-settings-button" type="button" @click="openBenchmarkSettings">
              <Settings :size="14" /> {{ t.adminStudentSkills.benchmarkButton }}
            </button>
          </div>

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

               <!-- Outer Hexagon -->
               <polygon
               points="250,45 380,120 380,270 250,345 120,270 120,120"
               class="radar-grid"
               />

               <!-- Middle Hexagon -->
               <polygon
               points="250,95 337,145 337,245 250,295 163,245 163,145"
               class="radar-grid"
               />

               <!-- Inner Hexagon -->
               <polygon
               points="250,145 293,170 293,220 250,245 207,220 207,170"
               class="radar-grid"
               />


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
               v-if="showActual"
               :points="actualRadarPoints"
               class="radar-area actual-area"
               />


               <!-- =========================
                    {{ t.adminStudentSkills.benchmarkLevel }}
                    ยังไม่มีข้อมูล
               ========================== -->

               <polygon
               v-if="showBenchmark"
               :points="benchmarkRadarPoints"
               class="benchmark-area"
               />


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

        <div class="radar-legend">

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
            {{ t.adminStudentSkills.facultyAverage }}: {{ topArea ? topArea.score.toFixed(2) : t.adminStudentSkills.notAvailable }}<template v-if="topArea"> / 5.0</template>
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
                colspan="6"
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
                {{ student.primarySkill ? skillDisplay(student.primarySkill) : t.adminStudentSkills.notAvailable }}
              </td>

              <td>
                {{ student.score !== null ? student.score.toFixed(2) : t.adminStudentSkills.notAvailable }}
              </td>

              <td>
                <strong>{{ student.activityCount ?? 0 }}</strong> {{ t.adminStudentSkills.activitiesUnit }}
              </td>

              <td>

                <button
                  class="radar-button"
                  @click="openStudentRadar(student)"
                >
                  {{ t.adminStudentSkills.viewRadar }}
                </button>

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
            <p>{{ t.adminStudentSkills.benchmarkModalSubtitle }}</p>
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
                <span class="student-meta-chip">{{ t.adminStudentSkills.major }}: {{ selectedStudent.major ?? '—' }}</span>
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
                <span><i class="legend-swatch faculty"></i> {{ t.adminStudentSkills.facultyAvgShort }}</span>
              </div>
            </div>

            <div class="detail-radar-wrap">
              <svg class="detail-radar" viewBox="0 0 500 400">
                <polygon points="250,45 380,120 380,270 250,345 120,270 120,120" class="radar-grid" />
                <polygon points="250,95 337,145 337,245 250,295 163,245 163,145" class="radar-grid" />
                <polygon points="250,145 293,170 293,220 250,245 207,220 207,170" class="radar-grid" />

                <line x1="250" y1="195" x2="250" y2="45" class="radar-axis" />
                <line x1="250" y1="195" x2="380" y2="120" class="radar-axis" />
                <line x1="250" y1="195" x2="380" y2="270" class="radar-axis" />
                <line x1="250" y1="195" x2="250" y2="345" class="radar-axis" />
                <line x1="250" y1="195" x2="120" y2="270" class="radar-axis" />
                <line x1="250" y1="195" x2="120" y2="120" class="radar-axis" />

                <polygon :points="selectedFacultyRadarPoints" class="student-faculty-area" />
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
                <span>{{ skillDisplay(skill.label) }}</span>
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
                <p>{{ t.adminStudentSkills.skillGapSub }}</p>
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
                        {{ Math.abs(gap.percentDifference).toFixed(0) }}% {{ t.adminStudentSkills.belowFacultyAverage }}
                      </span>
                    </div>
                    <AlertTriangle v-if="gap.difference <= -0.5" :size="16" />
                    <CheckCircle v-else :size="16" />
                  </div>

                  <div class="gap-comparison">
                    <span>{{ t.adminStudentSkills.student }} {{ gap.studentScore.toFixed(1) }}</span>
                    <span>{{ t.adminStudentSkills.faculty }} {{ gap.facultyScore.toFixed(1) }}</span>
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
                <span>{{ t.adminStudentSkills.noGapSub }}</span>
              </div>
            </section>
          </aside>
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