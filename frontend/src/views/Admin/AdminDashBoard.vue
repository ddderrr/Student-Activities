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

  /*
    ตอนนี้ Backend ยังไม่มี
    เลย comment ไว้ก่อน

    พอ Backend พร้อม
    ให้เอา // ออกได้เลย
  */

  // fetchDashboard()

})


/* =========================================
   Quarterly
========================================= */

const quarterlyData = computed(() => [

  {
    month: 'Q1',

    count:
      dashboardData.activityGrowth[0].count +
      dashboardData.activityGrowth[1].count +
      dashboardData.activityGrowth[2].count
  },

  {
    month: 'Q2',

    count:
      dashboardData.activityGrowth[3].count +
      dashboardData.activityGrowth[4].count +
      dashboardData.activityGrowth[5].count
  },

  {
    month: 'Q3',

    count:
      dashboardData.activityGrowth[6].count +
      dashboardData.activityGrowth[7].count +
      dashboardData.activityGrowth[8].count
  },

  {
    month: 'Q4',

    count:
      dashboardData.activityGrowth[9].count +
      dashboardData.activityGrowth[10].count +
      dashboardData.activityGrowth[11].count
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
   Summary Cards
========================================= */

const summaryCards = computed(() => [

  {
    title: 'Activities',
    value: dashboardData.totalActivities,
    icon: CalendarDays,
    type: 'blue'
  },

  {
    title: 'Students',
    value: dashboardData.totalStudents,
    icon: Users,
    type: 'blue'
  },

  {
    title: 'Participants',
    value: dashboardData.totalParticipants,
    icon: TrendingUp,
    type: 'green'
  },

  {
    title: 'Completion Rate',
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

</script>


<template>

  <div class="dashboard">

    <!-- =========================
         Header
    ========================== -->

    <div class="dashboard-header">

      <div>
        <h1>Dashboard</h1>

        <p>
          Overview of faculty activities and student participation
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

          <h2>Activity Growth</h2>

          <p>
            Number of activities created over time
          </p>

        </div>

        <div class="period-buttons">

          <button
              :class="{ active: selectedPeriod === 'MONTHLY' }"
              @click="selectPeriod('MONTHLY')"
            >
              MONTHLY
            </button>

            <button
              :class="{ active: selectedPeriod === 'QUARTERLY' }"
              @click="selectPeriod('QUARTERLY')"
            >
              QUARTERLY
            </button>

        </div>

      </div> <!-- ✅ เพิ่มตรงนี้ -->

      <!-- Chart -->

      <div class="chart">

          <div class="grid-line line-1"></div>
          <div class="grid-line line-2"></div>
          <div class="grid-line line-3"></div>
          <div class="grid-line line-4"></div>

          <div class="bars">

            <div
              v-for="item in chartData"
              :key="item.month"
              class="bar-wrapper"
            >

              <div class="bar-area">

                <div
                  class="bar"
                  :class="{
                    selected: item.month === selectedItem
                  }"
                  :style="{
                    height: `${(item.count / maxActivity) * 100}%`
                  }"
                ></div>

              </div>

              <span
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

    </section>


    <!-- =========================
         Skill Distribution
    ========================== -->

    <section class="card skill-card">

      <div class="card-header">

        <div>

          <h2>Faculty Skill Distribution</h2>

          <p>
            Average proficiency levels across core competencies
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
                {{ skill.name }}
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
                AVG SCORE
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

      SYSTEM STATUS:

      <span v-if="loading">
        LOADING DATA
      </span>

      <span v-else-if="error">
        WAITING FOR BACKEND
      </span>

      <span v-else>
        READY
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

  font-size: 12px;

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

  font-size: 11px;

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

  font-size: 19px;

  font-weight: 800;

  color: #1d3268;
}


.card-header p {
  margin: 6px 0 0;

  font-size: 11px;

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

  font-size: 9px;

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

.chart {
  position: relative;

  height: 240px;

  margin-top: 25px;

  overflow-x: auto;
  overflow-y: hidden;
}


.grid-line {
  position: absolute;

  left: 0;
  right: 0;

  height: 1px;

  background: #eef2f6;
}


.line-1 {
  top: 15%;
}

.line-2 {
  top: 35%;
}

.line-3 {
  top: 55%;
}

.line-4 {
  top: 75%;
}


.bars {
  position: absolute;

  left: 0;
  top: 0;
  bottom: 0;

  height: 190px;

  display: flex;
  align-items: flex-end;

  /* เปลี่ยนตรงนี้ */
  justify-content: space-between;
  gap: 25px;

  width: max(100%, 900px);

  padding: 0 20px;
  box-sizing: border-box;
}


.bar-wrapper {
  flex: 0 0 45px;

  height: 100%;

  display: flex;
  flex-direction: column;

  align-items: center;
  justify-content: flex-end;
}


.bar-area {
  height: 160px;

  width: 100%;

  display: flex;

  justify-content: center;

  align-items: flex-end;
}


.bar {
  width: 5px;

  min-height: 2px;

  border-radius: 5px 5px 0 0;

  background: #e9eef5;

  transition: height 0.3s ease;
}


.bar.selected {
  background: #3264ed;
}


.bar-wrapper span {
  margin-top: 18px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #9cacbf;
  cursor: pointer;
}

.bar-wrapper span:hover {
  color: #3264ed;
}


.bar-wrapper span.selected-month {
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
  font-size: 9px;

  font-weight: 800;

  letter-spacing: 0.4px;

  color: #31508f;
}


.skill-info strong {
  font-size: 10px;

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

  font-size: 7px;

  font-weight: 700;

  color: #9aa9be;
}


/* =========================
   Status
========================= */

.system-status {
  padding: 28px 0 10px;

  text-align: center;

  font-size: 8px;

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