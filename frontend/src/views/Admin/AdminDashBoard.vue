<script setup>
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { CalendarDays, Users, CheckCircle, TrendingUp } from 'lucide-vue-next'
import { useLanguage } from '../../composables/useLanguage'
import { API_BASE } from '../../config/api'
import { adminFetch } from '../../constants/currentAdmin'
import BranchFilterSelect from '../../components/common/BranchFilterSelect.vue'
import ActivityCalendar from '../../components/Admin/ActivityCalendar.vue'
import { ALL_BRANCHES_VALUE } from '../../constants/branches'
import {
  MONTH_LABELS,
  dashboardPeriodParams,
  selectedMonthNumbers as monthNumbersFor
} from '../../utils/dashboardPeriod'

const { t } = useLanguage()

const now = new Date()
const currentMonthLabel = MONTH_LABELS[now.getMonth()]
const currentQuarterLabel = `Q${Math.floor(now.getMonth() / 3) + 1}`

const STAFF_SKILLS = [
  ['creative_leadership', 'Creative Leadership'],
  ['innovation', 'Innovation'],
  ['entrepreneurship', 'Entrepreneurship'],
  ['promote_equality', 'Promote Equality'],
  ['academic', 'Academic'],
  ['nature_environmental', 'Nature and Environmental']
]

const PARTICIPANT_SKILLS = [
  ['arts_culture_traditions', 'Arts, Culture, and Traditions'],
  ['volunteerism', 'Volunteerism'],
  ['academics', 'Academics'],
  ['internationalization', 'Internationalization'],
  ['health_promotion', 'Health Promotion'],
  ['nature_environmental_conservation', 'Nature and Environmental Conservation']
]

const selectedPeriod = ref('MONTHLY')
const selectedItem = ref(currentMonthLabel)

// true เฉพาะตอนผู้ใช้กดเลือกเดือน/ไตรมาสใน Activity Growth chart เองเท่านั้น
// (ไม่ใช่ตอนเปิดหน้าครั้งแรก หรือตอนเปลี่ยนปี/Semester) เพื่อให้ Summary Cards
// ยังคงเป็นยอดรวมทั้ง Semester ตามที่ป้ายกำกับ "Academic Year / Semester
// Filter" ด้านบนบอกไว้ จนกว่าจะมีการ drill-down ลงเดือน/ไตรมาสจริง ๆ
const hasSelectedChartItem = ref(false)

// Dashboard history filters
// ใช้ logic เดียวกับ backend ปัจจุบัน:
// Semester 1 = JAN-JUN, Semester 2 = JUL-DEC
const selectedYear = ref(now.getFullYear())
const selectedSemester = ref('ALL')
// filter สาขา สำหรับแอดมินกลางเท่านั้น (BranchFilterSelect ซ่อนตัวเองให้แอดมินสาขา)
const selectedBranch = ref(ALL_BRANCHES_VALUE)
const selectedSkillRole = ref('participant')
const loading = ref(false)
const error = ref(null)
const activityDetails = ref([])

const dashboardData = reactive({
  totalActivities: 0,
  totalStudents: 0,
  totalParticipants: 0,
  completionRate: 0
})

