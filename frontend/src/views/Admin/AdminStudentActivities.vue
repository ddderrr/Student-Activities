<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Plus,
  Search,
  SlidersHorizontal,
  Zap,
  Users,
  FileText,
  ChevronLeft,
  ChevronRight,
  Eye,
  Upload,
  CalendarDays,
  X,
  FileSpreadsheet,
  LoaderCircle,
  TriangleAlert,
  CheckCircle2,
  UserPlus,
  ChevronDown
} from 'lucide-vue-next'

const searchText = ref('')
const quickSearch = ref('')
const selectedCategory = ref('all')
const selectedDate = ref('')
const currentPage = ref(1)
const rowsPerPage = 10
const router = useRouter()
// Loading states
// pageLoading = ใช้ตอนเปิด/refresh หน้า เพื่อทำ Skeleton ทั้งหน้า
// tableLoading = ใช้ตอน reload เฉพาะตารางในอนาคต
const pageLoading = ref(true)
const tableLoading = ref(true)
const skeletonRows = Array.from({ length: rowsPerPage }, (_, index) => index)

const majorOptions = [
  'เคมี',
  'เคมีอุตสาหกรรม',
  'จุลชีววิทยา',
  'ชีวเคมีและชีวเคมีนวัตกรรม',
  'ชีววิทยา',
  'ธรณีวิทยา',
  'ฟิสิกส์และวัสดุศาสตร์',
  'สัตววิทยา',
  'วิทยาการคอมพิวเตอร์',
  'วิทยาการข้อมูล',
  'วิทยาศาสตร์สิ่งแวดล้อม (หลักสูตรนานาชาติ)',
  'สถิติ',
  'อัญมณีวิทยา'
]

const roleOptions = [
  { value: 'participant', label: 'Participant' },
  { value: 'organizer', label: 'Organizer' }
]

const API_BASE = 'http://localhost:8000'

// Import participants modal state
const showImportModal = ref(false)
const selectedActivity = ref(null)
const selectedFile = ref(null)
const importPreview = ref(null)
const importError = ref('')
const importLoading = ref(false)
const confirmLoading = ref(false)
const importSuccess = ref('')

// Manage participants
const openManageMenuId = ref(null)
const showAddStudentModal = ref(false)
const addStudentLoading = ref(false)
const addStudentError = ref('')
const addStudentSuccess = ref('')
const showMajorDropdown = ref(false)
const showRoleDropdown = ref(false)

const manualStudent = ref({
  student_id: '',
  first_name: '',
  last_name: '',
  email: '',
  major: '',
  role: 'participant'
})

/*
  Mock data สำหรับทดสอบ UI ก่อน
  ภายหลังเปลี่ยนเป็นข้อมูลจาก Backend ได้
*/
const activities = ref([
  {
    id: 1,
    uid: 'SC-2026-001',
    name: 'Annual Chemistry Expo',
    organizer: 'Chemistry Society',
    category: 'Academic',
    date: '2026-09-02',
    participants: 45,
    capacity: 50
  },
  {
    id: 2,
    uid: 'SC-2026-002',
    name: 'Community Lab Visit',
    organizer: 'Dept. of Life Sciences',
    category: 'Community',
    date: '2026-09-04',
    participants: 12,
    capacity: 15
  },
  {
    id: 3,
    uid: 'SC-2026-003',
    name: 'Peer Mentorship Workshop',
    organizer: 'Faculty Council',
    category: 'Workshop',
    date: '2026-09-06',
    participants: 30,
    capacity: 30
  },
  {
    id: 4,
    uid: 'SC-2026-004',
    name: 'Sci-Comm Symposium',
    organizer: 'Communications Lab',
    category: 'Seminar',
    date: '2026-09-08',
    participants: 114,
    capacity: 200
  },
  {
    id: 5,
    uid: 'SC-2026-005',
    name: 'Data Science Bootcamp',
    organizer: 'Computer Science',
    category: 'Workshop',
    date: '2026-09-10',
    participants: 68,
    capacity: 80
  },
  {
    id: 6,
    uid: 'SC-2026-006',
    name: 'Biology Field Study',
    organizer: 'Biology Department',
    category: 'Academic',
    date: '2026-09-12',
    participants: 28,
    capacity: 35
  },
  {
    id: 7,
    uid: 'SC-2026-007',
    name: 'Physics Open House',
    organizer: 'Physics Department',
    category: 'Academic',
    date: '2026-09-14',
    participants: 74,
    capacity: 100
  },
  {
    id: 8,
    uid: 'SC-2026-008',
    name: 'Environmental Volunteer Day',
    organizer: 'Green Science Club',
    category: 'Community',
    date: '2026-09-16',
    participants: 52,
    capacity: 70
  },
  {
    id: 9,
    uid: 'SC-2026-009',
    name: 'Research Poster Day',
    organizer: 'Research Affairs',
    category: 'Seminar',
    date: '2026-09-18',
    participants: 83,
    capacity: 120
  },
  {
    id: 10,
    uid: 'SC-2026-010',
    name: 'Science Career Talk',
    organizer: 'Student Affairs',
    category: 'Seminar',
    date: '2026-09-20',
    participants: 95,
    capacity: 150
  },
  {
    id: 11,
    uid: 'SC-2026-011',
    name: 'Mathematics Challenge',
    organizer: 'Mathematics Department',
    category: 'Academic',
    date: '2026-09-22',
    participants: 42,
    capacity: 60
  },
  {
    id: 12,
    uid: 'SC-2026-012',
    name: 'Innovation Hackathon',
    organizer: 'Innovation Center',
    category: 'Workshop',
    date: '2026-09-24',
    participants: 101,
    capacity: 120
  }
])

const categories = computed(() => {
  const unique = [...new Set(activities.value.map((item) => item.category))]
  return unique.sort()
})

