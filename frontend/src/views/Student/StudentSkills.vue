<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  BarChart3,
  CalendarDays,
  Download,
  Info,
  LoaderCircle,
  RefreshCw,
  UserCog,
  Users
} from 'lucide-vue-next'
import {
  API_BASE,
  studentHeaders
} from '../../constants/currentStudent'
import { SKILLS_BY_ROLE } from '../../constants/activitySkills'
import { useLanguage } from '../../composables/useLanguage'

const { t, currentLanguage } = useLanguage()

// โหมดการดู skill: participant = skill จากการเข้าร่วม, staff = skill จากการเป็นผู้จัด
const DEFAULT_TRACK = 'participant'

const loading = ref(true)
const trackLoading = ref(false)
const exporting = ref(false)
const errorMessage = ref('')
const exportOpen = ref(false)
const exportIncludeChart = ref(true)
const exportAction = ref('')

// track = โหมดของข้อมูลที่แสดงอยู่ตอนนี้, pendingTrack = โหมดที่กำลังโหลด
const track = ref(DEFAULT_TRACK)
const pendingTrack = ref('')
let loadRequestId = 0

const student = ref(null)
const apiSkillDefinitions = ref([])
const periodDefinitions = ref([])
const periods = ref({})
const selectedPeriod = ref('')
const showMySkills = ref(true)
const showFacultyAverage = ref(true)

// กราฟเปรียบเทียบ: major = กิจกรรมสาขา vs ค่าเฉลี่ยสาขา,
// faculty = กิจกรรมคณะ vs ค่าเฉลี่ยคณะ (ไม่นับกิจกรรมภายนอก)
const comparison = ref('major')

const comparisonOptions = computed(() => [
  {
    key: 'major',
    label: t.value.studentSkills.comparisonMajorOption
  },
  {
    key: 'faculty',
    label: t.value.studentSkills.comparisonFacultyOption
  }
])

const isMajorComparison = computed(() => comparison.value === 'major')

const comparisonText = computed(() => {
  const text = t.value.studentSkills

  return isMajorComparison.value
    ? {
        hint: text.comparisonMajorHint,
        mySkillsLegend: text.mySkillsMajorLegend,
        averageLegend: text.majorAverageLegend
      }
    : {
        hint: text.comparisonFacultyHint,
        mySkillsLegend: text.mySkillsFacultyLegend,
        averageLegend: text.facultyAverageLegend
      }
})

const hasStudentMajor = computed(() =>
  Boolean((student.value?.major || '').trim())
)

const scopeLabels = computed(() => ({
  major: t.value.studentSkills.scopeMajor,
  faculty: t.value.studentSkills.scopeFaculty,
  external: t.value.studentSkills.scopeExternal,
  other_major: t.value.studentSkills.scopeOtherMajor
}))

const trackOptions = computed(() => [
  {
    key: 'participant',
    label: t.value.studentSkills.participantSkillsOption,
    icon: Users
  },
  {
    key: 'staff',
    label: t.value.studentSkills.staffSkillsOption,
    icon: UserCog
  }
])

const isStaffTrack = computed(() => track.value === 'staff')

const activeTrackLabel = computed(() =>
  trackOptions.value.find((option) => option.key === track.value)
    ?.label || track.value
)

// ข้อความที่เปลี่ยนตามโหมด (participant / staff)
const trackText = computed(() => {
  const text = t.value.studentSkills

  return isStaffTrack.value
    ? {
        radarChartTitle: text.radarChartTitleStaff,
        noDataInPeriod: text.noDataInPeriodStaff,
        activitiesUsedTitle: text.activitiesUsedTitleStaff,
        noActivityData: text.noActivityDataStaff,
        noActivityDataSubtitle: text.noActivityDataSubtitleStaff
      }
    : {
        radarChartTitle: text.radarChartTitle,
        noDataInPeriod: text.noDataInPeriod,
        activitiesUsedTitle: text.activitiesUsedTitle,
        noActivityData: text.noActivityData,
        noActivityDataSubtitle: text.noActivityDataSubtitle
      }
})

// metadata (label, คำอธิบายภาษาไทย, icon) ของ skill ใน track ปัจจุบัน
const trackSkillMeta = computed(() =>
  SKILLS_BY_ROLE[track.value] || []
)

// ใช้ลำดับจาก API (skillDefinitions) แล้วเติม metadata จาก activitySkills.js
// ถ้า API ไม่ส่ง skillDefinitions มา ใช้ชุดของ track จาก activitySkills.js แทน
const skillDefinitions = computed(() => {
  const metaByKey = Object.fromEntries(
    trackSkillMeta.value.map((meta) => [meta.key, meta])
  )
  const source = apiSkillDefinitions.value.length
    ? apiSkillDefinitions.value
    : trackSkillMeta.value

  return source.map((definition) => {
    const meta = metaByKey[definition.key] || {}

    return {
      key: definition.key,
      label: definition.label || meta.label || definition.key,
      description: meta.description || '',
      icon: meta.icon || null
    }
  })
})

// คำอธิบายใน activitySkills.js เป็นภาษาไทย แสดงเฉพาะตอนใช้ภาษาไทย
const showSkillDescription = computed(() =>
  currentLanguage.value === 'TH'
)

const currentPeriod = computed(() =>
  periods.value[selectedPeriod.value] || {
    skills: {},
    activities: []
  }
)

const currentComparison = computed(() =>
  currentPeriod.value.comparisons?.[comparison.value] || {}
)

// ทักษะของฉันเฉพาะกิจกรรมในขอบเขตที่เลือก (สาขา / คณะ)
const currentSkills = computed(() =>
  currentComparison.value.skills || {}
)

// ค่าเฉลี่ยของขอบเขตที่เลือก (ค่าเฉลี่ยสาขา / ค่าเฉลี่ยคณะ)
const facultySkills = computed(() =>
  currentComparison.value.average || {}
)