const semesterMonthIndexes = computed(() => {
  if (selectedSemester.value === 'SEMESTER_1') return [0, 1, 2, 3, 4, 5]
  if (selectedSemester.value === 'SEMESTER_2') return [6, 7, 8, 9, 10, 11]
  return [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
})

const availableYears = computed(() => {
  const years = new Set()

  // ไม่แสดงปีที่มีแต่กิจกรรม cancelled
  for (const activity of activityDetails.value) {
    if (!activity.start_at || activity.status === 'cancelled') continue
    const date = new Date(activity.start_at)
    if (!Number.isNaN(date.getTime())) years.add(date.getFullYear())
  }

  // ให้ปีปัจจุบันเลือกได้เสมอ แม้ยังไม่มีกิจกรรม
  years.add(now.getFullYear())
  return [...years].sort((a, b) => b - a)
})

const semesterLabel = computed(() => {
  if (selectedSemester.value === 'SEMESTER_1') return t.value.adminDashboard.semester1
  if (selectedSemester.value === 'SEMESTER_2') return t.value.adminDashboard.semester2
  return t.value.adminDashboard.allSemesters
})

const resetSelectedItem = () => {
  hasSelectedChartItem.value = false
  const indexes = semesterMonthIndexes.value

  if (selectedPeriod.value === 'MONTHLY') {
    const currentIndex = now.getMonth()
    const preferredIndex = selectedYear.value === now.getFullYear() && indexes.includes(currentIndex)
      ? currentIndex
      : indexes[0]
    selectedItem.value = MONTH_LABELS[preferredIndex]
    return
  }

  const allowedQuarters = [...new Set(indexes.map(index => `Q${Math.floor(index / 3) + 1}`))]
  const preferredQuarter = selectedYear.value === now.getFullYear() && allowedQuarters.includes(currentQuarterLabel)
    ? currentQuarterLabel
    : allowedQuarters[0]
  selectedItem.value = preferredQuarter
}

// เดือน/ไตรมาสที่ผู้ใช้คลิกใน Activity Growth chart แปลงเป็นเลขเดือน (1-12)
// ส่งให้ backend กรองทั้ง KPI (Activities/Participants/Completion Rate) และกราฟ
// Skill Distribution ให้แคบลงเหลือแค่ช่วงที่คลิกจริง ยังไม่คลิก = ทั้ง Semester
const selectedMonthNumbers = computed(() => monthNumbersFor({
  hasSelectedChartItem: hasSelectedChartItem.value,
  period: selectedPeriod.value,
  selectedItem: selectedItem.value
}))

const periodParams = () => dashboardPeriodParams({
  year: selectedYear.value,
  semester: selectedSemester.value,
  monthNumbers: selectedMonthNumbers.value,
  branch: selectedBranch.value,
  allBranchesValue: ALL_BRANCHES_VALUE
})

const selectPeriod = (period) => {
  selectedPeriod.value = period
  resetSelectedItem()
  return refreshSummary()
}

const fetchDashboardSummary = async () => {
  const params = periodParams()

  const response = await adminFetch(`${API_BASE}/api/admin/dashboard?${params.toString()}`)
  if (!response.ok) throw new Error('Cannot load dashboard summary')

  const data = await response.json()
  dashboardData.totalActivities = data.totalActivities ?? 0
  dashboardData.totalStudents = data.totalStudents ?? 0
  dashboardData.totalParticipants = data.totalParticipants ?? 0
  dashboardData.completionRate = data.completionRate ?? 0
}

const refreshSummary = async () => {
  loading.value = true
  error.value = null
  try {
    await fetchDashboardSummary()
  } catch (err) {
    console.error('Dashboard API Error:', err)
    error.value = err.message
  } finally {
    loading.value = false
  }
}

const changeYear = () => {
  resetSelectedItem()
  return refreshSummary()
}

const changeSemester = () => {
  resetSelectedItem()
  return refreshSummary()
}

const changeBranch = () => {
  resetSelectedItem()
  return fetchDashboard()
}

const selectChartItem = (month) => {
  if (selectedItem.value === month && hasSelectedChartItem.value) return
  selectedItem.value = month
  hasSelectedChartItem.value = true
  return refreshSummary()
}

const fetchDashboard = async () => {
  loading.value = true
  error.value = null

  try {
    // Activity ทั้งหมดในครั้งเดียว: list มี status / staff_skills / participant_skills
    // อยู่แล้ว ไม่ต้องยิง /api/activities/{id} ทีละกิจกรรม
    // owned_only=true: หน้า Dashboard ไม่ควรนับกิจกรรมที่ยังไม่มีเจ้าของ
    // (major=None) เป็นสถิติของสาขาไหนสาขาหนึ่ง ต่างจากหน้า Activities list
    // ที่ยังให้แอดมินสาขาเห็น/จัดการกิจกรรมที่ยังไม่มีเจ้าของได้ตามเดิม
    //
    // "กิจกรรม" ในหน้านี้หมายถึงกิจกรรมของคณะ (Activity) เท่านั้น ไม่รวม
    // กิจกรรมภายนอกที่นักศึกษายื่นเอง แม้จะอนุมัติแล้วก็ตาม เพื่อให้ตัวเลข/
    // กราฟ/skill distribution ตรงกับหน้า Activities list และ KPI ฝั่ง
    // /api/admin/dashboard เสมอ (ก่อนหน้านี้เอามารวมกันเงียบ ๆ ทำให้ตัวเลข
    // สองหน้าไม่ตรงกัน)
    const activitiesParams = new URLSearchParams({ owned_only: 'true' })
    if (selectedBranch.value !== ALL_BRANCHES_VALUE) {
      activitiesParams.set('major', selectedBranch.value)
    }

    const activitiesResponse = await adminFetch(
      `${API_BASE}/api/activities?${activitiesParams.toString()}`
    )
    if (!activitiesResponse.ok) throw new Error('Cannot load activities')
    const activitiesPayload = await activitiesResponse.json()
    const activities = Array.isArray(activitiesPayload.activities)
      ? activitiesPayload.activities
      : []

    activityDetails.value = activities

    // ถ้าปีปัจจุบันไม่มีข้อมูลก็ยังคงเลือกได้ตามเดิม
    // Summary จะกรองตามปี + Semester ที่ผู้ใช้เลือก
    await fetchDashboardSummary()
  } catch (err) {
    console.error('Dashboard API Error:', err)
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchDashboard)

// ============================================================
// Activity Growth: นับตาม start_at ของปี/ภาคเรียนที่เลือก
// ============================================================
const monthlyActivityData = computed(() => {
  const counts = Array(12).fill(0)
  const year = Number(selectedYear.value)

  // กิจกรรม cancelled ไม่นับ ให้ตรงกับ KPI Total Activities ฝั่ง backend
  for (const activity of activityDetails.value) {
    if (!activity.start_at || activity.status === 'cancelled') continue
    const date = new Date(activity.start_at)
    if (Number.isNaN(date.getTime()) || date.getFullYear() !== year) continue
    counts[date.getMonth()] += 1
  }

  return semesterMonthIndexes.value.map(index => ({
    month: MONTH_LABELS[index],
    monthIndex: index,
    count: counts[index]
  }))
})

const quarterlyData = computed(() => {
  const quarterMap = new Map()

  for (const item of monthlyActivityData.value) {
    const quarter = `Q${Math.floor(item.monthIndex / 3) + 1}`
    quarterMap.set(quarter, (quarterMap.get(quarter) ?? 0) + item.count)
  }

  return [...quarterMap.entries()].map(([month, count]) => ({ month, count }))
})

const chartData = computed(() =>
  selectedPeriod.value === 'QUARTERLY' ? quarterlyData.value : monthlyActivityData.value
)

// Dynamic Y-axis: ไม่ล็อกไว้ที่ 10
const maxActivity = computed(() => Math.max(...chartData.value.map(item => item.count), 0))

const yAxisStep = computed(() => {
  const max = maxActivity.value
  if (max <= 10) return 2
  if (max <= 20) return 5
  if (max <= 50) return 10
  if (max <= 100) return 20
  if (max <= 250) return 50
  return Math.ceil(max / 5 / 100) * 100
})

const yAxisMax = computed(() => {
  if (maxActivity.value <= 10) return 10
  return Math.ceil(maxActivity.value / yAxisStep.value) * yAxisStep.value
})

const yAxisTicks = computed(() => {
  const ticks = []
  for (let value = yAxisMax.value; value >= 0; value -= yAxisStep.value) ticks.push(value)
  return ticks
})

// ============================================================
// Skill Distribution
// คำนวณที่ backend (GET /api/admin/dashboard/skill-distribution) ด้วยกติกาเดียวกับ
// คะแนนทักษะส่วนอื่น: ไม่นับกิจกรรม cancelled, ขอบเขตตามสิทธิ์แอดมินเหมือน KPI
// Participant และ Staff คำนวณแยกกัน ไม่มี skill ใน activity = ไม่นับเป็น 0 และไม่นำมาหาร
// ช่วงเวลา: เดียวกับ KPI (ทั้งภาคเรียนจนกว่าจะคลิกเดือน/ไตรมาสใน Activity Growth)
// ============================================================
const skillDefinitions = computed(() =>
  selectedSkillRole.value === 'participant' ? PARTICIPANT_SKILLS : STAFF_SKILLS
)

const skillDistribution = ref({ skills: [], averagePercentage: 0 })

// เปลี่ยนตัวเลือกเร็ว ๆ: ผลของคำขอเก่าต้องไม่ทับของใหม่
let skillRequest = 0

const fetchSkillDistribution = async () => {
  const request = ++skillRequest
  const params = periodParams()
  params.set('track', selectedSkillRole.value)

  try {
    const response = await adminFetch(`${API_BASE}/api/admin/dashboard/skill-distribution?${params}`)
    if (!response.ok) throw new Error('Cannot load skill distribution')
    const data = await response.json()
    if (request === skillRequest) skillDistribution.value = data
  } catch (err) {
    console.error('Skill distribution API Error:', err)
    if (request === skillRequest) skillDistribution.value = { skills: [], averagePercentage: 0 }
  }
}

watch(
  [selectedYear, selectedSemester, selectedBranch, () => selectedMonthNumbers.value.join(','), selectedSkillRole],
  fetchSkillDistribution,
  { immediate: true }
)

const displayedSkills = computed(() => {
  const byKey = new Map(skillDistribution.value.skills.map(skill => [skill.key, skill]))

  return skillDefinitions.value.map(([key, name]) => {
    const skill = byKey.get(key)

    return {
      key,
      name,
      averageLevel: skill?.averageLevel ?? null,
      percentage: skill?.percentage ?? 0,
      evidenceCount: skill?.evidenceCount ?? 0
    }
  })
})

// Average รวมเฉพาะ skill ที่มีข้อมูลจริง (คำนวณที่ backend)
const averageSkill = computed(() => skillDistribution.value.averagePercentage ?? 0)

const monthLabelMap = computed(() => ({
  JAN: t.value.adminDashboard.monthJan,
  FEB: t.value.adminDashboard.monthFeb,
  MAR: t.value.adminDashboard.monthMar,
  APR: t.value.adminDashboard.monthApr,
  MAY: t.value.adminDashboard.monthMay,
  JUN: t.value.adminDashboard.monthJun,
  JUL: t.value.adminDashboard.monthJul,
  AUG: t.value.adminDashboard.monthAug,
  SEP: t.value.adminDashboard.monthSep,
  OCT: t.value.adminDashboard.monthOct,
  NOV: t.value.adminDashboard.monthNov,
  DEC: t.value.adminDashboard.monthDec,
  Q1: t.value.adminDashboard.quarterQ1,
  Q2: t.value.adminDashboard.quarterQ2,
  Q3: t.value.adminDashboard.quarterQ3,
  Q4: t.value.adminDashboard.quarterQ4
}))

// Display-only translation for month/quarter labels.
// MONTH_LABELS / quarter strings themselves stay untranslated because they are
// also used internally for date-matching (selectedItem, chart selection, etc).
const displayLabel = (label) => monthLabelMap.value[label] || label

// ช่วงเวลาที่กราฟ Skill Distribution ใช้: ยังไม่คลิก Activity Growth = ทั้งภาคเรียน
const selectedPeriodText = computed(() =>
  hasSelectedChartItem.value
    ? `${displayLabel(selectedItem.value)} · ${semesterLabel.value} · ${selectedYear.value}`
    : `${semesterLabel.value} · ${selectedYear.value}`
)

const summaryCards = computed(() => [
  { title: t.value.adminDashboard.activities, value: dashboardData.totalActivities, icon: CalendarDays, type: 'blue' },
  { title: t.value.adminDashboard.students, value: dashboardData.totalStudents, icon: Users, type: 'blue' },
  { title: t.value.adminDashboard.participants, value: dashboardData.totalParticipants, icon: TrendingUp, type: 'green' },
  { title: t.value.adminDashboard.completionRate, value: `${dashboardData.completionRate}%`, icon: CheckCircle, type: 'orange' }
])
</script>


<template>

  <div class="dashboard">

    <!-- =========================
         Header
    ========================== -->

    <div class="dashboard-header">

      <div>
        <h1>{{ t.adminDashboard.title }}</h1>

        <p>
          {{ t.adminDashboard.subtitle }}
        </p>
      </div>

    </div>


    <!-- =========================
         Academic Year / Semester Filter
    ========================== -->

    <section class="history-filter">
      <div class="history-filter-text">
        <strong>{{ t.adminDashboard.dashboardHistory }}</strong>
        <span>{{ t.adminDashboard.dashboardHistoryDescription }}</span>
      </div>

      <div class="history-filter-controls">
        <BranchFilterSelect v-model="selectedBranch" @update:model-value="changeBranch" />

        <label class="filter-field">
          <span>{{ t.adminDashboard.academicYear }}</span>
          <select v-model.number="selectedYear" @change="changeYear">
            <option
              v-for="year in availableYears"
              :key="year"
              :value="year"
            >
              {{ year }}
            </option>
          </select>
        </label>

        <label class="filter-field">
          <span>{{ t.adminDashboard.semester }}</span>
          <select v-model="selectedSemester" @change="changeSemester">
            <option value="ALL">{{ t.adminDashboard.allSemesters }}</option>
            <option value="SEMESTER_1">{{ t.adminDashboard.semester1 }} ({{ displayLabel('JAN') }} - {{ displayLabel('JUN') }})</option>
            <option value="SEMESTER_2">{{ t.adminDashboard.semester2 }} ({{ displayLabel('JUL') }} - {{ displayLabel('DEC') }})</option>
          </select>
        </label>
      </div>
    </section>


    <!-- =========================
         Summary Cards
    ========================== -->

    <section class="summary-grid">

      <div
        v-for="card in summaryCards"
        :key="card.title"
        class="summary-card"
      >

        <div class="summary-top">

          <div
            class="summary-icon"
            :class="card.type"
          >
            <component
              :is="card.icon"
              :size="20"
            />
          </div>

        </div>

        <div class="summary-value">
          {{ card.value }}
        </div>

        <div class="summary-title">
          {{ card.title }}
        </div>

      </div>

    </section>


    <!-- =========================
         Activity Growth
    ========================== -->

        <section class="card activity-card">

      <div class="card-header">

        <div>

          <h2>{{ t.adminDashboard.activityGrowth }}</h2>

          <p>
            {{ t.adminDashboard.activityGrowthDescription }} · {{ semesterLabel }} · {{ selectedYear }}
          </p>

        </div>

        <div class="period-buttons">

          <button
              :class="{ active: selectedPeriod === 'MONTHLY' }"
              @click="selectPeriod('MONTHLY')"
            >
              {{ t.adminDashboard.monthly }}
            </button>

            <button
              :class="{ active: selectedPeriod === 'QUARTERLY' }"
              @click="selectPeriod('QUARTERLY')"
            >
              {{ t.adminDashboard.quarterly }}
            </button>

        </div>

      </div> <!-- ✅ เพิ่มตรงนี้ -->

      <!-- Chart -->

      <div class="chart-shell">

        <div class="y-axis">

          <div class="y-axis-title">
            {{ t.adminDashboard.activities }}
          </div>

          <div class="y-axis-ticks">

            <span
              v-for="tick in yAxisTicks"
              :key="tick"
            >
              {{ tick }}
            </span>

          </div>

        </div>


        <div class="chart-scroll">

          <div class="chart-content">

            <div class="plot-area">

              <div
                v-for="tick in yAxisTicks"
                :key="`grid-${tick}`"
                class="grid-line"
                :style="{
                  top: `${((yAxisMax - tick) / yAxisMax) * 100}%`
                }"
              ></div>

              <div class="bars">

                <div
                  v-for="item in chartData"
                  :key="item.month"
                  class="bar-wrapper"
                >

                  <div
                    class="bar"
                    :class="{
                      selected: item.month === selectedItem
                    }"
                    :style="{
                      height: `${(item.count / yAxisMax) * 100}%`
                    }"
                    :title="`${displayLabel(item.month)}: ${item.count}`"
                  ></div>

                </div>

              </div>

            </div>


            <div class="x-axis-labels">
              <div
                v-for="item in chartData"
                :key="`label-${item.month}`"
                class="x-axis-item"
                :class="{ 'selected-month': item.month === selectedItem }"
                @click="selectChartItem(item.month)"
              >
                <strong class="activity-count">{{ item.count }}</strong>
                <span>{{ displayLabel(item.month) }}</span>
              </div>
            </div>

          </div>

        </div>

      </div>

    </section>


    <!-- =========================
         Skill Distribution
    ========================== -->

    <section class="card skill-card">

      <div class="card-header">

        <div>
          <h2>{{ t.adminDashboard.skillDistribution }}</h2>
          <p>
            {{ t.adminDashboard.skillDescription }} · {{ selectedPeriodText }}
          </p>
        </div>

        <div class="skill-role-buttons">
          <button
            :class="{ active: selectedSkillRole === 'participant' }"
            @click="selectedSkillRole = 'participant'"
          >
            {{ t.adminDashboard.participantRole }}
          </button>
          <button
            :class="{ active: selectedSkillRole === 'staff' }"
            @click="selectedSkillRole = 'staff'"
          >
            {{ t.adminDashboard.staffRole }}
          </button>
        </div>

      </div>


      <div class="skill-content">

        <!-- Skill List -->

        <div class="skill-list">

          <div
            v-for="skill in displayedSkills"
            :key="skill.name"
            class="skill-item"
          >

            <div class="skill-info">

              <span>
                {{ skill.name }}
              </span>

              <strong>
                {{ skill.percentage }}%
                <small v-if="skill.evidenceCount > 0">({{ skill.evidenceCount }} {{ t.adminDashboard.activitiesUnit }})</small>
                <small v-else>({{ t.adminDashboard.noData }})</small>
              </strong>

            </div>


            <div class="skill-bar">

              <div
                class="skill-progress"
                :style="{
                  width: `${skill.percentage}%`
                }"
              ></div>

            </div>

          </div>

        </div>


        <!-- Average Score -->

        <div class="average-score">

          <div
            class="score-circle"
            :style="{
              background: `conic-gradient(
                #0d9d93 0deg,
                #0d9d93 ${averageSkill * 3.6}deg,
                #edf2f6 ${averageSkill * 3.6}deg,
                #edf2f6 360deg
              )`
            }"
          >

            <div class="score-inner">

              <strong>
                {{ averageSkill }}%
              </strong>

              <span>
                {{ t.adminDashboard.averageScore }}
              </span>

            </div>

          </div>

        </div>

      </div>

    </section>


    <!-- =========================
         Activity Calendar (filter สาขาแยกจากด้านบน)
    ========================== -->

    <ActivityCalendar />


    <!-- =========================
         System Status
    ========================== -->

    <div class="system-status">

      {{ t.adminDashboard.systemStatus }}:

      <span v-if="loading">
        {{ t.adminDashboard.loadingData }}
      </span>

      <span v-else-if="error">
        {{ t.adminDashboard.waitingBackend }}
      </span>

      <span v-else>
        {{ t.adminDashboard.ready }}
      </span>

    </div>

  </div>