const filteredActivities = computed(() => {
  const mainKeyword = searchText.value.trim().toLowerCase()
  const quickKeyword = quickSearch.value.trim().toLowerCase()

  return activities.value.filter((activity) => {
    const matchMain =
      !mainKeyword ||
      activity.name.toLowerCase().includes(mainKeyword)

    const matchQuick =
      !quickKeyword ||
      activity.name.toLowerCase().includes(quickKeyword) ||
      activity.organizer.toLowerCase().includes(quickKeyword) ||
      activity.uid.toLowerCase().includes(quickKeyword)

    const matchCategory =
      selectedCategory.value === 'all' ||
      activity.category === selectedCategory.value

    const matchDate =
      !selectedDate.value ||
      activity.date === selectedDate.value

    return matchMain && matchQuick && matchCategory && matchDate
  })
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredActivities.value.length / rowsPerPage))
)

const paginatedActivities = computed(() => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value
  }

  const start = (currentPage.value - 1) * rowsPerPage
  return filteredActivities.value.slice(start, start + rowsPerPage)
})

const monthlyParticipants = computed(() => {
  const now = new Date()
  const currentYear = now.getFullYear()
  const currentMonth = now.getMonth()

  return activities.value
    .filter((activity) => {
      const date = new Date(`${activity.date}T00:00:00`)
      return (
        date.getFullYear() === currentYear &&
        date.getMonth() === currentMonth
      )
    })
    .reduce((sum, activity) => sum + activity.participants, 0)
})

const activeActivities = computed(() => activities.value.length)

/*
  Placeholder ก่อนเชื่อม Backend จริง
*/
const pendingEvaluations = ref(12)

function applyFilters() {
  currentPage.value = 1
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function formatDate(dateString) {
  const date = new Date(`${dateString}T00:00:00`)
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: '2-digit',
    year: 'numeric'
  }).format(date)
}

function participantPercent(activity) {
  if (!activity.capacity) return 0
  return Math.min(100, (activity.participants / activity.capacity) * 100)
}

onMounted(() => {
  /*
    DEMO ONLY:
    ให้เห็น Full-page Skeleton ตอนเปิด/refresh หน้า

    พอเชื่อม Backend จริง:
    - ตั้ง pageLoading = true ก่อน fetch ข้อมูลหน้า Activities
    - fetch summary + filters + activities
    - ตั้ง pageLoading = false ใน finally
    - tableLoading เอาไว้ใช้ตอน reload/filter ตารางเฉพาะส่วน
  */
  setTimeout(() => {
    pageLoading.value = false
    tableLoading.value = false
  }, 700)
})

function createActivity() {
  console.log('Create New Activity')
}

function viewActivity(activity) {
  router.push(`/admin/activities/${activity.id}/details`)
}

function toggleManageMenu(activityId) {
  openManageMenuId.value =
    openManageMenuId.value === activityId
      ? null
      : activityId
}

function openAddStudent(activity) {
  selectedActivity.value = activity
  openManageMenuId.value = null

  manualStudent.value = {
    student_id: '',
    first_name: '',
    last_name: '',
    email: '',
    major: '',
    role: 'participant'
  }

  addStudentError.value = ''
  addStudentSuccess.value = ''
  showMajorDropdown.value = false
  showRoleDropdown.value = false
  showAddStudentModal.value = true
}

function closeAddStudentModal() {
  if (addStudentLoading.value) return

  showAddStudentModal.value = false
  showMajorDropdown.value = false
  showRoleDropdown.value = false
  selectedActivity.value = null
  addStudentError.value = ''
  addStudentSuccess.value = ''
}

function selectMajor(major) {
  manualStudent.value.major = major
  showMajorDropdown.value = false
}

function selectRole(role) {
  manualStudent.value.role = role.value
  showRoleDropdown.value = false
}

function roleLabel(value) {
  return (
    roleOptions.find((role) => role.value === value)?.label ||
    'เลือก Role'
  )
}

async function addStudentManually() {
  if (!selectedActivity.value) return

  const student = {
    student_id: manualStudent.value.student_id.trim(),
    first_name: manualStudent.value.first_name.trim(),
    last_name: manualStudent.value.last_name.trim(),
    email: manualStudent.value.email.trim(),
    major: manualStudent.value.major.trim(),
    role: manualStudent.value.role
  }

  if (
    !student.student_id ||
    !student.first_name ||
    !student.last_name ||
    !student.email ||
    !student.major ||
    !student.role
  ) {
    addStudentError.value =
      'กรุณากรอกรหัสนักศึกษา ชื่อ นามสกุล อีเมล สาขาวิชา และ Role ให้ครบ'
    return
  }

  if (!student.email.includes('@')) {
    addStudentError.value = 'รูปแบบอีเมลไม่ถูกต้อง'
    return
  }

  addStudentLoading.value = true
  addStudentError.value = ''
  addStudentSuccess.value = ''

  try {
    const response = await fetch(
      `${API_BASE}/api/activities/${selectedActivity.value.id}/participants/import/confirm`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          students: [student]
        })
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'เพิ่มนักศึกษาไม่สำเร็จ')
    }

    selectedActivity.value.participants = data.total_participants

    if (data.duplicate_count > 0) {
      addStudentError.value =
        'นักศึกษาคนนี้มีอยู่ในกิจกรรมแล้ว'
      return
    }

    addStudentSuccess.value = 'เพิ่มนักศึกษาเข้ากิจกรรมสำเร็จ'

    manualStudent.value = {
      student_id: '',
      first_name: '',
      last_name: '',
      email: '',
      major: '',
      role: 'participant'
    }
  } catch (error) {
    addStudentError.value =
      error.message || 'ไม่สามารถเชื่อมต่อ Backend ได้'
  } finally {
    addStudentLoading.value = false
  }
}

function openImportParticipants(activity) {
  openManageMenuId.value = null
  importParticipants(activity)
}