const currentActivities = computed(() =>
  currentPeriod.value.activities || []
)

const selectedYear = ref('')
const selectedSemester = ref('all')

const yearOptions = computed(() => {
  const years = [
    ...new Set(
      periodDefinitions.value.map((period) =>
        String(period.year)
      )
    )
  ]

  return years.sort((a, b) => Number(b) - Number(a))
})

function syncPeriodControls(periodKey) {
  const period = periodDefinitions.value.find(
    (item) => item.key === periodKey
  )

  if (!period) return

  selectedYear.value = String(period.year)
  selectedSemester.value =
    period.semester === null
      ? 'all'
      : String(period.semester)
}

function applyPeriodSelection() {
  if (!selectedYear.value) return

  const key =
    selectedSemester.value === 'all'
      ? `year-${selectedYear.value}`
      : `semester-${selectedSemester.value}-${selectedYear.value}`

  if (periods.value[key]) {
    selectedPeriod.value = key
  }
}

watch(
  [selectedYear, selectedSemester],
  applyPeriodSelection
)

const skillItems = computed(() =>
  skillDefinitions.value.map((definition) => ({
    ...definition,
    value: currentSkills.value[definition.key] ?? null
  }))
)

// แบ่ง skill ครึ่งซ้าย / ครึ่งขวาของ radar ตามจำนวน skill จริงของ track
const leftSkills = computed(() =>
  skillItems.value.slice(0, Math.ceil(skillItems.value.length / 2))
)
const rightSkills = computed(() =>
  skillItems.value.slice(Math.ceil(skillItems.value.length / 2))
)

const RADAR_CENTER = 150
const RADAR_RADIUS = 112
const RADAR_LABEL_RADIUS = 137
const RADAR_GRID_LEVELS = [1, 0.8, 0.6, 0.4, 0.2]

// จำนวนแกนของ radar = จำนวน skill ของ track (อย่างน้อย 3 แกน)
const radarAxisCount = computed(() =>
  Math.max(
    3,
    skillDefinitions.value.length || trackSkillMeta.value.length
  )
)

function radarAngle(index, count) {
  return (-90 + index * (360 / count)) * Math.PI / 180
}

function radarPoint(index, count, ratio, radius = RADAR_RADIUS) {
  const angle = radarAngle(index, count)

  return [
    RADAR_CENTER + Math.cos(angle) * radius * ratio,
    RADAR_CENTER + Math.sin(angle) * radius * ratio
  ]
}

function skillRatio(value) {
  return Math.max(0, Math.min(5, Number(value ?? 0))) / 5
}

function polygonPoints(values) {
  if (!values.length) return ''

  return values
    .map((value, index) =>
      radarPoint(index, values.length, skillRatio(value)).join(',')
    )
    .join(' ')
}

const radarGridPolygons = computed(() =>
  RADAR_GRID_LEVELS.map((level) =>
    Array.from({ length: radarAxisCount.value }, (_, index) =>
      radarPoint(index, radarAxisCount.value, level).join(',')
    ).join(' ')
  )
)

const radarAxes = computed(() =>
  Array.from({ length: radarAxisCount.value }, (_, index) => {
    const [x, y] = radarPoint(index, radarAxisCount.value, 1)

    return { index, x, y }
  })
)

const radarPoints = computed(() =>
  polygonPoints(skillItems.value.map((item) => item.value))
)

const facultyRadarPoints = computed(() =>
  polygonPoints(
    skillDefinitions.value.map(
      (item) => facultySkills.value[item.key]
    )
  )
)

const hasFacultyData = computed(() =>
  skillDefinitions.value.some(
    (item) =>
      facultySkills.value[item.key] !== null &&
      facultySkills.value[item.key] !== undefined
  )
)

// ตัด label ยาวเป็นหลายบรรทัด (สูงสุด 3) บรรทัดละไม่เกิน RADAR_LABEL_MAX_CHARS
// ให้ label ด้านซ้าย/ขวาไม่ล้นออกนอกกรอบ radar ไปทับการ์ด skill ข้าง ๆ
// ภาษาไทยไม่เว้นวรรคระหว่างคำ จึงตัดคำด้วย Intl.Segmenter
const RADAR_LABEL_MAX_CHARS = 14
const RADAR_LABEL_MAX_LINES = 3

const thaiWordSegmenter = typeof Intl !== 'undefined' && Intl.Segmenter
  ? new Intl.Segmenter('th', { granularity: 'word' })
  : null

function splitRadarLabel(label) {
  const text = String(label || '')

  if (text.length <= RADAR_LABEL_MAX_CHARS) return [text]

  const hasSpaces = /\s/.test(text)
  const words = hasSpaces || !thaiWordSegmenter
    ? text.split(/\s+/)
    : [...thaiWordSegmenter.segment(text)].map((part) => part.segment)
  const joiner = hasSpaces ? ' ' : ''
  const lines = []

  for (const word of words) {
    const last = lines[lines.length - 1]

    if (last !== undefined && `${last}${joiner}${word}`.length <= RADAR_LABEL_MAX_CHARS) {
      lines[lines.length - 1] = `${last}${joiner}${word}`
    } else if (lines.length < RADAR_LABEL_MAX_LINES) {
      lines.push(word)
    } else {
      lines[lines.length - 1] = `${last}${joiner}${word}`
    }
  }

  return lines
}

const radarLabels = computed(() => {
  const items = skillItems.value
  if (!items.length) return []

  return items.map((item, index) => {
    const [x, y] = radarPoint(
      index,
      items.length,
      1,
      RADAR_LABEL_RADIUS
    )

    return {
      ...item,
      x,
      y,
      lines: splitRadarLabel(item.label)
    }
  })
})

const hasSkillData = computed(() =>
  skillItems.value.some((item) => item.value !== null)
)

function skillPercent(value) {
  if (value === null || value === undefined) return 0

  return Math.max(
    0,
    Math.min(100, (Number(value) / 5) * 100)
  )
}

