<script setup>

import {
  ref,
  computed,
  reactive,
  onMounted
} from 'vue'

import {
  CalendarDays,
  Users,
  CheckCircle,
  TrendingUp
} from 'lucide-vue-next'

import { useLanguage } from '../../composables/useLanguage'

const { t } = useLanguage()


/* =========================================
   Monthly / Quarterly
========================================= */

const selectedPeriod = ref('MONTHLY')
const selectedItem = ref('MAR')

const selectPeriod = (period) => {

  selectedPeriod.value = period

  if (period === 'MONTHLY') {
    selectedItem.value = 'MAR'
  } else {
    selectedItem.value = 'Q1'
  }

}


/* =========================================
   Loading / Error
========================================= */

const loading = ref(false)
const error = ref(null)


/* =========================================
   Mock / Real Data Mode

   true  = ใช้ข้อมูลจำลองสำหรับทดสอบหน้าจอ
   false = เรียกข้อมูลจริงจาก Backend API
========================================= */

const USE_MOCK_DATA = true


/* =========================================
   Dashboard Data
========================================= */

/*
  ข้อมูลตรงนี้เป็นค่าเริ่มต้น

  ในอนาคต Backend จะส่งข้อมูลมา
  แล้วนำมาใส่ dashboardData
*/

const dashboardData = reactive({

  totalActivities: 0,
  totalStudents: 0,
  totalParticipants: 0,
  completionRate: 0,

  activityGrowth: [
    { month: 'JAN', count: 0 },
    { month: 'FEB', count: 0 },
    { month: 'MAR', count: 0 },
    { month: 'APR', count: 0 },
    { month: 'MAY', count: 0 },
    { month: 'JUN', count: 0 },
    { month: 'JUL', count: 0 },
    { month: 'AUG', count: 0 },
    { month: 'SEP', count: 0 },
    { month: 'OCT', count: 0 },
    { month: 'NOV', count: 0 },
    { month: 'DEC', count: 0 }
  ],

  skills: [
    {
      name: 'CRITICAL THINKING',
      percentage: 0
    },
    {
      name: 'COMMUNICATION',
      percentage: 0
    },
    {
      name: 'LEADERSHIP',
      percentage: 0
    }
  ]

})


/* =========================================
   Mock Data

   โครงสร้างเหมือนข้อมูลที่ Backend ควรส่งมา
   เพื่อให้ตอนต่อ Database จริงไม่ต้องแก้หน้า UI
========================================= */

const loadMockData = () => {

  dashboardData.totalActivities = 48
  dashboardData.totalStudents = 1260
  dashboardData.totalParticipants = 842
  dashboardData.completionRate = 87

  dashboardData.activityGrowth = [
    { month: 'JAN', count: 4 },
    { month: 'FEB', count: 7 },
    { month: 'MAR', count: 12 },
    { month: 'APR', count: 8 },
    { month: 'MAY', count: 15 },
    { month: 'JUN', count: 10 },
    { month: 'JUL', count: 18 },
    { month: 'AUG', count: 14 },
    { month: 'SEP', count: 20 },
    { month: 'OCT', count: 16 },
    { month: 'NOV', count: 23 },
    { month: 'DEC', count: 19 }
  ]

  dashboardData.skills = [
    {
      name: 'CRITICAL THINKING',
      percentage: 82
    },
    {
      name: 'COMMUNICATION',
      percentage: 76
    },
    {
      name: 'LEADERSHIP',
      percentage: 68
    }
  ]

}


/* =========================================
   Fetch Dashboard API
========================================= */

const fetchDashboard = async () => {

  loading.value = true
  error.value = null

  try {

    const response = await fetch(
      'http://localhost:3000/api/admin/dashboard'
    )

    if (!response.ok) {
      throw new Error('Cannot load dashboard data')
    }

    const data = await response.json()


    /*
      เอาข้อมูลจาก Backend
      มาใส่ Dashboard
    */

    dashboardData.totalActivities =
      data.totalActivities ?? 0

    dashboardData.totalStudents =
      data.totalStudents ?? 0

    dashboardData.totalParticipants =
      data.totalParticipants ?? 0

    dashboardData.completionRate =
      data.completionRate ?? 0


    if (Array.isArray(data.activityGrowth)) {
      dashboardData.activityGrowth =
        data.activityGrowth
    }


    if (Array.isArray(data.skills)) {
      dashboardData.skills =
        data.skills
    }


  } catch (err) {

    console.error(
      'Dashboard API Error:',
      err
    )

    error.value = err.message

  } finally {

    loading.value = false

  }

}


/* =========================================
   โหลดข้อมูลเมื่อเข้าหน้า Dashboard
========================================= */

onMounted(() => {

  if (USE_MOCK_DATA) {
    loadMockData()
  } else {
    fetchDashboard()
  }

})


/* =========================================
   Quarterly
========================================= */

const getActivityCount = (index) => {
  return Number(dashboardData.activityGrowth[index]?.count ?? 0)
}

