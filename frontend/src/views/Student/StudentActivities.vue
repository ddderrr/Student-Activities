<script setup>

import {
  ref,
  computed,
  onMounted,
  onBeforeUnmount,
  inject,
  watch
} from 'vue'

import {
  Search,
  Building2,
  Globe2,
  SlidersHorizontal,
  ChevronRight,
  ChevronDown,
  ExternalLink,
  FileText
} from 'lucide-vue-next'

import {
  API_BASE,
  studentHeaders
} from '../../constants/currentStudent'

import {
  PARTICIPANT_SKILLS,
  STAFF_SKILLS
} from '../../constants/activitySkills'

import {
  useRoute,
  useRouter
} from 'vue-router'


const route = useRoute()
const router = useRouter()


/* =====================================================
   Search
   รับค่าจาก StudentLayout.vue
===================================================== */

const searchText = inject(
  'studentSearch',
  ref('')
)


/* =====================================================
   Filter Date
===================================================== */

const showDateFilter = ref(false)
const selectedDate = ref('')

const filterWrapper = ref(null)


const clearDateFilter = () => {
  selectedDate.value = ''
}


/* =====================================================
   Click Outside Filter
===================================================== */

const closeFilterOnOutside = (event) => {

  if (
    showDateFilter.value &&
    filterWrapper.value &&
    !filterWrapper.value.contains(event.target)
  ) {
    showDateFilter.value = false
  }

}


/* =====================================================
   จำนวน Activity ที่แสดง
===================================================== */

const visibleCount = ref(5)

const loadMore = () => {
  visibleCount.value += 5
}


/* =====================================================
   Loading / Error
===================================================== */

const loading = ref(false)
const error = ref(null)


/* =====================================================
   Activity Data

   สำคัญ:
   My Activities ต้องเป็นของ Student ที่ login อยู่เท่านั้น

   ตอนนี้เป็น Mock Data ของ Student คนเดียว
   ภายหลัง Backend ควรส่งเฉพาะข้อมูลของผู้ใช้ปัจจุบัน
===================================================== */

const activities = ref([])


/* =====================================================
   แปลงข้อมูลจาก GET /api/student/me/activities
   (กิจกรรมคณะ + กิจกรรมภายนอกที่อนุมัติแล้ว)
===================================================== */

const SKILL_LABELS = Object.fromEntries(
  [...STAFF_SKILLS, ...PARTICIPANT_SKILLS].map(
    skill => [skill.key, skill.label]
  )
)

const STATUS_LABELS = {
  active: 'Active',
  completed: 'Completed',
  cancelled: 'Cancelled',
  approved: 'Approved'
}

const toActivityView = (item, student) => {

  const isExternal =
    item.source === 'external_activity'

  return {
    key: `${item.source}-${item.id}`,
    id: item.id,
    source: item.source,
    sourceLabel: isExternal
      ? 'External Activity'
      : 'Faculty Activity',
    title: item.title,
    description: item.description || '',
    studentName:
      `${student.first_name} ${student.last_name}`,
    studentId: student.student_id,
    status: item.status,
    statusLabel:
      STATUS_LABELS[item.status] || item.status,
    date: String(item.start_at).slice(0, 10),
    endDate: String(item.end_at).slice(0, 10),
    category: item.activity_type,
    organizer: item.organizer,
    location: item.location,
    role: item.role === 'organizer'
      ? 'Organizer'
      : 'Participant',
    skills: Object.entries(item.skills || {}).map(
      ([key, level]) => ({
        key,
        label: SKILL_LABELS[key] || key,
        level
      })
    ),
    evidenceUrl: item.evidence_url
      ? `${API_BASE}${item.evidence_url}`
      : null
  }

}

const SUBMISSION_STATUS_LABELS = {
  pending: 'Pending',
  approved: 'Approved',
  rejected: 'Rejected'
}

// GET /api/student/me/external-activities (ทุกสถานะ)
const toSubmissionView = (item) => ({
  key: `submission-${item.id}`,
  id: item.id,
  source: 'submission',
  sourceLabel: 'External Activity',
  title: item.title,
  description: item.description || '',
  studentName:
    `${item.student.first_name} ${item.student.last_name}`,
  studentId: item.student_id,
  status: item.status,
  statusLabel: SUBMISSION_STATUS_LABELS[item.status] || item.status,
  date: item.start_date,
  endDate: item.end_date,
  category: item.activity_type,
  organizer: item.organization,
  location: item.location,
  role: item.role === 'organizer'
    ? 'Organizer'
    : 'Participant',
  skills: Object.entries(item.skills || {}).map(
    ([key, level]) => ({
      key,
      label: SKILL_LABELS[key] || key,
      level
    })
  ),
  evidenceUrl: `${API_BASE}${item.evidence.url}`,
  rejectReason: item.reject_reason
})