function formatLevel(value) {
  if (value === null || value === undefined) return '-'

  return Number(value)
    .toFixed(2)
    .replace(/\.00$/, '')
}

function formatDate(value) {
  if (!value) return '-'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return '-'

  return new Intl.DateTimeFormat('th-TH', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  }).format(date)
}

function statusLabel(status) {
  const labels = {
    active: t.value.studentSkills.statusActive,
    completed: t.value.studentSkills.statusCompleted,
    approved: t.value.studentSkills.statusApproved,
    pending: t.value.studentSkills.statusPending,
    rejected: t.value.studentSkills.statusRejected,
    cancelled: t.value.studentSkills.statusCancelled
  }

  return labels[status] || status || '-'
}

// skill ของกิจกรรม เรียงตามลำดับ skill ของ track ปัจจุบัน
// และแสดงเฉพาะ skill ที่อยู่ใน track นี้
function activitySkillChips(activity) {
  const skills = activity?.skills || {}

  return skillDefinitions.value
    .filter(
      (definition) =>
        skills[definition.key] !== null &&
        skills[definition.key] !== undefined
    )
    .map((definition) => ({
      key: definition.key,
      label: definition.label,
      description: definition.description,
      level: skills[definition.key]
    }))
}

async function loadSkills(requestedTrack = track.value) {
  const requestId = ++loadRequestId
  const isInitialLoad = !student.value

  if (isInitialLoad) {
    loading.value = true
  } else {
    trackLoading.value = true
  }

  pendingTrack.value = requestedTrack
  errorMessage.value = ''

  try {
    const response = await fetch(
      `${API_BASE}/api/student/me/skills?track=${encodeURIComponent(requestedTrack)}`,
      {
        headers: studentHeaders()
      }
    )

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      throw new Error(
        data?.detail || t.value.studentSkills.loadError
      )
    }

    // มีการสลับโหมดใหม่ระหว่างรอ ให้ใช้ผลของคำขอล่าสุดเท่านั้น
    if (requestId !== loadRequestId) return

    const previousPeriod = selectedPeriod.value
    const nextPeriods = data.periods || {}

    student.value = data.student || null
    track.value = data.track || requestedTrack
    apiSkillDefinitions.value =
      data.skillDefinitions || []
    periodDefinitions.value =
      data.periodDefinitions || []
    periods.value = nextPeriods

    // คงช่วงเวลาที่เลือกไว้ ถ้ายังมีอยู่ในข้อมูลของโหมดใหม่
    selectedPeriod.value =
      previousPeriod && nextPeriods[previousPeriod]
        ? previousPeriod
        : data.defaultPeriod ||
          data.periodDefinitions?.[0]?.key ||
          ''

    syncPeriodControls(selectedPeriod.value)
  } catch (error) {
    if (requestId !== loadRequestId) return

    errorMessage.value =
      error instanceof TypeError
        ? `${t.value.studentSkills.connectionError} (${API_BASE})`
        : error.message
  } finally {
    if (requestId === loadRequestId) {
      loading.value = false
      trackLoading.value = false
      pendingTrack.value = ''
    }
  }
}

function selectTrack(nextTrack) {
  if (nextTrack === (pendingTrack.value || track.value)) return

  loadSkills(nextTrack)
}

function openExportModal() {
  exportIncludeChart.value = true
  exportAction.value = ''
  exportOpen.value = true
}

function closeExportModal() {
  if (exporting.value) return
  exportOpen.value = false
}

async function fetchTranscriptPdf() {
  const includeChart = exportIncludeChart.value
    ? 'true'
    : 'false'

  const response = await fetch(
    `${API_BASE}/api/student/me/skills/export?period=${encodeURIComponent(selectedPeriod.value)}&include_chart=${includeChart}&track=${encodeURIComponent(track.value)}`,
    {
      headers: studentHeaders()
    }
  )

  if (!response.ok) {
    const data = await response.json().catch(() => null)

    throw new Error(
      data?.detail || t.value.studentSkills.exportError
    )
  }

  const blob = await response.blob()

  if (blob.type !== 'application/pdf') {
    throw new Error(t.value.studentSkills.notPdfError)
  }

  return {
    blob,
    disposition:
      response.headers.get('content-disposition') || ''
  }
}

function filenameFromDisposition(disposition) {
  const match = disposition.match(
    /filename="?([^";]+)"?/i
  )

  return (
    match?.[1] ||
    `skill-transcript-${track.value}-${selectedPeriod.value}.pdf`
  )
}

async function downloadTranscript() {
  if (!selectedPeriod.value || exporting.value) return

  exporting.value = true
  exportAction.value = 'download'
  errorMessage.value = ''

  try {
    const { blob, disposition } =
      await fetchTranscriptPdf()

    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')

    link.href = url
    link.download =
      filenameFromDisposition(disposition)

    document.body.appendChild(link)
    link.click()
    link.remove()

    setTimeout(() => {
      URL.revokeObjectURL(url)
    }, 1000)

    exportOpen.value = false
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    exporting.value = false
    exportAction.value = ''
  }
}

async function printTranscript() {
  if (!selectedPeriod.value || exporting.value) return

  // เปิดหน้าต่างทันทีจาก click event ป้องกัน popup blocker
  const printWindow = window.open('', '_blank')

  if (!printWindow) {
    errorMessage.value = t.value.studentSkills.popupBlockedError
    return
  }

  const preparingTranscriptText = t.value.studentSkills.preparingTranscript

  printWindow.document.write(`
    <html>
      <head>
        <title>${preparingTranscriptText}</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            display: grid;
            min-height: 100vh;
            place-items: center;
            margin: 0;
            color: #475467;
          }
        </style>
      </head>
      <body>${preparingTranscriptText}</body>
    </html>
  `)
  printWindow.document.close()

  exporting.value = true
  exportAction.value = 'print'
  errorMessage.value = ''

  try {
    const { blob } = await fetchTranscriptPdf()
    const url = URL.createObjectURL(blob)

    // เปิด PDF ใน browser viewer
    // จากหน้านี้ผู้ใช้กด Print หรือ Save as PDF ได้ตามปกติ
    printWindow.location.href = url

    // เก็บ URL ไว้นานพอให้ PDF viewer โหลดไฟล์
    setTimeout(() => {
      URL.revokeObjectURL(url)
    }, 60_000)

    exportOpen.value = false
  } catch (error) {
    printWindow.close()
    errorMessage.value = error.message
  } finally {
    exporting.value = false
    exportAction.value = ''
  }
}
onMounted(() => loadSkills())
</script>

