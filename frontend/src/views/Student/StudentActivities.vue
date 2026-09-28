<script setup>

import {
  ref,
  computed,
  onMounted,
  onBeforeUnmount,
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
  FileText,
  X
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

import { useLanguage } from '../../composables/useLanguage'


const route = useRoute()
const router = useRouter()

const { t } = useLanguage()


/* =====================================================
   Search
   ช่องค้นหาอยู่ใต้หัวข้อหน้า
===================================================== */

const searchText = ref('')

const clearSearch = () => {
  searchText.value = ''
}


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

const STATUS_LABELS = computed(() => ({
  active: t.value.studentActivities.statusActive,
  completed: t.value.studentActivities.statusCompleted,
  cancelled: t.value.studentActivities.statusCancelled,
  approved: t.value.studentActivities.statusApproved
}))

const toActivityView = (item, student) => {

  const isExternal =
    item.source === 'external_activity'

  return {
    key: `${item.source}-${item.id}`,
    id: item.id,
    source: item.source,
    sourceLabel: isExternal
      ? t.value.studentActivities.externalActivityLabel
      : t.value.studentActivities.facultyActivityLabel,
    title: item.title,
    description: item.description || '',
    studentName:
      `${student.first_name} ${student.last_name}`,
    studentId: student.student_id,
    status: item.status,
    statusLabel:
      STATUS_LABELS.value[item.status] || item.status,
    date: String(item.start_at).slice(0, 10),
    endDate: String(item.end_at).slice(0, 10),
    category: item.activity_type,
    organizer: item.organizer,
    location: item.location,
    role: item.role === 'organizer'
      ? t.value.studentActivities.roleOrganizer
      : t.value.studentActivities.roleParticipant,
    skills: Object.entries(item.skills || {}).map(
      ([key, level]) => ({
        key,
        label: SKILL_LABELS[key] || key,
        level
      })
    ),
    evidenceFiles: toEvidenceFiles(item.evidence_files)
  }

}

const SUBMISSION_STATUS_LABELS = computed(() => ({
  pending: t.value.studentActivities.statusPending,
  approved: t.value.studentActivities.statusApproved,
  rejected: t.value.studentActivities.statusRejected
}))

// GET /api/student/me/external-activities (ทุกสถานะ)
// ไฟล์หลักฐานทุกไฟล์ของคำขอ (สูงสุด 10 ไฟล์)
const toEvidenceFiles = (files) =>
  (files || []).map(file => ({
    id: file.id,
    name: file.original_name,
    url: `${API_BASE}${file.url}`
  }))


const toSubmissionView = (item) => ({
  key: `submission-${item.id}`,
  id: item.id,
  source: 'submission',
  sourceLabel: t.value.studentActivities.externalActivityLabel,
  title: item.title,
  description: item.description || '',
  studentName:
    `${item.student.first_name} ${item.student.last_name}`,
  studentId: item.student_id,
  status: item.status,
  statusLabel: SUBMISSION_STATUS_LABELS.value[item.status] || item.status,
  date: item.start_date,
  endDate: item.end_date,
  category: item.activity_type,
  organizer: item.organization,
  location: item.location,
  role: item.role === 'organizer'
    ? t.value.studentActivities.roleOrganizer
    : t.value.studentActivities.roleParticipant,
  skills: Object.entries(item.skills || {}).map(
    ([key, level]) => ({
      key,
      label: SKILL_LABELS[key] || key,
      level
    })
  ),
  evidenceFiles: toEvidenceFiles(item.evidence_files),
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

const SOURCE_TABS = computed(() => [
  { value: 'all', label: t.value.studentActivities.allTab },
  { value: 'activity', label: t.value.studentActivities.facultyActivitiesTab },
  { value: 'external_activity', label: t.value.studentActivities.externalActivitiesTab },
  { value: 'submissions', label: t.value.studentActivities.mySubmissionsTab }
])


/* =====================================================
   My Submissions: status filter
===================================================== */

const submissionStatus = ref('all')

const SUBMISSION_STATUS_TABS = computed(() => [
  { value: 'all', label: t.value.studentActivities.allTab },
  { value: 'pending', label: t.value.studentActivities.statusPending },
  { value: 'approved', label: t.value.studentActivities.statusApproved },
  { value: 'rejected', label: t.value.studentActivities.statusRejected }
])

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


// แก้ไข + ส่งใหม่กิจกรรมภายนอกที่ถูกไม่อนุมัติ
const editSubmission = (activity) => {

  router.push({
    path: '/student/external-activity',
    query: { edit: activity.id }
  })

}


// ลบคำขอกิจกรรมภายนอก ได้เฉพาะ pending / rejected (backend กันซ้ำอีกชั้น)
const deletingId = ref(null)

const canDeleteSubmission = (activity) =>
  activity.source === 'submission' &&
  ['pending', 'rejected'].includes(activity.status)

const deleteSubmission = async (activity) => {

  const confirmed = window.confirm(
    t.value.studentActivities.deleteSubmissionConfirm
      .replace('{title}', activity.title)
  )

  if (!confirmed) return

  deletingId.value = activity.id

  try {

    const response = await fetch(
      `${API_BASE}/api/student/me/external-activities/${activity.id}`,
      {
        method: 'DELETE',
        headers: studentHeaders()
      }
    )

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null)
      throw new Error(
        errorBody?.detail || t.value.studentActivities.deleteSubmissionFailed
      )
    }

    submissions.value = submissions.value.filter(
      item => item.id !== activity.id
    )

    if (selectedActivity.value?.id === activity.id && selectedActivity.value?.source === 'submission') {
      selectedActivity.value = null
    }

  } catch (err) {

    window.alert(
      err instanceof TypeError
        ? t.value.studentActivities.deleteSubmissionFailed
        : err.message
    )

  } finally {

    deletingId.value = null

  }

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

// ข้อมูลโหลดครบแล้วหรือยัง: watch ของ ?open ทำงานก่อน fetch เสร็จ
// ถ้าเปิดตอนนั้นจะหาไม่เจอแล้วล้าง ?open ทิ้ง modal เลยไม่เปิด
const dataLoaded = ref(false)

const openActivityFromNotification = async () => {

  const activityId =
    Number(route.query.open)


  if (!activityId || !dataLoaded.value) {
    return
  }


  // แจ้งเตือนอ้าง id ของคำขอกิจกรรมภายนอก (My Submissions) เท่านั้น
  // ห้ามหาใน Faculty Activities: id คนละตาราง ชนกันได้ จะเปิดผิดรายการ
  const submission =
    submissions.value.find(
      item =>
        item.id === activityId
    )


  if (submission) {

    sourceFilter.value = 'submissions'
    selectedActivity.value = submission

  }


  /*
    เปิด Modal แล้วล้าง ?open=... ?source=...
    เพื่อให้ URL กลับมาสะอาด
  */
  await router.replace({
    path: '/student/activities',
    query: submission
      ? { tab: 'submissions' }
      : route.query.tab
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
      SOURCE_TABS.value.some(item => item.value === tab)
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
        t.value.studentActivities.loadActivitiesErrorLabel
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

    dataLoaded.value = true


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
            {{ t.studentActivities.pageTitle }}
          </h1>

          <p>
            {{ t.studentActivities.pageSubtitle }}
          </p>

          <div class="search-box">
            <Search :size="17" />
            <input
              v-model="searchText"
              type="search"
              :placeholder="t.studentActivities.searchPlaceholder"
              :aria-label="t.studentActivities.searchPlaceholder"
            />
            <button
              v-if="searchText"
              class="clear-search"
              type="button"
              :aria-label="t.studentActivities.clearSearch"
              @click="clearSearch"
            >
              <X :size="15" />
            </button>
          </div>

        </div>


        <div
          class="pending-card"
          data-testid="total-activities"
        >

          <strong>
            {{ sourceCounts.all }}
          </strong>

          <span>
            {{ t.studentActivities.totalActivitiesLabel }}
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

            {{ t.studentActivities.filterByDateLabel }}

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
              {{ t.studentActivities.clearLabel }}
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
        {{ t.studentActivities.loadingLabel }}
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
              {{ t.studentActivities.rejectReasonPrefix }} {{ activity.rejectReason }}
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
              v-if="activity.source === 'submission' && activity.status === 'rejected'"
              class="edit-submission-btn"
              type="button"
              @click="editSubmission(activity)"
            >
              {{ t.studentActivities.editLabel }}
            </button>


            <button
              v-if="canDeleteSubmission(activity)"
              class="delete-submission-btn"
              type="button"
              :disabled="deletingId === activity.id"
              @click="deleteSubmission(activity)"
            >
              {{
                deletingId === activity.id
                  ? t.studentActivities.deletingLabel
                  : t.studentActivities.deleteLabel
              }}
            </button>


            <button
              class="details-btn"
              type="button"
              @click="
                viewDetails(activity)
              "
            >
              {{ t.studentActivities.detailsButtonLabel }}
            </button>


            <button
              class="arrow-btn"
              type="button"
              :aria-label="t.studentActivities.viewActivityDetailsAriaLabel"
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
            {{ t.studentActivities.noActivitiesFoundTitle }}
          </h3>

          <p>
            {{
              activities.length
                ? t.studentActivities.tryAnotherLabel
                : sourceFilter === 'submissions'
                  ? t.studentActivities.noSubmissionsYetLabel
                  : t.studentActivities.noApprovedActivitiesYetLabel
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

          {{ t.studentActivities.loadMoreLabel }}

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

              ({{ t.studentActivities.idLabel }}
              {{ selectedActivity.studentId }})
            </p>

          </div>


          <button
            class="close-btn"
            type="button"
            :aria-label="t.studentActivities.closeDetailsAriaLabel"
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
                {{ t.studentActivities.activityDetailsHeading }}
              </h3>

              <div class="detail-divider">
              </div>


              <div class="detail-info-grid">

                <div>

                  <span class="detail-label">
                    {{ t.studentActivities.categoryLabel }}
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
                    {{ t.studentActivities.dateLabel }}
                  </span>

                  <p>
                    {{ dateRangeText(selectedActivity) }}
                  </p>

                </div>


                <div>

                  <span class="detail-label">
                    {{ t.studentActivities.sourceDetailLabel }}
                  </span>

                  <p>
                    {{ selectedActivity.sourceLabel }}
                  </p>

                </div>


                <div>

                  <span class="detail-label">
                    {{ t.studentActivities.roleLabel }}
                  </span>

                  <p>
                    {{ selectedActivity.role }}
                  </p>

                </div>


                <div>

                  <span class="detail-label">
                    {{ t.studentActivities.locationLabel }}
                  </span>

                  <p>
                    {{ selectedActivity.location || '-' }}
                  </p>

                </div>


                <div>

                  <span class="detail-label">
                    {{ t.studentActivities.organizerLabel }}
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
                    ? t.studentActivities.activityDescriptionHeading
                    : t.studentActivities.studentReflectionHeading
                }}
              </h3>


              <div class="reflection-text">

                {{
                  selectedActivity.description
                  || t.studentActivities.noDescriptionProvided
                }}

              </div>


              <ul
                v-if="selectedActivity.evidenceFiles?.length"
                class="evidence-links"
              >
                <li
                  v-for="file in selectedActivity.evidenceFiles"
                  :key="file.id"
                >
                  <a
                    class="evidence-link"
                    :href="file.url"
                    target="_blank"
                    rel="noopener"
                    :title="file.name"
                  >
                    <FileText :size="13" />
                    <span>{{ file.name }}</span>
                    <ExternalLink :size="11" />
                  </a>
                </li>
              </ul>

            </section>


            <!-- Skills -->

            <section class="detail-card">

              <h3>
                {{
                  selectedActivity.source === 'activity'
                    ? t.studentActivities.skillsHeading
                    : t.studentActivities.skillMappingHeading
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
                  {{ skill.label }} · {{ t.studentActivities.levelLabel }} {{ skill.level }}
                </span>

              </div>


              <p
                v-else
                class="no-data"
              >
                {{ t.studentActivities.noRelatedSkillsLabel }}
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
                {{ t.studentActivities.currentStatusLabel }}
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
                  {{ t.studentActivities.waitingForReviewTitle }}
                </strong>
                <p>
                  {{ t.studentActivities.waitingForReviewText }}
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
                  {{ t.studentActivities.activityNotApprovedTitle }}
                </strong>
                <p data-testid="reject-reason">
                  {{
                    selectedActivity.rejectReason
                    || t.studentActivities.activityNotApprovedFallbackText
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
                  {{ t.studentActivities.approvedByAdminTitle }}
                </strong>
                <p>
                  {{ t.studentActivities.approvedByAdminText }}
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
                  {{ t.studentActivities.activityCancelledTitle }}
                </strong>
                <p>
                  {{ t.studentActivities.activityCancelledText }}
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
                      ? t.studentActivities.activityCompletedTitle
                      : t.studentActivities.registeredTitle
                  }}
                </strong>
                <p>
                  {{ t.studentActivities.listedAsRolePrefix }}
                  {{ selectedActivity.role.toLowerCase() }}
                  {{ t.studentActivities.listedAsRoleSuffix }}
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

.page-header > div:first-child {
  min-width: 0;
  flex: 1;
}


/* =====================================================
   Search
===================================================== */

.search-box {
  width: 420px;
  max-width: 100%;
  height: 40px;
  margin-top: 14px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  gap: 9px;
  background: #fff;
  border: 1px solid #e0e3e8;
  border-radius: 20px;
  color: #9ca3af;
  box-sizing: border-box;
}

.search-box:focus-within {
  border-color: #b5c0ff;
  box-shadow: 0 0 0 3px rgba(67, 89, 255, 0.07);
}

.search-box input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  color: #303846;
  font: inherit;
  font-size: 13px;
}

.search-box input::placeholder {
  color: #9ca3af;
  opacity: 1;
}

/* ใช้ปุ่มล้างของเราเอง ไม่ใช้ปุ่ม x ของ input type=search */
.search-box input::-webkit-search-cancel-button {
  display: none;
}

.clear-search {
  padding: 0;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: #8d96a5;
  cursor: pointer;
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


.evidence-links {
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}


.evidence-link {
  max-width: 100%;

  display: inline-flex;

  align-items: center;

  gap: 5px;

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


.edit-submission-btn {
  min-width: 70px;

  padding: 8px 15px;

  border: none;

  border-radius: 7px;

  background: #f0631f;

  color: white;

  font-size: 10px;
  font-weight: 700;

  cursor: pointer;
}


.edit-submission-btn:hover {
  opacity: 0.85;
}


.delete-submission-btn {
  min-width: 70px;

  padding: 7px 14px;

  border: 1px solid #f3c1bd;

  border-radius: 7px;

  background: #fff;

  color: #d92d20;

  font-size: 10px;
  font-weight: 700;

  cursor: pointer;
}


.delete-submission-btn:hover {
  background: #fef3f2;
}


.delete-submission-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