function importParticipants(activity) {
  selectedActivity.value = activity
  selectedFile.value = null
  importPreview.value = null
  importError.value = ''
  importSuccess.value = ''
  showImportModal.value = true
}

function closeImportModal() {
  if (importLoading.value || confirmLoading.value) return

  showImportModal.value = false
  selectedActivity.value = null
  selectedFile.value = null
  importPreview.value = null
  importError.value = ''
  importSuccess.value = ''
}

function handleImportFile(event) {
  selectedFile.value = event.target.files?.[0] ?? null
  importPreview.value = null
  importError.value = ''
  importSuccess.value = ''
}

async function previewParticipantsImport() {
  if (!selectedActivity.value) return

  if (!selectedFile.value) {
    importError.value = 'กรุณาเลือกไฟล์ CSV หรือ Excel ก่อน'
    return
  }

  importLoading.value = true
  importError.value = ''
  importSuccess.value = ''

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const response = await fetch(
      `${API_BASE}/api/activities/${selectedActivity.value.id}/participants/import/preview`,
      {
        method: 'POST',
        body: formData
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'ไม่สามารถอ่านไฟล์ได้')
    }

    importPreview.value = data
  } catch (error) {
    importError.value =
      error.message || 'ไม่สามารถเชื่อมต่อ Backend ได้'
  } finally {
    importLoading.value = false
  }
}

async function confirmParticipantsImport() {
  if (!selectedActivity.value || !importPreview.value) return

  if (importPreview.value.invalid_count > 0) {
    importError.value =
      'กรุณาแก้ข้อมูลที่ไม่ถูกต้องก่อน Confirm Import'
    return
  }

  confirmLoading.value = true
  importError.value = ''
  importSuccess.value = ''

  try {
    const response = await fetch(
      `${API_BASE}/api/activities/${selectedActivity.value.id}/participants/import/confirm`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          students: importPreview.value.students
        })
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'Import ไม่สำเร็จ')
    }

    // TEST MODE: sync จำนวน participant จาก backend memory
    selectedActivity.value.participants = data.total_participants

    importSuccess.value =
      `Import สำเร็จ ${data.imported_count} คน` +
      (data.duplicate_count
        ? ` (ข้ามข้อมูลซ้ำ ${data.duplicate_count} คน)`
        : '')

    // ให้ modal ยังอยู่เพื่อเห็นผลลัพธ์ก่อน
  } catch (error) {
    importError.value =
      error.message || 'ไม่สามารถเชื่อมต่อ Backend ได้'
  } finally {
    confirmLoading.value = false
  }
}
</script>