<template>
  <section class="skills-page">
    <div v-if="loading" class="state-card">
      <LoaderCircle class="spin" :size="22" />
      <span>{{ t.studentSkills.loading }}</span>
    </div>

    <div
      v-else-if="errorMessage && !student"
      class="state-card error-state"
    >
      <span>{{ errorMessage }}</span>

      <button type="button" @click="loadSkills()">
        <RefreshCw :size="15" />
        {{ t.studentSkills.retry }}
      </button>
    </div>

    <template v-else>
      <div class="page-heading">
        <div>
          <h1>{{ t.studentSkills.title }}</h1>

          <p v-if="student">
            {{ student.first_name }}
            {{ student.last_name }}
            <span v-if="student.student_id">
              · {{ student.student_id }}
            </span>
          </p>
        </div>

        <div class="heading-controls">
          <!-- สลับโหมด: skill ผู้เข้าร่วม / skill ผู้จัด (staff) -->
          <div
            class="track-toggle"
            role="group"
            :aria-label="t.studentSkills.skillTrackLabel"
            :aria-busy="trackLoading ? 'true' : 'false'"
          >
            <button
              v-for="option in trackOptions"
              :key="option.key"
              type="button"
              class="track-option"
              :class="{
                active: option.key === (pendingTrack || track)
              }"
              :aria-pressed="option.key === (pendingTrack || track) ? 'true' : 'false'"
              @click="selectTrack(option.key)"
            >
              <LoaderCircle
                v-if="trackLoading && pendingTrack === option.key"
                class="spin"
                :size="14"
              />
              <component
                :is="option.icon"
                v-else
                :size="14"
              />
              <span>{{ option.label }}</span>
            </button>
          </div>

          <!-- เลือกปี + ช่วงเวลา แบบเดียวกับหน้า Admin -->
          <div class="period-controls">
            <select
              v-model="selectedYear"
              class="period-select year-select"
            >
              <option
                v-for="year in yearOptions"
                :key="year"
                :value="year"
              >
                ปี {{ year }}
              </option>
            </select>

            <select
              v-model="selectedSemester"
              class="period-select semester-select"
            >
              <option value="all">ทั้งปี</option>
              <option value="1">เทอม 1</option>
              <option value="2">เทอม 2</option>
            </select>
          </div>
        </div>
      </div>

      <div
        v-if="isStaffTrack"
        class="track-hint"
      >
        <Info :size="15" />
        <span>{{ t.studentSkills.staffTrackHint }}</span>
      </div>

      <div
        v-if="errorMessage"
        class="inline-error"
      >
        {{ errorMessage }}
      </div>

      <div
        class="overview-card"
        :class="{ refreshing: trackLoading }"
      >
        <div class="section-title">
          <BarChart3 :size="18" />

          <span>
            {{ trackText.radarChartTitle }}
          </span>

          <span
            v-if="currentPeriod.label"
            class="period-chip"
          >
            {{ currentPeriod.label }}
          </span>
        </div>

        <div class="comparison-bar">
          <div
            class="track-toggle comparison-toggle"
            role="group"
            :aria-label="t.studentSkills.comparisonLabel"
          >
            <button
              v-for="option in comparisonOptions"
              :key="option.key"
              type="button"
              class="track-option"
              :class="{ active: option.key === comparison }"
              :aria-pressed="option.key === comparison ? 'true' : 'false'"
              @click="comparison = option.key"
            >
              {{ option.label }}
            </button>
          </div>

          <p class="comparison-hint">
            {{
              isMajorComparison && !hasStudentMajor
                ? t.studentSkills.comparisonNoMajor
                : comparisonText.hint
            }}
          </p>
        </div>

        <div class="overview-grid">
          <!-- LEFT -->
          <div class="skill-column">
            <div
              v-for="skill in leftSkills"
              :key="skill.key"
              class="skill-card"
              :title="skill.description || skill.label"
            >
              <div class="skill-card-top">
                <span class="skill-card-name">
                  <component
                    :is="skill.icon"
                    v-if="skill.icon"
                    class="skill-card-icon"
                    :size="15"
                  />
                  <span>
                    {{ skill.label }}
                    <small v-if="showSkillDescription && skill.description">
                      {{ skill.description }}
                    </small>
                  </span>
                </span>

                <strong>
                  {{ formatLevel(skill.value) }} / 5
                </strong>
              </div>

              <div class="progress-track">
                <div
                  class="progress-value"
                  :style="{
                    width: `${skillPercent(skill.value)}%`
                  }"
                ></div>
              </div>
            </div>
          </div>

          <!-- RADAR -->
          <div class="radar-area">
            <div class="radar-wrap">
              <!-- เว้นขอบซ้าย/ขวา 30 หน่วยไว้ให้ label ด้านข้าง (radar อยู่กลางที่ 150,150 เหมือนเดิม) -->
              <svg
                viewBox="-30 -6 360 312"
                class="radar"
              >
                <!-- grid + แกน สร้างตามจำนวน skill ของ track -->
                <polygon
                  v-for="(points, index) in radarGridPolygons"
                  :key="`grid-${index}`"
                  :points="points"
                  class="grid"
                />

                <line
                  v-for="axis in radarAxes"
                  :key="`axis-${axis.index}`"
                  :x1="RADAR_CENTER"
                  :y1="RADAR_CENTER"
                  :x2="axis.x"
                  :y2="axis.y"
                  class="axis"
                />

                <polygon
                  v-if="hasFacultyData && showFacultyAverage"
                  :points="facultyRadarPoints"
                  class="faculty-radar"
                />

                <polygon
                  v-if="hasSkillData && showMySkills"
                  :points="radarPoints"
                  class="student-radar"
                />

                <g
                  v-for="label in radarLabels"
                  :key="label.key"
                >
                  <text
                    :x="label.x"
                    :y="label.y"
                    text-anchor="middle"
                    dominant-baseline="middle"
                    class="radar-label"
                  >
                    <title>{{ label.description || label.label }}</title>
                    <tspan
                      v-for="(line, lineIndex) in label.lines"
                      :key="lineIndex"
                      :x="label.x"
                      :dy="lineIndex === 0
                        ? `${-(label.lines.length - 1) * 0.6}em`
                        : '1.2em'"
                    >{{ line }}</tspan>
                  </text>
                </g>
              </svg>

              <div class="radar-legend">
                <button
                  type="button"
                  class="legend-toggle"
                  :class="{ inactive: !showMySkills }"
                  @click="showMySkills = !showMySkills"
                >
                  <i class="legend-dot student-dot"></i>
                  {{ comparisonText.mySkillsLegend }}
                </button>

                <button
                  type="button"
                  class="legend-toggle"
                  :class="{ inactive: !showFacultyAverage }"
                  @click="showFacultyAverage = !showFacultyAverage"
                >
                  <i class="legend-line faculty-line"></i>
                  {{ comparisonText.averageLegend }}
                </button>
              </div>

              <div
                v-if="!hasSkillData"
                class="radar-empty"
              >
                <strong>{{ t.studentSkills.skillRadar }}</strong>

                <span>
                  {{ trackText.noDataInPeriod }}
                </span>
              </div>
            </div>
          </div>

          <!-- RIGHT -->
          <div class="skill-column">
            <div
              v-for="skill in rightSkills"
              :key="skill.key"
              class="skill-card"
              :title="skill.description || skill.label"
            >
              <div class="skill-card-top">
                <span class="skill-card-name">
                  <component
                    :is="skill.icon"
                    v-if="skill.icon"
                    class="skill-card-icon"
                    :size="15"
                  />
                  <span>
                    {{ skill.label }}
                    <small v-if="showSkillDescription && skill.description">
                      {{ skill.description }}
                    </small>
                  </span>
                </span>

                <strong>
                  {{ formatLevel(skill.value) }} / 5
                </strong>
              </div>

              <div class="progress-track">
                <div
                  class="progress-value"
                  :style="{
                    width: `${skillPercent(skill.value)}%`
                  }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ACTIVITIES -->
      <div
        class="activity-card"
        :class="{ refreshing: trackLoading }"
      >
        <div class="activity-title">
          <div class="activity-title-left">
            <CalendarDays :size="17" />

            <span>
              {{ trackText.activitiesUsedTitle }}
            </span>
          </div>

          <span class="activity-count">
            {{ currentActivities.length }} {{ t.studentSkills.activitiesUnit }}
          </span>
        </div>

        <!--
          ถ้ากิจกรรมเยอะ:
          table-body-scroll จำกัดความสูง
          แล้วเลื่อนขึ้นลงภายในกรอบนี้
        -->
        <div class="table-scroll">
          <div class="table-body-scroll">
            <table>
              <thead>
                <tr>
                  <th>{{ t.studentSkills.tableActivityName }}</th>
                  <th>{{ t.studentSkills.tableDescription }}</th>
                  <th>{{ t.studentSkills.tableSkillsGained }}</th>
                  <th>{{ t.studentSkills.tableDate }}</th>
                  <th>{{ t.studentSkills.tableStatus }}</th>
                </tr>
              </thead>

              <tbody>
                <tr
                  v-for="activity in currentActivities"
                  :key="`${activity.source}-${activity.id}`"
                >
                  <td class="activity-name">
                    {{ activity.title }}
                    <span
                      v-if="activity.scope"
                      class="scope-badge"
                      :class="`scope-${activity.scope}`"
                    >
                      {{ scopeLabels[activity.scope] || activity.scope }}
                    </span>
                  </td>

                  <td>
                    {{ activity.description || '-' }}
                  </td>

                  <td>
                    <div class="skill-tags">
                      <span
                        v-for="chip in activitySkillChips(activity)"
                        :key="chip.key"
                        class="skill-tag"
                        :title="chip.description || chip.label"
                      >
                        {{ chip.label }}
                        {{ chip.level }}/5
                      </span>
                    </div>
                  </td>

                  <td>
                    {{ formatDate(activity.start_at) }}
                  </td>

                  <td>
                    <span
                      class="status-pill"
                      :class="`status-${activity.status}`"
                    >
                      {{ statusLabel(activity.status) }}
                    </span>
                  </td>
                </tr>

                <tr v-if="currentActivities.length === 0">
                  <td colspan="5">
                    <div class="empty-table">
                      <strong>
                        {{ trackText.noActivityData }}
                      </strong>

                      <span>
                        {{ trackText.noActivityDataSubtitle }}
                      </span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- EXPORT -->
      <div class="export-row">
        <button
          class="export-button"
          type="button"
          :disabled="exporting || trackLoading"
          @click="openExportModal"
        >
          <Download :size="15" />
          {{ t.studentSkills.exportButton }}
        </button>
      </div>
    </template>
  
      <!-- EXPORT MODAL -->
      <Teleport to="body">
      <div
        v-if="exportOpen"
        class="export-overlay"
        @click.self="closeExportModal"
      >
        <div class="export-modal">
          <div class="export-modal-header">
            <div>
              <h2>{{ t.studentSkills.exportModalTitle }}</h2>
              <p>
                {{ t.studentSkills.exportModalSubtitle }}
              </p>
            </div>

            <button
              class="modal-close"
              type="button"
              :disabled="exporting"
              @click="closeExportModal"
            >
              ×
            </button>
          </div>

          <div class="export-period-box">
            <span>{{ t.studentSkills.selectedPeriodLabel }}</span>
            <strong>
              {{ currentPeriod.label || '-' }}
            </strong>
          </div>

          <div class="export-period-box export-track-box">
            <span>{{ t.studentSkills.skillTrackLabel }}</span>
            <strong>
              {{ activeTrackLabel }}
            </strong>
          </div>

          <div class="export-section">
            <h3>{{ t.studentSkills.transcriptStyleTitle }}</h3>

            <label
              class="export-option"
              :class="{
                selected: exportIncludeChart
              }"
            >
              <input
                v-model="exportIncludeChart"
                type="radio"
                :value="true"
              />

              <div>
                <strong>{{ t.studentSkills.withRadarChart }}</strong>
                <span>

                  {{ t.studentSkills.withRadarChartDesc }}

            

                </span>
              </div>
            </label>

            <label
              class="export-option"
              :class="{
                selected: !exportIncludeChart
              }"
            >
              <input
                v-model="exportIncludeChart"
                type="radio"
                :value="false"
              />

              <div>
                <strong>{{ t.studentSkills.withoutRadarChart }}</strong>
                <span>
                  {{ t.studentSkills.withoutRadarChartDesc }}
                </span>
              </div>
            </label>
          </div>

          <div class="export-modal-actions">
            <button
              class="print-button"
              type="button"
              :disabled="exporting"
              @click="printTranscript"
            >
              <LoaderCircle
                v-if="
                  exporting &&
                  exportAction === 'print'
                "
                class="spin"
                :size="16"
              />
              <span v-else>🖨</span>

              {{
                exporting &&
                exportAction === 'print'
                  ? t.studentSkills.preparingDots
                  : t.studentSkills.printButton
              }}
            </button>

            <button
              class="download-button"
              type="button"
              :disabled="exporting"
              @click="downloadTranscript"
            >
              <LoaderCircle
                v-if="
                  exporting &&
                  exportAction === 'download'
                "
                class="spin"
                :size="16"
              />
              <Download
                v-else
                :size="16"
              />

              {{
                exporting &&
                exportAction === 'download'
                  ? t.studentSkills.generatingPdf
                  : t.studentSkills.downloadPdfButton
              }}
            </button>
          </div>
        </div>
      </div>
      </Teleport>

