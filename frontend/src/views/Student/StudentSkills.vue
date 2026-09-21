<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  BarChart3,
  CalendarDays,
  Download,
  LoaderCircle,
  RefreshCw
} from 'lucide-vue-next'
import {
  API_BASE,
  studentHeaders
} from '../../constants/currentStudent'
import { useLanguage } from '../../composables/useLanguage'

const { t } = useLanguage()

const loading = ref(true)
const exporting = ref(false)
const errorMessage = ref('')
const exportOpen = ref(false)
const exportIncludeChart = ref(true)
const exportAction = ref('')

const student = ref(null)
const skillDefinitions = ref([])
const periodDefinitions = ref([])
const periods = ref({})
const selectedPeriod = ref('')

const currentPeriod = computed(() =>
  periods.value[selectedPeriod.value] || {
    skills: {},
    activities: []
  }
)

const currentSkills = computed(() =>
  currentPeriod.value.skills || {}
)

const currentActivities = computed(() =>
  currentPeriod.value.activities || []
)

const periodGroups = computed(() => {
  const groups = new Map()

  for (const period of periodDefinitions.value) {
    if (!groups.has(period.year)) {
      groups.set(period.year, [])
    }
    groups.get(period.year).push(period)
  }

  return [...groups.entries()].map(([year, items]) => ({
    year,
    items
  }))
})

const skillItems = computed(() =>
  skillDefinitions.value.map((definition) => ({
    ...definition,
    value: currentSkills.value[definition.key] ?? null
  }))
)

const leftSkills = computed(() => skillItems.value.slice(0, 3))
const rightSkills = computed(() => skillItems.value.slice(3, 6))

const radarPoints = computed(() => {
  const items = skillItems.value
  if (!items.length) return ''

  const center = 150
  const radius = 112

  return items.map((item, index) => {
    const value = Number(item.value ?? 0)
    const ratio = Math.max(0, Math.min(5, value)) / 5
    const angle =
      (-90 + index * (360 / items.length)) *
      Math.PI / 180

    return [
      center + Math.cos(angle) * radius * ratio,
      center + Math.sin(angle) * radius * ratio
    ].join(',')
  }).join(' ')
})