<template>
  <section class="activities-page">

    <!-- FULL PAGE SKELETON -->
    <div
      v-if="pageLoading"
      class="page-skeleton"
      aria-label="Loading activities"
    >
      <!-- top action skeleton -->
      <div class="skeleton-top-action">
        <div class="skeleton skeleton-create-button"></div>
      </div>

      <!-- summary skeleton -->
      <div class="summary-grid">
        <article
          v-for="card in 3"
          :key="`summary-skeleton-${card}`"
          class="summary-card"
        >
          <div class="skeleton skeleton-summary-icon"></div>

          <div class="skeleton-summary-content">
            <div class="skeleton skeleton-label"></div>
            <div class="skeleton skeleton-number"></div>
          </div>
        </article>
      </div>

      <!-- filter skeleton -->
      <section class="filter-card skeleton-filter-card">
        <div class="skeleton-filter-group wide">
          <div class="skeleton skeleton-filter-label"></div>
          <div class="skeleton skeleton-filter-input"></div>
        </div>

        <div class="skeleton-filter-group">
          <div class="skeleton skeleton-filter-label"></div>
          <div class="skeleton skeleton-filter-input"></div>
        </div>

        <div class="skeleton-filter-group">
          <div class="skeleton skeleton-filter-label"></div>
          <div class="skeleton skeleton-filter-input"></div>
        </div>

        <div class="skeleton skeleton-filter-button"></div>
      </section>

      <!-- quick search skeleton -->
      <div class="skeleton-quick-search-row">
        <div class="skeleton skeleton-quick-search"></div>
      </div>

      <!-- table skeleton -->
      <section class="activities-table-card">
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>ACTIVITY NAME</th>
                <th>ORGANIZER</th>
                <th>DATE</th>
                <th>PARTICIPANTS</th>
                <th>DETAILS</th>
                <th>MANAGE PARTICIPANTS</th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="row in skeletonRows"
                :key="`page-skeleton-row-${row}`"
                class="skeleton-row"
              >
                <td>
                  <div class="skeleton-stack">
                    <div class="skeleton skeleton-title"></div>
                    <div class="skeleton skeleton-subtitle"></div>
                  </div>
                </td>

                <td>
                  <div class="skeleton skeleton-text medium"></div>
                </td>

                <td>
                  <div class="skeleton skeleton-text short"></div>
                </td>

                <td>
                  <div class="skeleton-stack">
                    <div class="skeleton skeleton-text short"></div>
                    <div class="skeleton skeleton-progress"></div>
                  </div>
                </td>

                <td>
                  <div class="skeleton skeleton-pill"></div>
                </td>

                <td>
                  <div class="skeleton skeleton-button"></div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <footer class="table-footer">
          <div class="skeleton skeleton-footer-info"></div>
          <div class="skeleton skeleton-pagination"></div>
        </footer>
      </section>
    </div>

    <template v-else>
    <!-- TOP ACTION -->
    <div class="top-action">
      <button class="create-button" @click="createActivity">
        <Plus :size="18" />
        Create New Activity
      </button>
    </div>

    <!-- SUMMARY -->
    <div class="summary-grid">
      <article class="summary-card summary-card-active">
        <div class="summary-icon blue">
          <Zap :size="25" />
        </div>

        <div>
          <span class="summary-label">ACTIVE ACTIVITIES</span>
          <strong class="summary-value">{{ activeActivities }}</strong>
        </div>
      </article>

      <article class="summary-card">
        <div class="summary-icon">
          <Users :size="25" />
        </div>

        <div>
          <span class="summary-label">PARTICIPANTS (MONTH)</span>
          <strong class="summary-value">
            {{ monthlyParticipants.toLocaleString() }}
          </strong>
        </div>
      </article>

      <article class="summary-card">
        <div class="summary-icon">
          <FileText :size="24" />
        </div>

        <div>
          <span class="summary-label">PENDING EVALUATIONS</span>
          <strong class="summary-value">{{ pendingEvaluations }}</strong>
        </div>
      </article>
    </div>

    <!-- FILTER -->
    <section class="filter-card">
      <div class="filter-field search-activity">
        <label>SEARCH ACTIVITY</label>

        <div class="input-box">
          <Search :size="16" />
          <input
            v-model="searchText"
            type="text"
            placeholder="Activity name..."
            @keyup.enter="applyFilters"
          />
        </div>
      </div>

      <div class="filter-field">
        <label>CATEGORY</label>

        <select
          v-model="selectedCategory"
          @change="applyFilters"
        >
          <option value="all">All Categories</option>
          <option
            v-for="category in categories"
            :key="category"
            :value="category"
          >
            {{ category }}
          </option>
        </select>
      </div>

      <div class="filter-field">
        <label>DATE FROM</label>

        <div class="input-box">
          <CalendarDays :size="16" />
          <input
            v-model="selectedDate"
            type="date"
            @change="applyFilters"
          />
        </div>
      </div>

      <button class="filter-button" @click="applyFilters">
        <SlidersHorizontal :size="17" />
        Apply Filters
      </button>
    </section>

    <!-- QUICK SEARCH -->
    <div class="quick-search-row">
      <div class="quick-search">
        <Search :size="15" />
        <input
          v-model="quickSearch"
          type="text"
          placeholder="Quick search activities..."
          @input="currentPage = 1"
        />
      </div>
    </div>

    <!-- TABLE -->
    <section class="activities-table-card">
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>ACTIVITY NAME</th>
              <th>ORGANIZER</th>
              <th>DATE</th>
              <th>PARTICIPANTS</th>
              <th>DETAILS</th>
              <th>MANAGE PARTICIPANTS</th>
            </tr>
          </thead>

          <tbody>
            <!-- Skeleton rows -->
            <template v-if="tableLoading">
              <tr
                v-for="row in skeletonRows"
                :key="`skeleton-${row}`"
                class="skeleton-row"
              >
                <td>
                  <div class="skeleton-stack">
                    <div class="skeleton skeleton-title"></div>
                    <div class="skeleton skeleton-subtitle"></div>
                  </div>
                </td>

                <td>
                  <div class="skeleton skeleton-text medium"></div>
                </td>

                <td>
                  <div class="skeleton skeleton-text short"></div>
                </td>

                <td>
                  <div class="skeleton-stack">
                    <div class="skeleton skeleton-text short"></div>
                    <div class="skeleton skeleton-progress"></div>
                  </div>
                </td>

                <td>
                  <div class="skeleton skeleton-pill"></div>
                </td>

                <td>
                  <div class="skeleton skeleton-button"></div>
                </td>
              </tr>
            </template>

            <template v-else>
            <tr
              v-for="activity in paginatedActivities"
              :key="activity.id"
            >
              <td>
                <div class="activity-name">
                  <strong>{{ activity.name }}</strong>
                  <small>UID: {{ activity.uid }}</small>
                </div>
              </td>

              <td class="organizer">
                {{ activity.organizer }}
              </td>

              <td>
                {{ formatDate(activity.date) }}
              </td>

              <td>
                <div class="participant-cell">
                  <strong>
                    {{ activity.participants }}/{{ activity.capacity }}
                  </strong>

                  <div class="progress-track">
                    <div
                      class="progress-value"
                      :style="{ width: `${participantPercent(activity)}%` }"
                    ></div>
                  </div>
                </div>
              </td>

              <td>
                <button
                  class="detail-button"
                  @click="viewActivity(activity)"
                >
                  <Eye :size="13" />
                  View Detail
                </button>
              </td>

              <td>
                <div class="manage-participants">
                  <button
                    class="manage-button"
                    @click="toggleManageMenu(activity.id)"
                  >
                    Manage
                    <ChevronDown :size="14" />
                  </button>

                  <div
                    v-if="openManageMenuId === activity.id"
                    class="manage-menu"
                  >
                    <button
                      class="manage-menu-item"
                      @click="openAddStudent(activity)"
                    >
                      <UserPlus :size="15" />
                      Add Student
                    </button>

                    <button
                      class="manage-menu-item"
                      @click="openImportParticipants(activity)"
                    >
                      <Upload :size="15" />
                      Import from File
                    </button>
                  </div>
                </div>
              </td>
            </tr>

            <tr v-if="!paginatedActivities.length">
              <td colspan="6">
                <div class="empty-table">
                  ไม่พบกิจกรรมที่ตรงกับเงื่อนไข
                </div>
              </td>
            </tr>
            </template>
          </tbody>
        </table>
      </div>

      <!-- PAGINATION -->
      <footer class="table-footer">
        <span v-if="!tableLoading" class="rows-info">
          Showing
          {{ filteredActivities.length ? (currentPage - 1) * rowsPerPage + 1 : 0 }}
          -
          {{
            Math.min(currentPage * rowsPerPage, filteredActivities.length)
          }}
          of {{ filteredActivities.length }}
        </span>

        <div v-if="!tableLoading" class="pagination">
          <button
            class="page-arrow"
            :disabled="currentPage === 1"
            @click="goToPage(currentPage - 1)"
          >
            <ChevronLeft :size="17" />
          </button>

          <button
            v-for="page in totalPages"
            :key="page"
            class="page-button"
            :class="{ active: currentPage === page }"
            @click="goToPage(page)"
          >
            {{ page }}
          </button>

          <button
            class="page-arrow"
            :disabled="currentPage === totalPages"
            @click="goToPage(currentPage + 1)"
          >
            <ChevronRight :size="17" />
          </button>
        </div>
      </footer>
    </section>

    </template>

    <!-- ADD STUDENT MODAL -->
    <div
      v-if="showAddStudentModal"
      class="modal-backdrop"
      @click.self="closeAddStudentModal"
    >
      <div class="import-modal add-student-modal">
        <div class="modal-header">
          <div>
            <p class="modal-eyebrow">ADD STUDENT</p>
            <h2>Add Student Manually</h2>
            <p v-if="selectedActivity" class="selected-activity">
              {{ selectedActivity.name }}
              <span>• {{ selectedActivity.uid }}</span>
            </p>
          </div>

          <button
            class="modal-close"
            @click="closeAddStudentModal"
          >
            <X :size="20" />
          </button>
        </div>

        <div class="manual-form">
          <label>
            <span>Student ID *</span>
            <input
              v-model="manualStudent.student_id"
              type="text"
              placeholder="เช่น 670510001"
            />
          </label>

          <div class="form-row">
            <label>
              <span>First Name *</span>
              <input
                v-model="manualStudent.first_name"
                type="text"
                placeholder="ชื่อ"
              />
            </label>

            <label>
              <span>Last Name *</span>
              <input
                v-model="manualStudent.last_name"
                type="text"
                placeholder="นามสกุล"
              />
            </label>
          </div>

          <label>
            <span>Email *</span>
            <input
              v-model="manualStudent.email"
              type="email"
              placeholder="student@cmu.ac.th"
            />
          </label>

          <label>
            <span>Major *</span>

            <div class="major-select">
              <button
                type="button"
                class="major-select-button"
                @click="showMajorDropdown = !showMajorDropdown"
              >
                <span
                  :class="{ placeholder: !manualStudent.major }"
                >
                  {{
                    manualStudent.major ||
                    'เลือกสาขาวิชา'
                  }}
                </span>

                <ChevronDown
                  :size="16"
                  :class="{ rotated: showMajorDropdown }"
                />
              </button>

              <div
                v-if="showMajorDropdown"
                class="major-dropdown"
              >
                <button
                  v-for="major in majorOptions"
                  :key="major"
                  type="button"
                  class="major-option"
                  @click="selectMajor(major)"
                >
                  {{ major }}
                </button>
              </div>
            </div>
          </label>

          <label>
            <span>Role *</span>

            <div class="role-select">
              <button
                type="button"
                class="role-select-button"
                @click="showRoleDropdown = !showRoleDropdown"
              >
                <span>{{ roleLabel(manualStudent.role) }}</span>

                <ChevronDown
                  :size="16"
                  :class="{ rotated: showRoleDropdown }"
                />
              </button>

              <div
                v-if="showRoleDropdown"
                class="role-dropdown"
              >
                <button
                  v-for="role in roleOptions"
                  :key="role.value"
                  type="button"
                  class="role-option"
                  :class="{ selected: manualStudent.role === role.value }"
                  @click="selectRole(role)"
                >
                  {{ role.label }}
                </button>
              </div>
            </div>
          </label>
        </div>

        <div
          v-if="addStudentError"
          class="import-message error"
        >
          <TriangleAlert :size="17" />
          {{ addStudentError }}
        </div>

        <div
          v-if="addStudentSuccess"
          class="import-message success"
        >
          <CheckCircle2 :size="17" />
          {{ addStudentSuccess }}
        </div>

        <div class="modal-actions">
          <button
            class="modal-secondary-button"
            :disabled="addStudentLoading"
            @click="closeAddStudentModal"
          >
            Cancel
          </button>

          <button
            class="modal-confirm-button"
            :disabled="addStudentLoading"
            @click="addStudentManually"
          >
            <LoaderCircle
              v-if="addStudentLoading"
              class="spin"
              :size="17"
            />
            <UserPlus v-else :size="17" />

            {{
              addStudentLoading
                ? 'Adding...'
                : 'Add Student'
            }}
          </button>
        </div>
      </div>
    </div>

    <!-- IMPORT PARTICIPANTS MODAL -->
    <div
      v-if="showImportModal"
      class="modal-backdrop"
      @click.self="closeImportModal"
    >
      <div class="import-modal">
        <div class="modal-header">
          <div>
            <p class="modal-eyebrow">IMPORT FROM FILE</p>
            <h2>Import Student List</h2>
            <p v-if="selectedActivity" class="selected-activity">
              {{ selectedActivity.name }}
              <span>• {{ selectedActivity.uid }}</span>
            </p>
          </div>

          <button
            class="modal-close"
            @click="closeImportModal"
          >
            <X :size="20" />
          </button>
        </div>

        <label class="file-dropzone">
          <FileSpreadsheet :size="34" />

          <strong>
            {{
              selectedFile
                ? selectedFile.name
                : 'Select CSV or Excel file'
            }}
          </strong>

          <span>
            รองรับไฟล์ .csv และ .xlsx
          </span>

          <input
            type="file"
            accept=".csv,.xlsx"
            hidden
            @change="handleImportFile"
          />
        </label>

        <div
          v-if="importError"
          class="import-message error"
        >
          <TriangleAlert :size="17" />
          {{ importError }}
        </div>

        <div
          v-if="importSuccess"
          class="import-message success"
        >
          <CheckCircle2 :size="17" />
          {{ importSuccess }}
        </div>

        <div
          v-if="importPreview"
          class="preview-panel"
        >
          <div class="preview-summary">
            <div>
              <span>FOUND</span>
              <strong>{{ importPreview.total }}</strong>
            </div>

            <div>
              <span>VALID</span>
              <strong>
                {{
                  importPreview.total -
                  importPreview.invalid_count
                }}
              </strong>
            </div>

            <div>
              <span>ISSUES</span>
              <strong>{{ importPreview.invalid_count }}</strong>
            </div>
          </div>

          <div class="preview-table-wrapper">
            <table class="preview-table">
              <thead>
                <tr>
                  <th>STUDENT ID</th>
                  <th>NAME</th>
                  <th>EMAIL</th>
                </tr>
              </thead>

              <tbody>
                <tr
                  v-for="(student, index) in importPreview.students.slice(0, 5)"
                  :key="student.student_id || index"
                >
                  <td>{{ student.student_id }}</td>
                  <td>
                    {{ student.first_name }}
                    {{ student.last_name }}
                  </td>
                  <td>{{ student.email }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p
            v-if="importPreview.total > 5"
            class="preview-note"
          >
            แสดงตัวอย่าง 5 จาก {{ importPreview.total }} คน
          </p>
        </div>

        <div class="modal-actions">
          <button
            class="modal-secondary-button"
            :disabled="importLoading || confirmLoading"
            @click="closeImportModal"
          >
            Cancel
          </button>

          <button
            class="modal-preview-button"
            :disabled="importLoading || confirmLoading"
            @click="previewParticipantsImport"
          >
            <LoaderCircle
              v-if="importLoading"
              class="spin"
              :size="17"
            />
            <Upload v-else :size="17" />

            {{
              importLoading
                ? 'Reading...'
                : 'Preview Import'
            }}
          </button>

          <button
            v-if="importPreview"
            class="modal-confirm-button"
            :disabled="
              confirmLoading ||
              importPreview.invalid_count > 0
            "
            @click="confirmParticipantsImport"
          >
            <LoaderCircle
              v-if="confirmLoading"
              class="spin"
              :size="17"
            />
            <CheckCircle2 v-else :size="17" />

            {{
              confirmLoading
                ? 'Importing...'
                : 'Confirm Import'
            }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.activities-page {
  min-height: 100vh;
  padding: 28px 30px 42px;
  background: #f7f8fc;
  color: #1d2a3f;
}

.top-action {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 26px;
}

.create-button {
  height: 44px;
  padding: 0 20px;
  border: 0;
  border-radius: 10px;
  background: #8613bd;
  color: #fff;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: inherit;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 7px 18px rgba(134, 19, 189, 0.18);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.summary-card {
  min-height: 110px;
  padding: 20px;
  border: 1px solid #e5ebf3;
  border-radius: 14px;
  background: #fff;
  display: flex;
  align-items: center;
  gap: 18px;
  position: relative;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.02);
}

.summary-card-active::before {
  content: '';
  position: absolute;
  top: 10px;
  bottom: 10px;
  left: 0;
  width: 4px;
  border-radius: 0 5px 5px 0;
  background: #1670f4;
}

.summary-icon {
  width: 48px;
  height: 48px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  background: #f4f7fb;
  color: #90a3bd;
}

.summary-icon.blue {
  background: #edf5ff;
  color: #0875f5;
}

.summary-label {
  display: block;
  margin-bottom: 4px;
  color: #8fa0b9;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.09em;
}

.summary-value {
  display: block;
  color: #172236;
  font-size: 28px;
  line-height: 1;
}

.filter-card {
  min-height: 116px;
  margin-bottom: 14px;
  padding: 19px 22px;
  border: 1px solid #e5ebf3;
  border-radius: 14px;
  background: #fff;
  display: flex;
  align-items: flex-end;
  gap: 18px;
}

.filter-field {
  width: 180px;
}

.filter-field.search-activity {
  width: 220px;
}

.filter-field label {
  display: block;
  margin-bottom: 7px;
  color: #8fa0b8;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.input-box {
  height: 42px;
  padding: 0 12px;
  border: 1px solid #dfe7f2;
  border-radius: 9px;
  background: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #91a2b9;
}

.input-box input,
.filter-field select {
  width: 100%;
  height: 42px;
  border: 1px solid #dfe7f2;
  border-radius: 9px;
  outline: none;
  background: #fff;
  color: #3c4b60;
  font: inherit;
  font-size: 13px;
}

.input-box input {
  height: auto;
  padding: 0;
  border: 0;
}

.filter-field select {
  padding: 0 12px;
}

.filter-button {
  margin-left: auto;
  height: 42px;
  padding: 0 16px;
  border: 0;
  border-radius: 9px;
  background: #eaf2ff;
  color: #1265d8;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-family: inherit;
  font-weight: 700;
  cursor: pointer;
}

.quick-search-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0;
}