</section>
</template>

<style scoped>
* {
  box-sizing: border-box;
}

.skills-page {
  width: 100%;
  min-height: 100vh;
  padding: 24px 28px 38px;
  background: #f5f7fb;
  color: #17213c;
}

.page-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 16px;
}

.page-heading h1 {
  margin: 0 0 5px;
  color: #172d68;
  font-size: 26px;
}

.page-heading p {
  margin: 0;
  color: #8793aa;
  font-size: var(--fs-body);
}

.period-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.period-select {
  min-width: 112px;
  padding: 9px 12px;
  border: 1px solid #d7deeb;
  border-radius: 8px;
  outline: none;
  background: #fff;
  color: #33415f;
}

/* =========================
   SKILL TRACK TOGGLE
========================= */

.heading-controls {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
}

.track-toggle {
  display: inline-flex;
  gap: 3px;
  padding: 3px;
  border: 1px solid #d7deeb;
  border-radius: 9px;
  background: #fff;
}

.track-option {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 7px 12px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #33415f;
  font: inherit;
  font-size: var(--fs-body);
  font-weight: 650;
  white-space: nowrap;
  cursor: pointer;
  transition: background .18s ease, color .18s ease;
}

.track-option:hover {
  background: #f4f7fb;
}

.track-option.active {
  background: #172d78;
  color: #fff;
}

