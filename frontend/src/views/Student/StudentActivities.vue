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
  UserRound,
  SlidersHorizontal,
  ChevronRight,
  ChevronDown
} from 'lucide-vue-next'

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

const activities = ref([
  {
    id: 1,

    title:
      'Science Volunteer Camp',

    description:
      'Volunteer activity at the Faculty of Science.',

    studentName:
      'Tanakit Wanprasert',

    studentId:
      '670510659',

    status:
      'Pending',

    date:
      '2026-09-10',

    category:
      'Community Service',

    organizer:
      'Faculty of Science',

    reflection:
      'This activity helped me improve teamwork, communication and responsibility while working with other students.',

    skills: [
      'Communication',
      'Teamwork',
      'Leadership'
    ]
  },


  {
    id: 2,

    title:
      'Leadership Workshop',

    description:
      'Leadership and teamwork development workshop.',

    studentName:
      'Tanakit Wanprasert',

    studentId:
      '670510659',

    status:
      'Pending',

    date:
      '2026-09-12',

    category:
      'Leadership',

    organizer:
      'Faculty of Science',

    reflection:
      'I learned how to work with a team, make decisions and communicate more clearly in group activities.',

    skills: [
      'Leadership',
      'Communication',
      'Teamwork'
    ]
  },


  {
    id: 3,

    title:
      'Communication Training',

    description:
      'Communication skills training program.',

    studentName:
      'Tanakit Wanprasert',

    studentId:
      '670510659',

    status:
      'Approved',

    date:
      '2026-09-13',

    category:
      'Science Communication',

    organizer:
      'Science Student Development Unit',

    reflection:
      'This training helped me improve my presentation skills and communicate scientific information more clearly.',

    skills: [
      'Communication',
      'Presentation',
      'Public Speaking'
    ]
  },


  {
    id: 4,

    title:
      'Programming Workshop',

    description:
      'Basic programming and problem solving workshop.',

    studentName:
      'Tanakit Wanprasert',

    studentId:
      '670510659',

    status:
      'Rejected',

    date:
      '2026-09-16',

    category:
      'Academic Activity',

    organizer:
      'Computer Science Department',

    reflection:
      'I practiced problem solving and programming with other students.',

    skills: [
      'Problem Solving',
      'Critical Thinking'
    ],

    rejectionReason:
      'Please upload a clearer participation certificate.'
  }
])


/* =====================================================
   Pending Count
===================================================== */

const totalPending = computed(() => {

  return activities.value.filter(
    activity =>
      activity.status.toLowerCase()
      === 'pending'
  ).length

})


/* =====================================================
   Search + Date Filter
===================================================== */

const filteredActivities = computed(() => {

  const keyword =
    searchText.value
      .trim()
      .toLowerCase()


  return activities.value.filter(
    activity => {

      const matchSearch =
        !keyword ||

        activity.title
          .toLowerCase()
          .includes(keyword) ||

        activity.description
          .toLowerCase()
          .includes(keyword) ||

        activity.studentName
          .toLowerCase()
          .includes(keyword) ||

        activity.studentId
          .toLowerCase()
          .includes(keyword)


      const matchDate =
        !selectedDate.value ||
        activity.date === selectedDate.value


      return (
        matchSearch &&
        matchDate
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
    path: '/student/activities'
  })

}


/*
  watch ช่วยให้กด Notification ได้
  แม้ตอนนี้อยู่หน้า /student/activities อยู่แล้ว
*/
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

    const response = await fetch(
      'http://localhost:8000/api/student/me/activities'
    )


    if (!response.ok) {

      throw new Error(
        'Cannot load activities'
      )

    }


    const data =
      await response.json()


    activities.value =
      data


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


  /*
    ตอนนี้ใช้ Mock Data
    ไม่ต้องเปิด fetchActivities()

    ตอน Backend พร้อม:
    fetchActivities()
  */

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
            Review and track your activity submissions.
          </p>

        </div>


        <div class="pending-card">

          <strong>
            {{ totalPending }}
          </strong>

          <span>
            TOTAL PENDING
          </span>

        </div>

      </section>


      <!-- =================================================
           Tabs / Filter
      ================================================== -->

      <section class="tabs-row">

        <button
          class="tab active"
          type="button"
        >
          Pending
        </button>


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
          :key="activity.id"
          class="activity-card"
        >

          <!-- Avatar -->

          <div class="avatar">

            <UserRound :size="20" />

          </div>


          <!-- Activity Info -->

          <div class="activity-info">

            <h3>
              {{ activity.title }}
            </h3>

            <p>
              {{ activity.description }}
            </p>


            <small>

              {{ activity.studentName }}

              •

              {{ activity.studentId }}

            </small>

          </div>


          <!-- Right -->

          <div class="activity-meta">

            <span class="activity-date">
              {{ activity.date }}
            </span>


            <span
              class="status"
              :class="
                activity.status
                  .toLowerCase()
              "
            >
              {{ activity.status }}
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
            Try another activity name
            or date.
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
                    {{ selectedActivity.date }}
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
                Student Reflection
              </h3>


              <div class="reflection-text">

                {{
                  selectedActivity.reflection
                  || 'No reflection provided.'
                }}

              </div>

            </section>


            <!-- Skills -->

            <section class="detail-card">

              <h3>
                Self-Mapped Skills
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
                  :key="skill"
                  class="skill"
                >
                  {{ skill }}
                </span>

              </div>


              <p
                v-else
                class="no-data"
              >
                No skills added.
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
              :class="
                selectedActivity.status
                  .toLowerCase()
              "
            >

              <span class="detail-label">
                CURRENT STATUS
              </span>


              <!-- Pending -->

              <div
                v-if="
                  selectedActivity.status
                  === 'Pending'
                "
                class="big-status"
              >

                <span class="status-symbol">
                  ◷
                </span>

                Pending Review

              </div>


              <!-- Approved -->

              <div
                v-else-if="
                  selectedActivity.status
                  === 'Approved'
                "
                class="big-status"
              >

                <span class="status-symbol">
                  ✓
                </span>

                Approved

              </div>


              <!-- Rejected -->

              <div
                v-else
                class="big-status"
              >

                <span class="status-symbol">
                  ✕
                </span>

                Not Approved

              </div>

            </section>


            <!-- Status Message -->

            <section class="detail-card">

              <h3>
                Submission Status
              </h3>


              <!-- Pending -->

              <div
                v-if="
                  selectedActivity.status
                  === 'Pending'
                "
                class="
                  status-message
                  pending-message
                "
              >

                <strong>
                  Waiting for Review
                </strong>

                <p>
                  This activity is currently
                  waiting for administrator
                  review.
                </p>

              </div>


              <!-- Approved -->

              <div
                v-else-if="
                  selectedActivity.status
                  === 'Approved'
                "
                class="
                  status-message
                  approved-message
                "
              >

                <strong>
                  Activity Approved
                </strong>

                <p>
                  This activity has already
                  been reviewed and approved.
                </p>

              </div>


              <!-- Rejected -->

              <div
                v-else
                class="
                  status-message
                  rejected-message
                "
              >

                <strong>
                  Activity Not Approved
                </strong>

                <p>
                  {{
                    selectedActivity
                      .rejectionReason

                    ||
                    'This activity was not approved.'
                  }}
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