const radarLabels = computed(() => {
  const items = skillItems.value
  if (!items.length) return []

  const center = 150
  const radius = 137

  return items.map((item, index) => {
    const angle =
      (-90 + index * (360 / items.length)) *
      Math.PI / 180

    return {
      ...item,
      x: center + Math.cos(angle) * radius,
      y: center + Math.sin(angle) * radius
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

function skillLabel(key) {
  return (
    skillDefinitions.value.find(
      (item) => item.key === key
    )?.label || key
  )
}

async function loadSkills() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(
      `${API_BASE}/api/student/me/skills`,
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

    student.value = data.student || null
    skillDefinitions.value =
      data.skillDefinitions || []
    periodDefinitions.value =
      data.periodDefinitions || []
    periods.value = data.periods || {}
    selectedPeriod.value =
      data.defaultPeriod ||
      data.periodDefinitions?.[0]?.key ||
      ''
  } catch (error) {
    errorMessage.value =
      error instanceof TypeError
        ? `${t.value.studentSkills.connectionError} (${API_BASE})`
        : error.message
  } finally {
    loading.value = false
  }
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
    `${API_BASE}/api/student/me/skills/export?period=${encodeURIComponent(selectedPeriod.value)}&include_chart=${includeChart}`,
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
    `skill-transcript-${selectedPeriod.value}.pdf`
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
onMounted(loadSkills)
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

      <button type="button" @click="loadSkills">
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

        <!-- เลือกดูทั้งปี / Semester 1 / Semester 2 -->
        <select
          v-model="selectedPeriod"
          class="period-select"
        >
          <optgroup
            v-for="group in periodGroups"
            :key="group.year"
            :label="`${t.studentSkills.year} ${group.year}`"
          >
            <option
              v-for="period in group.items"
              :key="period.key"
              :value="period.key"
            >
              {{ period.label }}
            </option>
          </optgroup>
        </select>
      </div>

      <div
        v-if="errorMessage"
        class="inline-error"
      >
        {{ errorMessage }}
      </div>

      <div class="overview-card">
        <div class="section-title">
          <BarChart3 :size="18" />

          <span>
            {{ t.studentSkills.radarChartTitle }}
          </span>

          <span
            v-if="currentPeriod.label"
            class="period-chip"
          >
            {{ currentPeriod.label }}
          </span>
        </div>

        <div class="overview-grid">
          <!-- LEFT -->
          <div class="skill-column">
            <div
              v-for="skill in leftSkills"
              :key="skill.key"
              class="skill-card"
            >
              <div class="skill-card-top">
                <span>{{ skill.label }}</span>

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
              <svg
                viewBox="0 0 300 300"
                class="radar"
              >
                <polygon
                  points="150,38 247,94 247,206 150,262 53,206 53,94"
                  class="grid"
                />
                <polygon
                  points="150,60 228,105 228,195 150,240 72,195 72,105"
                  class="grid"
                />
                <polygon
                  points="150,83 208,116 208,184 150,217 92,184 92,116"
                  class="grid"
                />
                <polygon
                  points="150,105 189,128 189,172 150,195 111,172 111,128"
                  class="grid"
                />
                <polygon
                  points="150,128 169,139 169,161 150,172 131,161 131,139"
                  class="grid"
                />

                <line
                  x1="150"
                  y1="150"
                  x2="150"
                  y2="38"
                  class="axis"
                />
                <line
                  x1="150"
                  y1="150"
                  x2="247"
                  y2="94"
                  class="axis"
                />
                <line
                  x1="150"
                  y1="150"
                  x2="247"
                  y2="206"
                  class="axis"
                />
                <line
                  x1="150"
                  y1="150"
                  x2="150"
                  y2="262"
                  class="axis"
                />
                <line
                  x1="150"
                  y1="150"
                  x2="53"
                  y2="206"
                  class="axis"
                />
                <line
                  x1="150"
                  y1="150"
                  x2="53"
                  y2="94"
                  class="axis"
                />

                <polygon
                  v-if="hasSkillData"
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
                    {{ label.label }}
                  </text>
                </g>
              </svg>

              <div
                v-if="!hasSkillData"
                class="radar-empty"
              >
                <strong>{{ t.studentSkills.skillRadar }}</strong>

                <span>
                  {{ t.studentSkills.noDataInPeriod }}
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
            >
              <div class="skill-card-top">
                <span>{{ skill.label }}</span>

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
      <div class="activity-card">
        <div class="activity-title">
          <div class="activity-title-left">
            <CalendarDays :size="17" />

            <span>
              {{ t.studentSkills.activitiesUsedTitle }}
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
                  </td>

                  <td>
                    {{ activity.description || '-' }}
                  </td>

                  <td>
                    <div class="skill-tags">
                      <span
                        v-for="(level, key) in activity.skills"
                        :key="key"
                        class="skill-tag"
                      >
                        {{ skillLabel(key) }}
                        {{ level }}/5
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
                        {{ t.studentSkills.noActivityData }}
                      </strong>

                      <span>
                        {{ t.studentSkills.noActivityDataSubtitle }}
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
          :disabled="exporting"
          @click="openExportModal"
        >
          <Download :size="15" />
          {{ t.studentSkills.exportButton }}
        </button>
      </div>
    </template>
  
      <!-- EXPORT MODAL -->
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
  font-size: 24px;
}

.page-heading p {
  margin: 0;
  color: #8793aa;
  font-size: 13px;
}

.period-select {
  min-width: 190px;
  padding: 9px 12px;
  border: 1px solid #d7deeb;
  border-radius: 8px;
  outline: none;
  background: #fff;
  color: #33415f;
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
  font-size: 13px;
  font-weight: 700;
}

.period-chip {
  margin-left: auto;
  padding: 5px 9px;
  border-radius: 999px;
  background: #eef3ff;
  color: #315bb0;
  font-size: 10px;
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
  font-size: 11px;
  font-weight: 650;
}

.skill-card-top strong {
  flex: none;
  color: #172d78;
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

.student-radar {
  fill: rgba(53, 112, 229, .18);
  stroke: #356fe5;
  stroke-width: 2;
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
  font-size: 12px;
}

.radar-empty span {
  color: #929db0;
  font-size: 9px;
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
  font-size: 13px;
  font-weight: 700;
}

.activity-count {
  padding: 5px 9px;
  border-radius: 999px;
  background: #f2f4f7;
  color: #667085;
  font-size: 10px;
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
  font-size: 10px;
  letter-spacing: .04em;
}

td {
  color: #58657b;
  font-size: 11px;
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
  font-size: 9px;
  font-weight: 650;
}

.status-pill {
  display: inline-flex;
  padding: 4px 8px;
  border-radius: 999px;
  background: #eef2f7;
  font-size: 9px;
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
  font-size: 9px;
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
  font-size: 11px;
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
  font-size: 19px;
}

.export-modal-header p {
  margin: 0;
  color: #8793aa;
  font-size: 11px;
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
  font-size: 23px;
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
  font-size: 11px;
}

.export-period-box strong {
  color: #244d9e;
  font-size: 12px;
}

.export-section {
  padding: 20px 22px;
}

.export-section h3 {
  margin: 0 0 11px;
  color: #344054;
  font-size: 12px;
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
  font-size: 12px;
}

.export-option span {
  color: #8793aa;
  font-size: 10px;
  line-height: 1.45;
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
  font-size: 11px;
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

  .period-select {
    width: 100%;
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
</style>