.track-option:focus-visible {
  outline: 2px solid #356fe5;
  outline-offset: 1px;
}

.track-hint {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 12px;
  padding: 10px 12px;
  border: 1px solid #d6e0f5;
  border-radius: 8px;
  background: #eef3ff;
  color: #315bb0;
  font-size: var(--fs-small);
  line-height: 1.6;
}

.track-hint svg {
  flex: none;
  margin-top: 1px;
}

.comparison-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
  margin: -10px 0 20px;
}

.comparison-hint {
  flex: 1 1 260px;
  margin: 0;
  color: #667085;
  font-size: var(--fs-small);
  line-height: 1.6;
}

.scope-badge {
  display: inline-block;
  margin-left: 6px;
  padding: 2px 7px;
  border-radius: 999px;
  background: #eef2f7;
  color: #475467;
  font-size: var(--fs-badge);
  font-weight: 700;
  vertical-align: middle;
}

.scope-major {
  background: #e8f0ff;
  color: #2859bd;
}

.scope-faculty {
  background: #dcfce7;
  color: #16753a;
}

.overview-card,
.activity-card {
  transition: opacity .18s ease;
}

.overview-card.refreshing,
.activity-card.refreshing {
  opacity: .55;
}

.overview-card {
  width: 100%;
  min-height: 440px;
  padding: 25px 28px 30px;
  border: 1px solid #d8deea;
  border-radius: 17px;
  background: #fff;
}

.section-title,
.activity-title,
.activity-title-left {
  display: flex;
  align-items: center;
}

.section-title {
  gap: 7px;
  margin-bottom: 24px;
  color: #1a2340;
  font-size: var(--fs-body);
  font-weight: 700;
}

.period-chip {
  margin-left: auto;
  padding: 5px 9px;
  border-radius: 999px;
  background: #eef3ff;
  color: #315bb0;
  font-size: var(--fs-caption);
}

.overview-grid {
  display: grid;
  grid-template-columns:
    minmax(210px, 1fr)
    minmax(360px, 1.65fr)
    minmax(210px, 1fr);
  align-items: center;
  gap: 30px;
  min-height: 330px;
}