</template>


<style scoped>

/* =========================
   Dashboard
========================= */

.dashboard {
  min-height: 100vh;

  padding: 28px 32px;

  background: #f7f8fc;
}


/* =========================
   Header
========================= */

.dashboard-header {
  margin-bottom: 24px;
}

.dashboard-header h1 {
  margin: 0;

  font-size: 27px;
  font-weight: 800;

  color: #1d3268;
}

.dashboard-header p {
  margin: 6px 0 0;

  font-size: var(--fs-body);

  color: #8da0bd;
}


/* =========================
   Dashboard History Filter
========================= */

.history-filter {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
  padding: 16px 18px;
  background: white;
  border: 1px solid #edf0f5;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(30, 60, 100, 0.04);
}

.history-filter-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.history-filter-text strong {
  font-size: var(--fs-body);
  color: #1d3268;
}

.history-filter-text span {
  font-size: var(--fs-small);
  color: #8da0bd;
}

.history-filter-controls {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-field span {
  font-size: var(--fs-caption);
  font-weight: 800;
  color: #60738f;
  letter-spacing: 0.4px;
}

.filter-field select {
  min-width: 150px;
  height: 38px;
  padding: 0 34px 0 12px;
  border: 1px solid #e2e8f0;
  border-radius: 9px;
  outline: none;
  background: #f8faff;
  color: #31508f;
  font-size: var(--fs-small);
  font-weight: 700;
  cursor: pointer;
}

.filter-field select:focus {
  border-color: #7b08c7;
  box-shadow: 0 0 0 3px rgba(123, 8, 199, 0.08);
}

/* =========================
   Summary Cards
========================= */

.summary-grid {
  display: grid;

  grid-template-columns:
    repeat(4, minmax(0, 1fr));

  gap: 18px;
}


.summary-card {
  min-height: 140px;

  padding: 20px;

  background: white;

  border: 1px solid #edf0f5;

  border-radius: 16px;

  box-shadow:
    0 2px 8px rgba(30, 60, 100, 0.04);
}


.summary-top {
  display: flex;

  justify-content: space-between;

  align-items: center;
}


.summary-icon {
  width: 36px;
  height: 36px;

  border-radius: 9px;

  display: flex;

  align-items: center;
  justify-content: center;
}


.summary-icon.blue {
  color: #315de6;

  background: #edf2ff;
}


.summary-icon.green {
  color: #0d9d93;

  background: #eaf9f7;
}


.summary-icon.orange {
  color: #f97316;

  background: #fff1e8;
}


.summary-value {
  margin-top: 15px;

  font-size: 30px;

  font-weight: 800;

  color: #213d83;
}


.summary-title {
  margin-top: 3px;

  font-size: var(--fs-body);

  color: #8da0bd;
}


/* =========================
   General Card
========================= */

.card {
  margin-top: 20px;

  padding: 25px;

  background: white;

  border: 1px solid #edf0f5;

  border-radius: 18px;

  box-shadow:
    0 2px 8px rgba(30, 60, 100, 0.04);
}


.card-header {
  display: flex;

  justify-content: space-between;

  align-items: center;
}


.card-header h2 {
  margin: 0;

  font-size: 22px;

  font-weight: 800;

  color: #1d3268;
}


.card-header p {
  margin: 6px 0 0;

  font-size: var(--fs-body);

  color: #8da0bd;
}


/* =========================
   Period Buttons
========================= */

.period-buttons {
  display: flex;

  padding: 3px;

  background: #f5f7fb;

  border-radius: 7px;
}


.period-buttons button {
  border: none;

  padding: 7px 14px;

  background: transparent;

  border-radius: 5px;

  font-size: var(--fs-small);

  font-weight: 700;

  color: #9aa8bb;

  cursor: pointer;
}


.period-buttons button.active {
  color: white;

  background: #7b08c7;
}


/* =========================
   Chart
========================= */

.chart-shell {
  display: flex;
  align-items: flex-start;
  gap: 10px;

  margin-top: 25px;
}


.y-axis {
  position: relative;

  flex: 0 0 62px;

  height: 200px;
}


.y-axis-title {
  position: absolute;

  left: -6px;
  top: 50%;

  transform: translateY(-50%) rotate(-90deg);
  transform-origin: center;

  white-space: nowrap;

  font-size: var(--fs-caption);
  font-weight: 700;

  color: #8da0bd;
}


.y-axis-ticks {
  position: absolute;

  top: 0;
  right: 0;

  width: 24px;
  height: 200px;

  display: flex;
  flex-direction: column;
  justify-content: space-between;

  transform: translateY(-5px);

  font-size: var(--fs-caption);
  font-weight: 700;

  text-align: right;

  color: #9cacbf;
}


.chart-scroll {
  flex: 1;
  min-width: 0;

  overflow-x: auto;
  overflow-y: hidden;

  padding-bottom: 4px;

  scrollbar-width: thin;
  scrollbar-color: #cfd8e5 #ffffff;
}

.chart-scroll::-webkit-scrollbar {
  height: 8px;
}

.chart-scroll::-webkit-scrollbar-track {
  background: #ffffff;
}

.chart-scroll::-webkit-scrollbar-thumb {
  background: #cfd8e5;
  border-radius: 8px;
}

.chart-scroll::-webkit-scrollbar-thumb:hover {
  background: #b6c2d4;
}


.chart-content {
  width: max(100%, 900px);
}


.plot-area {
  position: relative;

  height: 200px;

  border-bottom: 1px solid #e7edf5;
}


.grid-line {
  position: absolute;

  left: 0;
  right: 0;

  height: 1px;

  background: #eef2f6;

  pointer-events: none;
}


.bars {
  position: absolute;

  inset: 0;

  display: flex;
  align-items: flex-end;
  justify-content: space-between;

  gap: 25px;

  padding: 0 22px;
  box-sizing: border-box;
}


.bar-wrapper {
  flex: 1 1 0;

  height: 100%;

  display: flex;
  align-items: flex-end;
  justify-content: center;

  min-width: 45px;
}


.bar {
  width: 5px;

  min-height: 2px;

  border-radius: 5px 5px 0 0;

  background: #e9eef5;

  transition:
    height 0.3s ease,
    background 0.2s ease;
}


.bar.selected {
  background: #3264ed;
}


.x-axis-labels {
  display: flex;
  justify-content: space-between;

  gap: 25px;

  padding: 14px 22px 0;

  box-sizing: border-box;
}


.x-axis-item {
  flex: 1 1 0;
  min-width: 45px;
  text-align: center;
  cursor: pointer;
  color: #9cacbf;
}

.x-axis-item span {
  display: block;
  margin-top: 3px;
  font-size: var(--fs-small);
  font-weight: 700;
  letter-spacing: 0.5px;
}

.activity-count {
  display: block;
  font-size: var(--fs-small);
  font-weight: 800;
  color: #60738f;
}

.x-axis-item:hover,
.x-axis-item.selected-month,
.x-axis-item.selected-month .activity-count {
  color: #3264ed;
}


.skill-role-buttons {
  display: flex;
  padding: 3px;
  background: #f5f7fb;
  border-radius: 7px;
}

.skill-role-buttons button {
  border: none;
  padding: 7px 12px;
  background: transparent;
  border-radius: 5px;
  font-size: var(--fs-small);
  font-weight: 800;
  color: #9aa8bb;
  cursor: pointer;
}

.skill-role-buttons button.active {
  color: white;
  background: #7b08c7;
}

.skill-info strong small {
  margin-left: 5px;
  font-size: var(--fs-badge);
  font-weight: 600;
  color: #9aa8bb;
}

/* =========================
   Skills
========================= */

.skill-content {
  display: flex;

  align-items: center;

  justify-content: space-between;

  margin-top: 25px;
}


.skill-list {
  width: 60%;

  max-width: 500px;
}


.skill-item {
  margin-bottom: 22px;
}


.skill-info {
  display: flex;

  justify-content: space-between;

  align-items: center;

  margin-bottom: 7px;
}


.skill-info span {
  font-size: var(--fs-small);

  font-weight: 800;

  letter-spacing: 0.4px;

  color: #31508f;
}


.skill-info strong {
  font-size: var(--fs-small);

  color: #31508f;
}


.skill-bar {
  width: 100%;

  height: 7px;

  overflow: hidden;

  border-radius: 10px;

  background: #edf2f7;
}


.skill-progress {
  height: 100%;

  border-radius: 10px;

  background: #315de6;

  transition: width 0.3s ease;
}


/* =========================
   Average Score
========================= */

.average-score {
  width: 35%;

  display: flex;

  justify-content: center;
}


.score-circle {
  width: 135px;
  height: 135px;

  border-radius: 50%;

  display: flex;
  align-items: center;
  justify-content: center;
}


.score-inner {
  width: 105px;
  height: 105px;

  border-radius: 50%;

  background: white;

  display: flex;

  flex-direction: column;

  align-items: center;

  justify-content: center;
}


.score-inner strong {
  font-size: 30px;

  color: #1d3268;
}


.score-inner span {
  margin-top: 3px;

  font-size: var(--fs-caption);

  font-weight: 700;

  color: #9aa9be;
}


/* =========================
   Status
========================= */

.system-status {
  padding: 28px 0 10px;

  text-align: center;

  font-size: var(--fs-caption);

  font-weight: 700;

  letter-spacing: 1px;

  color: #9aa9be;
}


.system-status span {
  color: #3264ed;
}


/* =========================
   Responsive
========================= */

@media (max-width: 900px) {

  .summary-grid {
    grid-template-columns:
      repeat(2, 1fr);
  }

}


@media (max-width: 600px) {

  .history-filter {
    align-items: stretch;
    flex-direction: column;
  }

  .history-filter-controls {
    align-items: stretch;
    flex-direction: column;
  }

  .filter-field select {
    width: 100%;
  }

  .dashboard {
    padding: 20px 15px;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .card-header {
    align-items: flex-start;

    gap: 15px;

    flex-direction: column;
  }

  .skill-content {
    flex-direction: column;

    gap: 30px;
  }

  .skill-list {
    width: 100%;
  }

  .average-score {
    width: 100%;
  }

  

}

</style>