const submissions = ref([])

const dateRangeText = (activity) => {

  return activity.date === activity.endDate
    ? activity.date
    : `${activity.date} – ${activity.endDate}`

}


/* =====================================================
   Source Tabs (All / Faculty / External)
===================================================== */

const sourceFilter = ref('all')

const SOURCE_TABS = [
  { value: 'all', label: 'All' },
  { value: 'activity', label: 'Faculty Activities' },
  { value: 'external_activity', label: 'External Activities' },
  { value: 'submissions', label: 'My Submissions' }
]


/* =====================================================
   My Submissions: status filter
===================================================== */

const submissionStatus = ref('all')

const SUBMISSION_STATUS_TABS = [
  { value: 'all', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' }
]

const submissionStatusCounts = computed(() => {

  const counts = {
    all: submissions.value.length,
    pending: 0,
    approved: 0,
    rejected: 0
  }

  for (const item of submissions.value) {
    counts[item.status] += 1
  }

  return counts

})

const sourceCounts = computed(() => {

  const counts = {
    all: activities.value.length,
    activity: 0,
    external_activity: 0,
    submissions: submissions.value.length
  }

  for (const activity of activities.value) {
    counts[activity.source] += 1
  }

  return counts

})


/* =====================================================
   Search + Date Filter
===================================================== */

const filteredActivities = computed(() => {

  const keyword =
    searchText.value
      .trim()
      .toLowerCase()


  const baseList =
    sourceFilter.value === 'submissions'
      ? submissions.value.filter(
        item =>
          submissionStatus.value === 'all' ||
          item.status === submissionStatus.value
      )
      : activities.value


  return baseList.filter(
    activity => {

      const matchSearch =
        !keyword ||

        [
          activity.title,
          activity.description,
          activity.category,
          activity.organizer,
          activity.location
        ].some(
          value =>
            String(value || '')
              .toLowerCase()
              .includes(keyword)
        )


      // วันที่เลือกอยู่ในช่วงวันเริ่ม-วันสิ้นสุดของกิจกรรม
      const matchDate =
        !selectedDate.value ||
        (
          activity.date <= selectedDate.value &&
          selectedDate.value <= activity.endDate
        )


      const matchSource =
        sourceFilter.value === 'all' ||
        sourceFilter.value === 'submissions' ||
        activity.source === sourceFilter.value


      return (
        matchSearch &&
        matchDate &&
        matchSource
      )

    }
  )

})


/* =====================================================
   Displayed Activities
===================================================== */

const displayedActivities = computed(() => {

  return filteredActivities.value.slice(
    0,
    visibleCount.value
  )

})


const hasMoreActivities = computed(() => {

  return (
    visibleCount.value <
    filteredActivities.value.length
  )

})


/* =====================================================
   Details Modal
===================================================== */

const selectedActivity = ref(null)


const viewDetails = (activity) => {

  selectedActivity.value =
    activity

}


const closeDetails = () => {

  selectedActivity.value =
    null

}


/* =====================================================
   เปิด Modal จาก Notification

   StudentLayout.vue จะส่ง:
   /student/activities?open=ACTIVITY_ID
===================================================== */

const openActivityFromNotification = async () => {

  const activityId =
    Number(route.query.open)


  if (!activityId) {
    return
  }


  const activity =
    activities.value.find(
      item =>
        item.id === activityId
    )


  if (activity) {

    selectedActivity.value =
      activity

  }


  /*
    เปิด Modal แล้วล้าง ?open=...
    เพื่อให้ URL กลับมาสะอาด
  */
  await router.replace({
    path: '/student/activities',
    query: route.query.tab
      ? { tab: route.query.tab }
      : {}
  })

}


/*
  watch ช่วยให้กด Notification ได้
  แม้ตอนนี้อยู่หน้า /student/activities อยู่แล้ว
*/
const selectSourceTab = (value) => {

  sourceFilter.value = value

  // เก็บแท็บไว้ใน URL เพื่อให้ refresh แล้วยังอยู่แท็บเดิม
  router.replace({
    query: {
      ...route.query,
      tab: value === 'all' ? undefined : value
    }
  })

}


watch(
  () => route.query.tab,

  (tab) => {
    sourceFilter.value =
      SOURCE_TABS.some(item => item.value === tab)
        ? tab
        : 'all'
  },

  {
    immediate: true
  }
)


watch(
  () => route.query.open,

  () => {
    openActivityFromNotification()
  },

  {
    immediate: true
  }
)


/* =====================================================
   Backend API

   ตอน Backend พร้อม:
   GET /api/student/me/activities

   ควรให้ Backend ส่งเฉพาะ Activity
   ของ Student ที่ login อยู่
===================================================== */

const fetchActivities = async () => {

  loading.value = true
  error.value = null

  try {

    const [response, submissionsResponse] =
      await Promise.all([
        fetch(
          `${API_BASE}/api/student/me/activities`,
          {
            headers: studentHeaders()
          }
        ),
        fetch(
          `${API_BASE}/api/student/me/external-activities`,
          {
            headers: studentHeaders()
          }
        )
      ])


    if (!response.ok || !submissionsResponse.ok) {

      throw new Error(
        'Cannot load activities'
      )

    }


    const data =
      await response.json()

    const submissionsData =
      await submissionsResponse.json()


    activities.value =
      data.activities.map(
        item => toActivityView(item, data.student)
      )

    submissions.value =
      submissionsData.external_activities.map(
        toSubmissionView
      )


    /*
      ถ้ามาจาก Notification
      รอข้อมูลจาก API เสร็จแล้วค่อยเปิด Modal
    */
    await openActivityFromNotification()

  } catch (err) {

    console.error(
      'Activity API Error:',
      err
    )

    error.value =
      err.message

  } finally {

    loading.value =
      false

  }

}


/* =====================================================
   Lifecycle
===================================================== */

onMounted(() => {

  document.addEventListener(
    'click',
    closeFilterOnOutside
  )


  fetchActivities()

})


onBeforeUnmount(() => {

  document.removeEventListener(
    'click',
    closeFilterOnOutside
  )

})

</script>


<template>

  <div class="student-page">


    <!-- =================================================
         Content
    ================================================== -->

    <main class="content">


      <!-- =================================================
           Header
      ================================================== -->

      <section class="page-header">

        <div>

          <h1>
            My Activities
          </h1>

          <p>
            Faculty activities you joined and approved external activities.
          </p>

        </div>


        <div
          class="pending-card"
          data-testid="total-activities"
        >

          <strong>
            {{ sourceCounts.all }}
          </strong>

          <span>
            TOTAL ACTIVITIES
          </span>

        </div>

      </section>


      <!-- =================================================
           Tabs / Filter
      ================================================== -->

      <section class="tabs-row">

        <div class="tabs">

          <button
            v-for="tab in SOURCE_TABS"
            :key="tab.value"
            class="tab"
            :class="{ active: sourceFilter === tab.value }"
            type="button"
            :data-source="tab.value"
            @click="selectSourceTab(tab.value)"
          >
            {{ tab.label }}
            <span class="tab-count">
              {{ sourceCounts[tab.value] }}
            </span>
          </button>

        </div>


        <div
          ref="filterWrapper"
          class="filter-wrapper"
        >

          <button
            class="filter-btn"
            type="button"
            @click.stop="
              showDateFilter =
              !showDateFilter
            "
          >

            <SlidersHorizontal
              :size="15"
            />

            Filter By Date

          </button>


          <!-- Date Filter -->

          <div
            v-if="showDateFilter"
            class="date-filter"
            @click.stop
          >

            <input
              v-model="selectedDate"
              type="date"
            />


            <button
              v-if="selectedDate"
              type="button"
              @click="clearDateFilter"
            >
              Clear
            </button>

          </div>

        </div>

      </section>


      <!-- =================================================
           My Submissions: status filter
      ================================================== -->

      <div
        v-if="sourceFilter === 'submissions'"
        class="submission-status-tabs"
        role="tablist"
      >

        <button
          v-for="tab in SUBMISSION_STATUS_TABS"
          :key="tab.value"
          type="button"
          role="tab"
          :class="{ active: submissionStatus === tab.value }"
          :aria-selected="submissionStatus === tab.value"
          :data-status="tab.value"
          @click="submissionStatus = tab.value"
        >
          {{ tab.label }}
          <span>{{ submissionStatusCounts[tab.value] }}</span>
        </button>

      </div>


      <!-- =================================================
           Loading
      ================================================== -->

      <div
        v-if="loading"
        class="message"
      >
        Loading activities...
      </div>


      <!-- =================================================
           Error
      ================================================== -->

      <div
        v-else-if="error"
        class="message error"
      >
        {{ error }}
      </div>


      <!-- =================================================
           Activities
      ================================================== -->

      <section
        v-else
        class="activities-list"
      >

        <div
          v-for="activity in displayedActivities"
          :key="activity.key"
          class="activity-card"
          :data-source="activity.source"
          :data-id="activity.id"
        >

          <!-- Avatar -->

          <div
            class="avatar"
            :class="{ external: activity.source !== 'activity' }"
          >

            <Globe2
              v-if="activity.source !== 'activity'"
              :size="19"
            />

            <Building2
              v-else
              :size="19"
            />

          </div>


          <!-- Activity Info -->

          <div class="activity-info">

            <div class="title-row">

              <h3>
                {{ activity.title }}
              </h3>

              <span
                class="source-badge"
                :class="activity.source"
              >
                {{ activity.sourceLabel }}
              </span>

            </div>

            <p>
              {{ activity.description || activity.category }}
            </p>


            <small>

              {{ activity.organizer }}

              •

              {{ activity.role }}

            </small>


            <small
              v-if="activity.status === 'rejected' && activity.rejectReason"
              class="reject-line"
            >
              เหตุผลที่ไม่อนุมัติ: {{ activity.rejectReason }}
            </small>

          </div>


          <!-- Right -->

          <div class="activity-meta">

            <span class="activity-date">
              {{ dateRangeText(activity) }}
            </span>


            <span
              class="status"
              :class="activity.status"
            >
              {{ activity.statusLabel }}
            </span>


            <button
              class="details-btn"
              type="button"
              @click="
                viewDetails(activity)
              "
            >
              DETAILS
            </button>


            <button
              class="arrow-btn"
              type="button"
              aria-label="View activity details"
              @click="
                viewDetails(activity)
              "
            >
              <ChevronRight
                :size="17"
              />
            </button>

          </div>

        </div>


        <!-- ไม่มีข้อมูล -->

        <div
          v-if="
            displayedActivities.length
            === 0
          "
          class="empty-state"
        >

          <Search :size="28" />

          <h3>
            No activities found
          </h3>

          <p>
            {{
              activities.length
                ? 'Try another activity name or date.'
                : sourceFilter === 'submissions'
                  ? 'No external activity submissions yet.'
                  : 'No faculty or approved external activities yet.'
            }}
          </p>

        </div>

      </section>


      <!-- =================================================
           Load More
      ================================================== -->

      <div
        v-if="hasMoreActivities"
        class="load-more"
      >

        <button
          type="button"
          @click="loadMore"
        >

          Load More Activities

          <ChevronDown :size="16" />

        </button>

      </div>

    </main>


    <!-- =================================================
         Activity Details Modal
    ================================================== -->

    <div
      v-if="selectedActivity"
      class="modal-overlay"
      @click.self="closeDetails"
    >

      <div class="details-modal">


        <!-- Modal Header -->

        <div class="modal-header">

          <div>

            <h2>
              {{ selectedActivity.title }}
            </h2>

            <p>
              {{ selectedActivity.studentName }}

              (ID:
              {{ selectedActivity.studentId }})
            </p>

          </div>


          <button
            class="close-btn"
            type="button"
            aria-label="Close details"
            @click="closeDetails"
          >
            ×
          </button>

        </div>


        <!-- Modal Content -->

        <div class="modal-grid">


          <!-- =========================
               LEFT
          ========================== -->

          <div class="modal-left">


            <!-- Activity Details -->

            <section class="detail-card">

              <h3>
                Activity Details
              </h3>

              <div class="detail-divider">
              </div>


              <div class="detail-info-grid">

                <div>

                  <span class="detail-label">
                    CATEGORY
                  </span>

                  <p>
                    {{
                      selectedActivity.category
                      || '-'
                    }}
                  </p>

                </div>


                <div>

                  <span class="detail-label">
                    DATE
                  </span>

                  <p>
                    {{ dateRangeText(selectedActivity) }}
                  </p>

                </div>


                <div>

                  <span class="detail-label">
                    SOURCE
                  </span>

                  <p>
                    {{ selectedActivity.sourceLabel }}
                  </p>

                </div>


                <div>

                  <span class="detail-label">
                    ROLE
                  </span>

                  <p>
                    {{ selectedActivity.role }}
                  </p>

                </div>


                <div>

                  <span class="detail-label">
                    LOCATION
                  </span>

                  <p>
                    {{ selectedActivity.location || '-' }}
                  </p>

                </div>


                <div>

                  <span class="detail-label">
                    ORGANIZER
                  </span>

                  <p>
                    {{
                      selectedActivity.organizer
                      || '-'
                    }}
                  </p>

                </div>

              </div>

            </section>


            <!-- Reflection -->

            <section class="detail-card">

              <h3>
                {{
                  selectedActivity.source === 'activity'
                    ? 'Activity Description'
                    : 'Student Reflection'
                }}
              </h3>


              <div class="reflection-text">

                {{
                  selectedActivity.description
                  || 'No description provided.'
                }}

              </div>


              <a
                v-if="selectedActivity.evidenceUrl"
                class="evidence-link"
                :href="selectedActivity.evidenceUrl"
                target="_blank"
                rel="noopener"
              >
                <FileText :size="13" />
                View evidence
                <ExternalLink :size="11" />
              </a>

            </section>


            <!-- Skills -->

            <section class="detail-card">

              <h3>
                {{
                  selectedActivity.source === 'activity'
                    ? 'Skills'
                    : 'Skill Mapping'
                }}
              </h3>


              <div
                v-if="
                  selectedActivity.skills &&
                  selectedActivity.skills.length
                "
                class="skills"
              >

                <span
                  v-for="
                    skill
                    in
                    selectedActivity.skills
                  "
                  :key="skill.key"
                  class="skill"
                >
                  {{ skill.label }} · Level {{ skill.level }}
                </span>

              </div>


              <p
                v-else
                class="no-data"
              >
                No related skills.
              </p>

            </section>

          </div>


          <!-- =========================
               RIGHT
          ========================== -->

          <div class="modal-right">



            <!-- Current Status -->

            <section
              class="status-detail-card"
              :class="selectedActivity.status"
            >

              <span class="detail-label">
                CURRENT STATUS
              </span>

              <div class="big-status">

                <span class="status-symbol">
                  {{
                    ['cancelled', 'rejected'].includes(selectedActivity.status)
                      ? '✕'
                      : selectedActivity.status === 'pending'
                        ? '◷'
                        : selectedActivity.status === 'active'
                          ? '●'
                          : '✓'
                  }}
                </span>

                {{ selectedActivity.statusLabel }}

              </div>

            </section>


            <!-- Status Message -->

            <section class="detail-card">

              <h3>
                {{ selectedActivity.sourceLabel }}
              </h3>


              <div
                v-if="selectedActivity.status === 'pending'"
                class="
                  status-message
                  pending-message
                "
              >
                <strong>
                  Waiting for Review
                </strong>
                <p>
                  This submission is waiting for
                  administrator review.
                </p>
              </div>


              <div
                v-else-if="selectedActivity.status === 'rejected'"
                class="
                  status-message
                  rejected-message
                "
              >
                <strong>
                  Activity Not Approved
                </strong>
                <p data-testid="reject-reason">
                  {{
                    selectedActivity.rejectReason
                    || 'This activity was not approved.'
                  }}
                </p>
              </div>


              <div
                v-else-if="selectedActivity.source !== 'activity'"
                class="
                  status-message
                  approved-message
                "
              >
                <strong>
                  Approved by Administrator
                </strong>
                <p>
                  This external activity and your
                  Skill Mapping were reviewed and approved.
                </p>
              </div>


              <div
                v-else-if="selectedActivity.status === 'cancelled'"
                class="
                  status-message
                  rejected-message
                "
              >
                <strong>
                  Activity Cancelled
                </strong>
                <p>
                  This faculty activity has been cancelled.
                </p>
              </div>


              <div
                v-else
                class="
                  status-message
                  approved-message
                "
              >
                <strong>
                  {{
                    selectedActivity.status === 'completed'
                      ? 'Activity Completed'
                      : 'Registered'
                  }}
                </strong>
                <p>
                  You are listed as a
                  {{ selectedActivity.role.toLowerCase() }}
                  in this faculty activity.
                </p>
              </div>

            </section>

          </div>

        </div>

      </div>

    </div>

  </div>

</template>


<style scoped>

/* =====================================================
   Page
===================================================== */

.student-page {
  width: 100%;

  min-height: 100vh;

  background: #f5f7fb;
}


/* =====================================================
   Content
===================================================== */

.content {
  padding: 30px;
}


/* =====================================================
   Header
===================================================== */

.page-header {
  display: flex;

  justify-content: space-between;
  align-items: flex-start;

  margin-bottom: 22px;
}


.page-header h1 {
  margin: 0;

  font-size: 28px;
  font-weight: 700;

  color: #1c2434;
}


.page-header p {
  margin-top: 8px;

  color: #7e8796;

  font-size: 14px;
}


/* =====================================================
   Pending Counter
===================================================== */

.pending-card {
  width: 110px;
  height: 78px;

  display: flex;

  flex-direction: column;

  align-items: center;
  justify-content: center;

  background: #eef1ff;

  border-radius: 10px;
}


.pending-card strong {
  font-size: 25px;

  color: #102c8f;
}


.pending-card span {
  margin-top: 4px;

  font-size: 9px;

  letter-spacing: 0.7px;

  color: #6b7280;
}


/* =====================================================
   Tabs / Filter
===================================================== */

.tabs-row {
  position: relative;

  display: flex;

  justify-content: space-between;
  align-items: flex-end;

  margin-bottom: 22px;

  border-bottom: 1px solid #dfe3ea;
}


.tabs {
  display: flex;

  gap: 22px;
}


.tab:not(.active) {
  border-bottom-color: transparent;

  color: #7e8796;

  font-weight: 500;
}


.tab-count {
  margin-left: 4px;

  padding: 1px 6px;

  border-radius: 10px;

  background: #eef1ff;

  font-size: 10px;
}


.tab {
  padding: 0 0 13px;

  border: none;

  border-bottom:
    2px solid #1e45c8;

  background: none;

  color: #1235a3;

  font-weight: 600;

  cursor: pointer;
}


.filter-wrapper {
  position: relative;
}


.filter-btn {
  display: flex;

  align-items: center;

  gap: 6px;

  margin-bottom: 12px;

  border: none;

  background: none;

  color: #656e7d;

  cursor: pointer;
}


.date-filter {
  position: absolute;

  top: 38px;
  right: 0;

  z-index: 50;

  display: flex;

  gap: 8px;

  padding: 12px;

  background: white;

  border: 1px solid #e0e4eb;

  border-radius: 8px;

  box-shadow:
    0 6px 20px
    rgba(30, 40, 70, 0.12);
}


.date-filter input {
  padding: 7px;

  border: 1px solid #dce1e8;

  border-radius: 6px;

  color: #303846;

  background: white;
}


.date-filter button {
  border: none;

  background: transparent;

  color: #355ae8;

  cursor: pointer;
}


/* =====================================================
   Activities
===================================================== */

.activities-list {
  display: flex;

  flex-direction: column;

  gap: 15px;
}


.activity-card {
  min-height: 92px;

  display: flex;

  align-items: center;

  padding: 18px 22px;

  background: white;

  border: 1px solid #e9ebef;

  border-radius: 12px;

  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease;
}


.activity-card:hover {
  transform: translateY(-1px);

  box-shadow:
    0 4px 14px
    rgba(30, 45, 80, 0.05);
}


.avatar {
  width: 38px;
  height: 38px;

  display: flex;

  align-items: center;
  justify-content: center;

  flex-shrink: 0;

  border-radius: 50%;

  background: #edf2ff;

  color: #2f62e9;
}


.activity-info {
  flex: 1;

  min-width: 0;

  margin-left: 18px;
}


.activity-info h3 {
  margin: 0 0 6px;

  font-size: 15px;

  color: #212837;
}


.activity-info p {
  margin: 0;

  font-size: 12px;

  color: #858d99;
}


.activity-info small {
  display: block;

  margin-top: 7px;

  font-size: 10px;

  color: #a0a7b2;
}


.activity-meta {
  display: flex;

  align-items: center;

  gap: 15px;

  color: #9da4af;

  font-size: 11px;
}


.activity-date {
  white-space: nowrap;
}


/* =====================================================
   Status
===================================================== */

.status {
  padding: 5px 9px;

  border-radius: 12px;

  font-size: 9px;

  font-weight: 700;

  text-transform: uppercase;
}


.status.pending {
  color: #c77d00;

  background: #fff5da;
}


.status.approved {
  color: #168c4c;

  background: #e6f8ed;
}


.status.active {
  color: #1e45c8;

  background: #eaf0ff;
}


.status.completed {
  color: #168c4c;

  background: #e6f8ed;
}


.status.cancelled {
  color: #c33f3f;

  background: #fdeaea;
}


.title-row {
  display: flex;

  align-items: center;

  flex-wrap: wrap;

  gap: 8px;

  margin-bottom: 6px;
}


.title-row h3 {
  margin: 0;
}


.source-badge {
  padding: 3px 8px;

  border-radius: 10px;

  font-size: 9px;

  font-weight: 700;

  letter-spacing: 0.3px;

  white-space: nowrap;
}


.source-badge.activity {
  color: #1e45c8;

  background: #eaf0ff;
}


.source-badge.external_activity,
.source-badge.submission {
  color: #7e10c6;

  background: #f3e8ff;
}


.submission-status-tabs {
  display: flex;

  flex-wrap: wrap;

  gap: 8px;

  margin: -8px 0 18px;
}


.submission-status-tabs button {
  padding: 6px 12px;

  border: 1px solid #dfe3ea;

  border-radius: 16px;

  background: white;

  color: #5b6472;

  font-size: 11px;

  font-weight: 600;

  cursor: pointer;
}


.submission-status-tabs button span {
  margin-left: 4px;

  color: #9aa2af;
}


.submission-status-tabs button.active {
  border-color: #1e45c8;

  background: #eef1ff;

  color: #1235a3;
}


.reject-line {
  color: #c33f3f !important;
}


.avatar.external {
  color: #7e10c6;

  background: #f3e8ff;
}


.evidence-link {
  display: inline-flex;

  align-items: center;

  gap: 5px;

  margin-top: 12px;

  color: #1e45c8;

  font-size: 11px;

  font-weight: 600;

  text-decoration: none;
}


.status.rejected {
  color: #c33f3f;

  background: #fdeaea;
}


/* =====================================================
   Details Button
===================================================== */

.details-btn {
  min-width: 78px;

  padding: 8px 15px;

  border: none;

  border-radius: 7px;

  background: #23c768;

  color: white;

  font-size: 10px;
  font-weight: 700;

  cursor: pointer;
}


.details-btn:hover {
  opacity: 0.85;
}


.arrow-btn {
  display: flex;

  align-items: center;
  justify-content: center;

  padding: 4px;

  border: none;

  background: transparent;

  color: #9da4af;

  cursor: pointer;
}


.arrow-btn:hover {
  color: #345eea;
}


/* =====================================================
   Empty
===================================================== */

.empty-state {
  padding: 65px 20px;

  display: flex;

  flex-direction: column;

  align-items: center;

  color: #929baa;

  text-align: center;
}


.empty-state h3 {
  margin: 12px 0 4px;

  color: #4c5668;
}


.empty-state p {
  margin: 0;

  font-size: 12px;
}


/* =====================================================
   Message
===================================================== */

.message {
  padding: 40px;

  text-align: center;

  color: #7c8797;
}


.message.error {
  color: #d84646;
}


/* =====================================================
   Load More
===================================================== */

.load-more {
  display: flex;

  justify-content: center;

  margin-top: 28px;
}


.load-more button {
  display: flex;

  align-items: center;

  gap: 8px;

  padding: 11px 18px;

  background: white;

  border: 1px solid #dfe3ea;

  border-radius: 8px;

  color: #1539a2;

  font-weight: 600;

  cursor: pointer;
}


/* =====================================================
   Details Modal
===================================================== */

.modal-overlay {
  position: fixed;

  inset: 0;

  z-index: 2000;

  display: flex;

  align-items: center;
  justify-content: center;

  padding: 30px;

  background:
    rgba(25, 30, 50, 0.55);

  backdrop-filter:
    blur(3px);
}


.details-modal {
  width: 100%;

  max-width: 1050px;
  max-height: 90vh;

  overflow-y: auto;

  padding: 25px;

  background: #f4f6fb;

  border-radius: 15px;

  box-shadow:
    0 20px 60px
    rgba(20, 30, 60, 0.25);
}


.modal-header {
  display: flex;

  justify-content: space-between;
  align-items: flex-start;

  margin-bottom: 22px;
}


.modal-header h2 {
  margin: 0;

  font-size: 25px;

  color: #202738;
}


.modal-header p {
  margin: 7px 0 0;

  font-size: 13px;

  color: #7c8594;
}


.close-btn {
  width: 36px;
  height: 36px;

  flex-shrink: 0;

  border: none;

  border-radius: 50%;

  background: white;

  color: #667085;

  font-size: 24px;

  cursor: pointer;
}


.close-btn:hover {
  background: #e9edf3;
}


.modal-grid {
  display: grid;

  grid-template-columns:
    minmax(0, 2fr)
    minmax(250px, 0.8fr);

  gap: 18px;
}


.modal-left,
.modal-right {
  display: flex;

  flex-direction: column;

  gap: 16px;
}


.detail-card {
  padding: 20px;

  background: white;

  border: 1px solid #e6e9ef;

  border-radius: 10px;
}


.detail-card h3 {
  margin: 0;

  font-size: 14px;

  color: #2d3440;
}


.detail-divider {
  height: 1px;

  margin: 12px 0 18px;

  background: #e8eaf0;
}


.detail-info-grid {
  display: grid;

  grid-template-columns:
    repeat(2, 1fr);

  gap: 20px;
}


.detail-label {
  display: block;

  margin-bottom: 6px;

  font-size: 8px;

  font-weight: 700;

  color: #7b8493;
}


.detail-info-grid p {
  margin: 0;

  font-size: 12px;

  color: #343b48;
}


.reflection-text {
  margin-top: 15px;

  padding-left: 13px;

  border-left:
    3px solid #8d00c4;

  font-size: 12px;

  line-height: 1.7;

  color: #697282;
}


.skills {
  display: flex;

  flex-wrap: wrap;

  gap: 8px;

  margin-top: 14px;
}


.skill {
  padding: 6px 12px;

  border-radius: 16px;

  background: #efe6ff;

  color: #7e10c6;

  font-size: 10px;

  font-weight: 600;
}


.no-data {
  color: #9aa2af;

  font-size: 11px;
}


/* =====================================================
   Status Detail
===================================================== */

.status-detail-card {
  padding: 18px;

  background: white;

  border: 1px solid #e6e9ef;

  border-top:
    3px solid #e3a229;

  border-radius: 10px;
}


.status-detail-card.approved {
  border-top-color: #20bb68;
}


.status-detail-card.completed {
  border-top-color: #20bb68;
}


.status-detail-card.active {
  border-top-color: #2f62e9;
}


.status-detail-card.cancelled {
  border-top-color: #e34d4d;
}


.status-detail-card.completed
.status-symbol {
  color: #19a95b;
}


.status-detail-card.active
.status-symbol {
  color: #2f62e9;
}


.status-detail-card.cancelled
.status-symbol {
  color: #dc4747;
}


.status-detail-card.rejected {
  border-top-color: #e34d4d;
}


.big-status {
  display: flex;

  align-items: center;

  gap: 8px;

  font-size: 14px;

  font-weight: 700;

  color: #343b48;
}


.status-symbol {
  font-size: 18px;
}


.status-detail-card.pending
.status-symbol {
  color: #e69c15;
}


.status-detail-card.approved
.status-symbol {
  color: #19a95b;
}


.status-detail-card.rejected
.status-symbol {
  color: #dc4747;
}


/* =====================================================
   Status Message
===================================================== */

.status-message {
  margin-top: 15px;

  padding: 15px;

  border-radius: 8px;
}


.status-message strong {
  font-size: 12px;
}


.status-message p {
  margin: 6px 0 0;

  font-size: 10px;

  line-height: 1.5;
}


.pending-message {
  background: #fff5dc;

  color: #a87310;
}


.approved-message {
  background: #e7f8ee;

  color: #16884a;
}


.rejected-message {
  background: #fdeaea;

  color: #be3f3f;
}


/* =====================================================
   Responsive
===================================================== */

@media (max-width: 900px) {

  .content {
    padding: 20px;
  }


  .activity-date {
    display: none;
  }

}


@media (max-width: 700px) {

  .modal-overlay {
    padding: 15px;
  }


  .modal-grid {
    grid-template-columns: 1fr;
  }


  .details-modal {
    max-height: 95vh;

    padding: 18px;
  }


  .page-header h1 {
    font-size: 23px;
  }


  .activity-card {
    align-items: flex-start;
  }


  .activity-meta {
    flex-direction: column;

    align-items: flex-end;

    gap: 8px;
  }

}


@media (max-width: 500px) {

  .detail-info-grid {
    grid-template-columns: 1fr;
  }


  .modal-header h2 {
    font-size: 20px;
  }


  .pending-card {
    width: 90px;
  }


  .activity-info small {
    display: none;
  }

}

</style>