.skill-column {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.skill-card {
  min-height: 88px;
  padding: 16px;
  border: 1px solid #d8deea;
  border-radius: 12px;
  background: #fff;
}

.skill-card-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  min-height: 43px;
  font-size: var(--fs-small);
  font-weight: 650;
}

.skill-card-top strong {
  flex: none;
  color: #172d78;
}

.skill-card-name {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  min-width: 0;
}

.skill-card-icon {
  flex: none;
  margin-top: 1px;
  color: #172d78;
}

.skill-card-name small {
  display: block;
  margin-top: 3px;
  color: #8793aa;
  font-size: var(--fs-caption);
  font-weight: 500;
}

.progress-track {
  height: 6px;
  overflow: hidden;
  border-radius: 999px;
  background: #e9edf3;
}

.progress-value {
  height: 100%;
  border-radius: inherit;
  background: #172d78;
  transition: width .25s ease;
}

.radar-area {
  display: flex;
  justify-content: center;
}

.radar-wrap {
  position: relative;
  width: min(100%, 390px);
  aspect-ratio: 1;
}

.radar {
  width: 100%;
  height: 100%;
  overflow: visible;
}

.grid {
  fill: none;
  stroke: #dce4ef;
  stroke-width: 1;
}

.axis {
  stroke: #e3e8f0;
  stroke-width: 1;
}

.faculty-radar {
  fill: rgba(16, 185, 129, .08);
  stroke: #10b981;
  stroke-width: 2;
  stroke-dasharray: 5 4;
}

.student-radar {
  fill: rgba(53, 112, 229, .18);
  stroke: #356fe5;
  stroke-width: 2;
}

.radar-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  margin-top: -4px;
  color: #667085;
  font-size: var(--fs-badge);
  font-weight: 650;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend-toggle {
  border: 0;
  background: transparent;
  padding: 5px 7px;
  border-radius: 7px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #667085;
  font: inherit;
  font-weight: 650;
  cursor: pointer;
  transition: opacity .18s ease, background .18s ease;
}

.legend-toggle:hover {
  background: #f4f7fb;
}

.legend-toggle.inactive {
  opacity: .35;
  text-decoration: line-through;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.student-dot {
  background: #356fe5;
}

.legend-line {
  width: 18px;
  height: 0;
  border-top: 2px dashed #10b981;
}

.radar-label {
  fill: #52617d;
  font-size: 7px;
  font-weight: 600;
}

.radar-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  display: flex;
  width: 175px;
  padding: 12px;
  flex-direction: column;
  gap: 5px;
  border: 1px solid #e1e5ed;
  border-radius: 9px;
  background: rgba(255, 255, 255, .96);
  text-align: center;
  transform: translate(-50%, -50%);
}

.radar-empty strong {
  font-size: var(--fs-small);
}

.radar-empty span {
  color: #929db0;
  font-size: var(--fs-badge);
}

/* =========================
   ACTIVITY TABLE
========================= */

.activity-card {
  margin-top: 18px;
  overflow: hidden;
  border: 1px solid #d8deea;
  border-radius: 12px;
  background: #fff;
}

.activity-title {
  justify-content: space-between;
  gap: 15px;
  padding: 16px 18px;
  border-bottom: 1px solid #e8edf4;
}

.activity-title-left {
  gap: 7px;
  color: #1a2340;
  font-size: var(--fs-body);
  font-weight: 700;
}

.activity-count {
  padding: 5px 9px;
  border-radius: 999px;
  background: #f2f4f7;
  color: #667085;
  font-size: var(--fs-caption);
  font-weight: 700;
}

.table-scroll {
  width: 100%;
  overflow-x: auto;
}

/*
  ตารางสูงสุดประมาณ 5 แถว
  ถ้ามีกิจกรรมมากกว่านี้จะมี scrollbar แนวตั้ง
*/
.table-body-scroll {
  max-height: 360px;
  overflow-y: auto;
}

table {
  width: 100%;
  min-width: 900px;
  border-collapse: separate;
  border-spacing: 0;
}

thead {
  position: sticky;
  top: 0;
  z-index: 2;
  background: #eef3ff;
}

th,
td {
  padding: 14px 16px;
  border-bottom: 1px solid #e8ecf2;
  text-align: left;
  vertical-align: top;
}

th {
  color: #28354e;
  font-size: var(--fs-small);
  letter-spacing: .04em;
}

td {
  color: #58657b;
  font-size: var(--fs-small);
}

.activity-name {
  color: #263553;
  font-weight: 700;
}

.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.skill-tag {
  padding: 4px 7px;
  border-radius: 999px;
  background: #f0e5ff;
  color: #7b20b6;
  font-size: var(--fs-badge);
  font-weight: 650;
}

.status-pill {
  display: inline-flex;
  padding: 4px 8px;
  border-radius: 999px;
  background: #eef2f7;
  font-size: var(--fs-badge);
  font-weight: 700;
}

.status-approved,
.status-completed {
  background: #dcfce7;
  color: #16753a;
}

.status-active {
  background: #e8f0ff;
  color: #2859bd;
}

.status-pending {
  background: #fff4d7;
  color: #9a6700;
}

.status-rejected,
.status-cancelled {
  background: #fee2e2;
  color: #b42318;
}

.empty-table {
  display: flex;
  min-height: 160px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 7px;
  color: #98a2b3;
}

/* =========================
   EXPORT
========================= */

.export-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.export-button,
.state-card button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border: 0;
  border-radius: 7px;
  cursor: pointer;
}

.export-button {
  min-height: 37px;
  padding: 0 14px;
  background: #8500b7;
  color: #fff;
  font-size: var(--fs-small);
  font-weight: 700;
}

.export-button:disabled {
  cursor: wait;
  opacity: .7;
}

.state-card {
  display: flex;
  min-height: 220px;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 1px solid #d8deea;
  border-radius: 14px;
  background: #fff;
  color: #667085;
}