.quick-search {
  width: 290px;
  height: 36px;
  padding: 0 13px;
  border-radius: 999px 999px 0 0;
  background: #eef3f9;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #8ea0b8;
}

.quick-search input {
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: #53637a;
  font: inherit;
  font-size: 12px;
}

.activities-table-card {
  overflow: hidden;
  border: 1px solid #e5ebf3;
  border-radius: 14px;
  background: #fff;
}

.table-scroll {
  overflow-x: auto;
}

table {
  width: 100%;
  min-width: 900px;
  border-collapse: collapse;
}

thead {
  background: #f8fafc;
}

th {
  padding: 17px 20px;
  color: #8ea0b8;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-align: left;
}

td {
  height: 92px;
  padding: 15px 20px;
  border-top: 1px solid #edf1f6;
  color: #415269;
  font-size: 13px;
  vertical-align: middle;
}

.activity-name {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.activity-name strong {
  color: #1d2a3f;
  font-size: 14px;
  line-height: 1.35;
}

.activity-name small {
  color: #93a5bc;
  font-size: 9px;
}

.organizer {
  max-width: 160px;
}

.participant-cell {
  width: 110px;
}

.participant-cell strong {
  display: block;
  margin-bottom: 6px;
  color: #34465e;
  font-size: 12px;
}

.progress-track {
  width: 90px;
  height: 4px;
  overflow: hidden;
  border-radius: 99px;
  background: #edf2f7;
}

.progress-value {
  height: 100%;
  border-radius: inherit;
  background: #0b6df0;
}

.detail-button,
.manage-button,
.manage-menu-item {
  border: 0;
  font-family: inherit;
  cursor: pointer;
}

.detail-button {
  min-height: 27px;
  padding: 0 10px;
  border: 1px solid #e0e7f0;
  border-radius: 999px;
  background: #f5f8fb;
  color: #53647a;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
}

.manage-participants {
  position: relative;
  display: inline-block;
}

.manage-button {
  min-height: 31px;
  padding: 0 11px;
  border-radius: 7px;
  background: #edf4ff;
  color: #1468dc;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
}

.manage-button:hover {
  background: #dfebff;
}

.manage-menu {
  position: absolute;
  top: calc(100% + 7px);
  right: 0;
  z-index: 40;
  width: 170px;
  padding: 6px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.12);
}