const quarterlyData = computed(() => [

  {
    month: 'Q1',
    count:
      getActivityCount(0) +
      getActivityCount(1) +
      getActivityCount(2)
  },

  {
    month: 'Q2',
    count:
      getActivityCount(3) +
      getActivityCount(4) +
      getActivityCount(5)
  },

  {
    month: 'Q3',
    count:
      getActivityCount(6) +
      getActivityCount(7) +
      getActivityCount(8)
  },

  {
    month: 'Q4',
    count:
      getActivityCount(9) +
      getActivityCount(10) +
      getActivityCount(11)
  }

])


/* =========================================
   Chart Data
========================================= */

const chartData = computed(() => {

  if (
    selectedPeriod.value === 'QUARTERLY'
  ) {

    return quarterlyData.value

  }

  return dashboardData.activityGrowth

})


/* =========================================
   หาค่าสูงสุดของกราฟ
========================================= */

const maxActivity = computed(() => {

  return Math.max(
    ...chartData.value.map(
      item => item.count
    ),
    1
  )

})


/* =========================================
   Y Axis Scale

   ปรับช่วงตัวเลขอัตโนมัติตามข้อมูลจริง
========================================= */

const yAxisStep = computed(() => {

  const max = maxActivity.value

  if (max <= 10) return 2
  if (max <= 25) return 5
  if (max <= 50) return 10
  if (max <= 100) return 20

  return Math.ceil(max / 5 / 10) * 10

})

const yAxisMax = computed(() => {

  return Math.max(
    yAxisStep.value * 5,
    Math.ceil(maxActivity.value / yAxisStep.value) * yAxisStep.value
  )

})

const yAxisTicks = computed(() => {

  const ticks = []

  for (let value = yAxisMax.value; value >= 0; value -= yAxisStep.value) {
    ticks.push(value)
  }

  return ticks

})


/* =========================================
   Summary Cards
========================================= */

const summaryCards = computed(() => [

  {
    title: t.value.adminDashboard.activities,
    value: dashboardData.totalActivities,
    icon: CalendarDays,
    type: 'blue'
  },

  {
    title: t.value.adminDashboard.students,
    value: dashboardData.totalStudents,
    icon: Users,
    type: 'blue'
  },

  {
    title: t.value.adminDashboard.participants,
    value: dashboardData.totalParticipants,
    icon: TrendingUp,
    type: 'green'
  },

  {
    title: t.value.adminDashboard.completionRate,
    value: `${dashboardData.completionRate}%`,
    icon: CheckCircle,
    type: 'orange'
  }

])


/* =========================================
   Average Skill
========================================= */

const averageSkill = computed(() => {

  if (
    dashboardData.skills.length === 0
  ) {
    return 0
  }


  const total =
    dashboardData.skills.reduce(
      (sum, skill) =>
        sum + skill.percentage,
      0
    )


  return Math.round(
    total /
    dashboardData.skills.length
  )

})


/* =========================================
   Skill Translation
========================================= */

const skillLabel = (name) => {

  const skills = {
    'CRITICAL THINKING': t.value.adminDashboard.criticalThinking,
    'COMMUNICATION': t.value.adminDashboard.communication,
    'LEADERSHIP': t.value.adminDashboard.leadership
  }

  return skills[name] || name

}

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
            {{ t.adminDashboard.activityGrowthDescription }}
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
                    :title="`${item.month}: ${item.count}`"
                  ></div>

                </div>

              </div>

            </div>


            <div class="x-axis-labels">

              <span
                v-for="item in chartData"
                :key="`label-${item.month}`"
                :class="{
                  'selected-month': item.month === selectedItem
                }"
                @click="selectedItem = item.month"
              >
                {{ item.month }}
              </span>

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
            {{ t.adminDashboard.skillDescription }}
          </p>

        </div>

      </div>


      <div class="skill-content">

        <!-- Skill List -->

        <div class="skill-list">

          <div
            v-for="skill in dashboardData.skills"
            :key="skill.name"
            class="skill-item"
          >

            <div class="skill-info">

              <span>
                {{ skillLabel(skill.name) }}
              </span>

              <strong>
                {{ skill.percentage }}%
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

  font-size: 25px;
  font-weight: 800;

  color: #1d3268;
}

.dashboard-header p {
  margin: 6px 0 0;

  font-size: 14px;

  color: #8da0bd;
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

  font-size: 13px;

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

  font-size: 20px;

  font-weight: 800;

  color: #1d3268;
}


.card-header p {
  margin: 6px 0 0;

  font-size: 13px;

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

  font-size: 11px;

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

  font-size: 10px;
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

  font-size: 10px;
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


.x-axis-labels span {
  flex: 1 1 0;

  min-width: 45px;

  text-align: center;

  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;

  color: #9cacbf;

  cursor: pointer;
}


.x-axis-labels span:hover {
  color: #3264ed;
}


.x-axis-labels span.selected-month {
  color: #3264ed;
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
  font-size: 12px;

  font-weight: 800;

  letter-spacing: 0.4px;

  color: #31508f;
}


.skill-info strong {
  font-size: 12px;

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

  font-size: 10px;

  font-weight: 700;

  color: #9aa9be;
}


/* =========================
   Status
========================= */

.system-status {
  padding: 28px 0 10px;

  text-align: center;

  font-size: 10px;

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