.error-state {
  flex-direction: column;
  color: #b42318;
}

.state-card button {
  padding: 8px 12px;
  color: #344054;
}

.inline-error {
  margin-bottom: 12px;
  padding: 10px 12px;
  border: 1px solid #fecdca;
  border-radius: 8px;
  background: #fef3f2;
  color: #b42318;
  font-size: var(--fs-small);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}


/* =========================
   EXPORT MODAL
========================= */

.export-overlay {
  position: fixed;
  z-index: 3000;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(15, 23, 42, .46);
}

.export-modal {
  width: min(100%, 560px);
  overflow: hidden;
  border: 1px solid #d8deea;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 24px 70px rgba(15, 23, 42, .18);
}

.export-modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 22px 22px 17px;
  border-bottom: 1px solid #e9edf3;
}

.export-modal-header h2 {
  margin: 0 0 5px;
  color: #172d68;
  font-size: 21px;
}

.export-modal-header p {
  margin: 0;
  color: #8793aa;
  font-size: var(--fs-small);
}

.modal-close {
  width: 34px;
  height: 34px;
  flex: none;
  border: 1px solid #d8deea;
  border-radius: 8px;
  background: #fff;
  color: #667085;
  cursor: pointer;
  font-size: 25px;
  line-height: 1;
}

.export-period-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 18px 22px 0;
  padding: 13px 14px;
  border-radius: 10px;
  background: #f5f7fb;
}

.export-period-box span {
  color: #7b879c;
  font-size: var(--fs-small);
}

.export-period-box strong {
  color: #244d9e;
  font-size: var(--fs-small);
}

.export-track-box {
  margin-top: 10px;
}

.export-section {
  padding: 20px 22px;
}

.export-section h3 {
  margin: 0 0 11px;
  color: #344054;
  font-size: var(--fs-lead);
}

.export-option {
  display: flex;
  align-items: flex-start;
  gap: 11px;
  margin-top: 10px;
  padding: 14px;
  border: 1px solid #d8deea;
  border-radius: 11px;
  cursor: pointer;
  transition: .18s ease;
}

.export-option.selected {
  border-color: #8750d7;
  background: #faf7ff;
  box-shadow: 0 0 0 2px rgba(135, 80, 215, .08);
}

.export-option input {
  margin-top: 2px;
  accent-color: #8500b7;
}

.export-option div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.export-option strong {
  color: #24324b;
  font-size: var(--fs-small);
}

.export-option span {
  color: #8793aa;
  font-size: var(--fs-caption);
  line-height: 1.6;
}

.export-modal-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  padding: 0 22px 22px;
}

.print-button,
.download-button {
  display: inline-flex;
  min-height: 42px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 8px;
  cursor: pointer;
  font-size: var(--fs-small);
  font-weight: 700;
}

.print-button {
  border: 1px solid #cfd7e6;
  background: #fff;
  color: #344054;
}

.download-button {
  border: 1px solid #8500b7;
  background: #8500b7;
  color: #fff;
}

.print-button:disabled,
.download-button:disabled,
.modal-close:disabled {
  cursor: wait;
  opacity: .65;
}


@media (max-width: 1100px) {
  .overview-grid {
    grid-template-columns: 1fr 1fr;
  }

  .radar-area {
    grid-column: 1 / -1;
    grid-row: 1;
  }
}

@media (max-width: 720px) {
  .skills-page {
    padding: 18px 13px 30px;
  }

  .page-heading {
    align-items: stretch;
    flex-direction: column;
  }

  .heading-controls {
    width: 100%;
    align-items: stretch;
  }

  .track-toggle {
    display: flex;
    width: 100%;
  }

  .track-option {
    flex: 1 1 0;
    min-width: 0;
    padding: 8px;
    white-space: normal;
    text-align: center;
  }

  .period-controls {
    width: 100%;
  }

  .period-select {
    width: 50%;
  }

  .overview-card {
    padding: 20px 15px;
  }

  .overview-grid {
    grid-template-columns: 1fr;
  }

  .radar-area {
    grid-column: auto;
  }

  .export-button {
    width: 100%;
  }

  .export-modal-actions {
    grid-template-columns: 1fr;
  }
}


/* =========================
   READABILITY UPDATE
   เพิ่มขนาดตัวอักษรทั้งหน้าเล็กน้อย
========================= */

.skills-page {
  font-size: var(--fs-body);
}

.skills-page h1 {
  font-size: 27px;
}

.skills-page .page-subtitle {
  font-size: var(--fs-body);
}

.skills-page .chart-title,
.skills-page .activities-title {
  font-size: var(--fs-body);
}

.skills-page .skill-name {
  font-size: var(--fs-body);
}

.skills-page .skill-score {
  font-size: var(--fs-body);
}

.skills-page .radar-label {
  font-size: 10px;
}

.skills-page .period-select {
  font-size: var(--fs-body);
}

.skills-page .period-badge {
  font-size: var(--fs-small);
}

.skills-page .radar-legend,
.skills-page .legend-toggle {
  font-size: var(--fs-small);
}

.skills-page .activity-table {
  font-size: var(--fs-small);
}

.skills-page .activity-table th {
  font-size: var(--fs-small);
}

.skills-page .activity-table td {
  font-size: var(--fs-small);
}

.skills-page .skill-chip,
.skills-page .status-badge,
.skills-page .activity-count {
  font-size: var(--fs-caption);
}

.skills-page .export-button {
  font-size: var(--fs-small);
}

.legend-toggle .student-dot {
  width: 9px;
  height: 9px;
  flex: 0 0 9px;
  border-radius: 50%;
  background: #356fe5;
}

.legend-toggle .faculty-line {
  width: 19px;
  flex: 0 0 19px;
  border-top: 3px dashed #10b981;
}

.legend-toggle.inactive .student-dot,
.legend-toggle.inactive .faculty-line {
  opacity: .35;
}


</style>