.manage-menu-item {
  width: 100%;
  min-height: 36px;
  padding: 0 10px;
  border-radius: 7px;
  background: transparent;
  color: #46566d;
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 11px;
  text-align: left;
}

.manage-menu-item:hover {
  background: #f3f7fc;
  color: #1769dc;
}

.empty-table {
  padding: 45px 20px;
  text-align: center;
  color: #8999ae;
}

.table-footer {
  min-height: 62px;
  padding: 12px 18px;
  border-top: 1px solid #edf1f6;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.rows-info {
  color: #8b9bb0;
  font-size: 11px;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 5px;
}

.page-button,
.page-arrow {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #53647a;
  display: grid;
  place-items: center;
  font-family: inherit;
  cursor: pointer;
}

.page-button.active {
  background: #8613bd;
  color: #fff;
  font-weight: 700;
}

.page-button:hover:not(.active),
.page-arrow:hover:not(:disabled) {
  background: #f1f5f9;
}

.page-arrow:disabled {
  opacity: 0.35;
  cursor: default;
}




/* ============================= */
/* FULL PAGE SKELETON */
/* ============================= */

.page-skeleton {
  width: 100%;
}

.skeleton-top-action {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 26px;
}

.skeleton-create-button {
  width: 185px;
  height: 44px;
  border-radius: 10px;
}

.skeleton-summary-icon {
  width: 48px;
  height: 48px;
  border-radius: 11px;
  flex-shrink: 0;
}

.skeleton-summary-content {
  flex: 1;
  min-width: 0;
}

.skeleton-label {
  width: 120px;
  height: 9px;
  margin-bottom: 9px;
}

.skeleton-number {
  width: 62px;
  height: 26px;
}

.skeleton-filter-card {
  align-items: flex-end;
}

.skeleton-filter-group {
  width: 180px;
}

.skeleton-filter-group.wide {
  width: 220px;
}

.skeleton-filter-label {
  width: 78px;
  height: 9px;
  margin-bottom: 7px;
}

.skeleton-filter-input {
  width: 100%;
  height: 42px;
  border-radius: 9px;
}

.skeleton-filter-button {
  width: 132px;
  height: 42px;
  margin-left: auto;
  border-radius: 9px;
}

.skeleton-quick-search-row {
  display: flex;
  justify-content: flex-end;
}

.skeleton-quick-search {
  width: 290px;
  height: 36px;
  border-radius: 999px 999px 0 0;
}

.skeleton-footer-info {
  width: 100px;
  height: 10px;
}

.skeleton-pagination {
  width: 112px;
  height: 32px;
  border-radius: 8px;
}

/* ============================= */
/* TABLE SKELETON */
/* ============================= */

.skeleton-row td {
  height: 92px;
}

.skeleton-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton {
  position: relative;
  overflow: hidden;
  border-radius: 6px;
  background: #edf1f6;
}

.skeleton::after {
  content: '';
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.72),
    transparent
  );
  animation: skeleton-shimmer 1.25s infinite;
}

.skeleton-title {
  width: 150px;
  height: 14px;
}

.skeleton-subtitle {
  width: 95px;
  height: 8px;
}

.skeleton-text {
  height: 12px;
}

.skeleton-text.medium {
  width: 120px;
}

.skeleton-text.short {
  width: 72px;
}

.skeleton-progress {
  width: 90px;
  height: 4px;
  border-radius: 999px;
}

.skeleton-pill {
  width: 74px;
  height: 27px;
  border-radius: 999px;
}

.skeleton-button {
  width: 78px;
  height: 31px;
  border-radius: 7px;
}

@keyframes skeleton-shimmer {
  100% {
    transform: translateX(100%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton::after,
  .spin {
    animation: none;
  }
}

/* ============================= */
/* IMPORT PARTICIPANTS MODAL */
/* ============================= */

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1200;
  padding: 22px;
  display: grid;
  place-items: center;
  background: rgba(15, 23, 42, 0.34);
}

.import-modal {
  width: min(650px, 100%);
  max-height: 90vh;
  overflow-y: auto;
  padding: 22px;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 24px 65px rgba(15, 23, 42, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.modal-eyebrow {
  margin: 0 0 5px;
  color: #8da0ba;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.modal-header h2 {
  margin: 0;
  color: #1b283d;
  font-size: 21px;
}

.selected-activity {
  margin: 7px 0 0;
  color: #53647c;
  font-size: 13px;
  font-weight: 600;
}

.selected-activity span {
  color: #96a5b9;
  font-weight: 500;
}

.modal-close {
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: #f3f6f9;
  color: #75869d;
  cursor: pointer;
}

.file-dropzone {
  min-height: 170px;
  padding: 24px;
  border: 1.5px dashed #cad7e8;
  border-radius: 13px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #fafcff;
  color: #2b75e9;
  cursor: pointer;
}

.file-dropzone strong {
  color: #34445c;
  font-size: 14px;
}

.file-dropzone span {
  color: #92a2b8;
  font-size: 12px;
}

.import-message {
  margin-top: 14px;
  padding: 11px 13px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.import-message.error {
  background: #fff1f1;
  color: #bd3c3c;
}

.import-message.success {
  background: #ebf8f1;
  color: #26835a;
}

.preview-panel {
  margin-top: 16px;
  border: 1px solid #e4eaf2;
  border-radius: 12px;
  overflow: hidden;
}

.preview-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  background: #f8fafc;
  border-bottom: 1px solid #e8edf4;
}

.preview-summary > div {
  padding: 13px 15px;
}

.preview-summary span {
  display: block;
  color: #94a4b8;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.07em;
}

.preview-summary strong {
  display: block;
  margin-top: 3px;
  color: #24344a;
  font-size: 18px;
}

.preview-table-wrapper {
  overflow-x: auto;
}

.preview-table {
  min-width: 520px;
}

.preview-table th,
.preview-table td {
  height: auto;
  padding: 10px 13px;
  font-size: 11px;
}

.preview-note {
  margin: 0;
  padding: 9px 13px 12px;
  color: #8b9bb0;
  font-size: 10px;
}

.modal-actions {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
  gap: 9px;
  flex-wrap: wrap;
}

.modal-secondary-button,
.modal-preview-button,
.modal-confirm-button {
  min-height: 39px;
  padding: 0 14px;
  border: 0;
  border-radius: 9px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  font-family: inherit;
  font-weight: 700;
  cursor: pointer;
}

.modal-secondary-button {
  border: 1px solid #dfe6ef;
  background: #fff;
  color: #526279;
}

.modal-preview-button {
  background: #edf4ff;
  color: #1769dc;
}

.modal-confirm-button {
  background: #8613bd;
  color: #fff;
}

.modal-secondary-button:disabled,
.modal-preview-button:disabled,
.modal-confirm-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}


.add-student-modal {
  width: min(580px, 100%);
  overflow: visible;
}

.manual-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.manual-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.manual-form label > span {
  color: #66758c;
  font-size: 11px;
  font-weight: 700;
}

.manual-form input {
  width: 100%;
  height: 42px;
  padding: 0 12px;
  border: 1px solid #dce5ef;
  border-radius: 9px;
  outline: none;
  background: #fff;
  color: #34445a;
  font: inherit;
  font-size: 13px;
}

.manual-form input:focus {
  border-color: #7bb1f5;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}


.major-select {
  position: relative;
  width: 100%;
}

.major-select-button {
  width: 100%;
  min-height: 42px;
  padding: 0 12px;
  border: 1px solid #dce5ef;
  border-radius: 9px;
  background: #fff;
  color: #34445a;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font: inherit;
  font-size: 13px;
  text-align: left;
  cursor: pointer;
}

.major-select-button:hover {
  border-color: #c8d5e6;
}

.major-select-button:focus {
  outline: none;
  border-color: #7bb1f5;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

.major-select-button .placeholder {
  color: #98a5b7;
}

.major-select-button svg {
  flex-shrink: 0;
  color: #7b8da5;
  transition: transform 0.2s ease;
}

.major-select-button svg.rotated {
  transform: rotate(180deg);
}

.major-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: 1400;

  max-height: 230px;
  overflow-y: auto;

  padding: 6px;
  border: 1px solid #dce5ef;
  border-radius: 10px;
  background: #fff;

  box-shadow: 0 14px 35px rgba(15, 23, 42, 0.15);
}

.major-option {
  width: 100%;
  min-height: 36px;
  padding: 8px 10px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: #46566d;
  display: flex;
  align-items: center;
  font: inherit;
  font-size: 12px;
  text-align: left;
  cursor: pointer;
}

.major-option:hover {
  background: #f2f6fb;
  color: #1769dc;
}


.role-select {
  position: relative;
  width: 100%;
}

.role-select-button {
  width: 100%;
  min-height: 42px;
  padding: 0 12px;
  border: 1px solid #dce5ef;
  border-radius: 9px;
  background: #fff;
  color: #34445a;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font: inherit;
  font-size: 13px;
  text-align: left;
  cursor: pointer;
}

.role-select-button:hover {
  border-color: #c8d5e6;
}

.role-select-button:focus {
  outline: none;
  border-color: #7bb1f5;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

.role-select-button svg {
  flex-shrink: 0;
  color: #7b8da5;
  transition: transform 0.2s ease;
}

.role-select-button svg.rotated {
  transform: rotate(180deg);
}

.role-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: 1400;

  padding: 6px;
  border: 1px solid #dce5ef;
  border-radius: 10px;
  background: #fff;

  box-shadow: 0 14px 35px rgba(15, 23, 42, 0.15);
}

.role-option {
  width: 100%;
  min-height: 36px;
  padding: 8px 10px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: #46566d;
  display: flex;
  align-items: center;
  font: inherit;
  font-size: 12px;
  text-align: left;
  cursor: pointer;
}

.role-option:hover,
.role-option.selected {
  background: #f2f6fb;
  color: #1769dc;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

@media (max-width: 1000px) {
  .skeleton-filter-card {
    flex-wrap: wrap;
  }

  .skeleton-filter-button {
    margin-left: 0;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .filter-card {
    flex-wrap: wrap;
  }

  .filter-button {
    margin-left: 0;
  }
}

@media (max-width: 700px) {
  .skeleton-filter-group,
  .skeleton-filter-group.wide,
  .skeleton-filter-button,
  .skeleton-quick-search {
    width: 100%;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .activities-page {
    padding: 20px 14px 32px;
  }

  .top-action {
    justify-content: stretch;
  }

  .create-button {
    width: 100%;
    justify-content: center;
  }

  .filter-field,
  .filter-field.search-activity {
    width: 100%;
  }

  .filter-button {
    width: 100%;
    justify-content: center;
  }

  .quick-search {
    width: 100%;
  }

  .table-footer {
    gap: 12px;
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>