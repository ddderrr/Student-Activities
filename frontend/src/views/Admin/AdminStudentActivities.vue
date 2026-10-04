<script setup>
import { computed, onMounted, ref, watch } from 'vue'
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
  ChevronDown,
  Settings2,
  Pencil,
  CircleCheckBig,
  RotateCcw,
  Ban,
  Trash2,
  Download,
  ArrowDown,
  ArrowUp
} from 'lucide-vue-next'
import SkillLevelEditor from '../../components/Admin/SkillLevelEditor.vue'
import BranchFilterSelect from '../../components/common/BranchFilterSelect.vue'
import { ALL_BRANCHES_VALUE } from '../../constants/branches'
import {
  PARTICIPANT_SKILLS,
  SKILLS_BY_ROLE,
  STAFF_SKILLS,
  skillLevelsFromSaved
} from '../../constants/activitySkills'
import { useLanguage } from '../../composables/useLanguage'
import { validHours } from '../../utils/activityHours'
import { API_BASE } from '../../config/api'
import { adminFetch } from '../../constants/currentAdmin'

const { t } = useLanguage()

const searchText = ref('')
const activitiesError = ref('')
// filter สาขา สำหรับแอดมินกลางเท่านั้น (BranchFilterSelect ซ่อนตัวเองให้แอดมินสาขา)
const selectedBranch = ref(ALL_BRANCHES_VALUE)
const quickSearch = ref('')

// เรียงตาราง: latest = created_at, start = start_at (ค่าเริ่มต้น: รายการล่าสุดขึ้นก่อน)
const sortField = ref('latest')
const sortDirection = ref('desc')
const selectedCategory = ref('all')
const selectedDate = ref('')
const showFilterCalendar = ref(false)
const filterCalendarCursor = ref(new Date())
const filterWeekDays = computed(() => [
  t.value.adminStudentActivities.weekdayMon,
  t.value.adminStudentActivities.weekdayTue,
  t.value.adminStudentActivities.weekdayWed,
  t.value.adminStudentActivities.weekdayThu,
  t.value.adminStudentActivities.weekdayFri,
  t.value.adminStudentActivities.weekdaySat,
  t.value.adminStudentActivities.weekdaySun
])

const filterCalendarTitle = computed(() =>
  new Intl.DateTimeFormat('th-TH-u-ca-gregory', {
    month: 'long',
    year: 'numeric'
  }).format(filterCalendarCursor.value)
)

const filterCalendarDays = computed(() => {
  const year = filterCalendarCursor.value.getFullYear()
  const month = filterCalendarCursor.value.getMonth()
  const firstDay = new Date(year, month, 1)
  const mondayOffset = (firstDay.getDay() + 6) % 7
  const gridStart = new Date(year, month, 1 - mondayOffset)

  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(
      gridStart.getFullYear(),
      gridStart.getMonth(),
      gridStart.getDate() + index
    )

    return {
      date,
      key: filterDateKey(date),
      day: date.getDate(),
      outside: date.getMonth() !== month
    }
  })
})

function filterDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function parseFilterDate(value) {
  if (!value) return null
  const [year, month, day] = value.split('-').map(Number)
  if (!year || !month || !day) return null
  return new Date(year, month - 1, day)
}

function formatFilterDate(value) {
  const date = parseFilterDate(value)
  if (!date) return t.value.adminStudentActivities.filterDatePlaceholder

  return new Intl.DateTimeFormat('th-TH-u-ca-gregory', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  }).format(date)
}

function openFilterCalendar() {
  showFilterCalendar.value = !showFilterCalendar.value
  if (showFilterCalendar.value) {
    filterCalendarCursor.value = parseFilterDate(selectedDate.value) || new Date()
  }
}

function changeFilterMonth(offset) {
  const current = filterCalendarCursor.value
  filterCalendarCursor.value = new Date(
    current.getFullYear(),
    current.getMonth() + offset,
    1
  )
}

function isFilterDateSelected(day) {
  return day.key === selectedDate.value
}

function isFilterToday(day) {
  return day.key === filterDateKey(new Date())
}

function selectFilterDate(day) {
  selectedDate.value = day.key
  showFilterCalendar.value = false
  applyFilters()
}

function selectFilterToday() {
  selectedDate.value = filterDateKey(new Date())
  showFilterCalendar.value = false
  applyFilters()
}

function clearFilterDate() {
  selectedDate.value = ''
  showFilterCalendar.value = false
  applyFilters()
}

const currentPage = ref(1)
const rowsPerPage = 10
const router = useRouter()
// Loading states
// pageLoading = ใช้ตอนเปิด/refresh หน้า เพื่อทำ Skeleton ทั้งหน้า
// tableLoading = ใช้ตอน reload เฉพาะตารางในอนาคต
const pageLoading = ref(true)
const tableLoading = ref(true)
const skeletonRows = Array.from({ length: rowsPerPage }, (_, index) => index)


const roleOptions = computed(() => [
  { value: 'participant', label: t.value.adminStudentActivities.participantLabel },
  { value: 'organizer', label: t.value.adminStudentActivities.organizerLabel }
])


// Import participants modal state
const showImportModal = ref(false)

/* =========================
   Template สำหรับ import ผู้เข้าร่วม
   สร้างไฟล์ .xlsx ฝั่ง frontend (SheetJS) หัวคอลัมน์ต้องตรงกับ COLUMN_ALIASES ใน backend
========================= */
const IMPORT_TEMPLATE_HEADERS = ['รหัสนักศึกษา', 'ชื่อ', 'นามสกุล', 'อีเมล', 'สาขาวิชา']
const IMPORT_TEMPLATE_EXAMPLES = [
  ['670510101', 'สมชาย', 'ใจดี', '670510101@cmu.ac.th', 'วิทยาการคอมพิวเตอร์'],
  ['670510201', 'สมหญิง', 'รักเรียน', '670510201@cmu.ac.th', 'เคมี']
]
const templateDownloading = ref(false)

async function downloadImportTemplate() {
  if (templateDownloading.value) return
  templateDownloading.value = true

  try {
    // โหลด SheetJS ตอนกดเท่านั้น ไม่ให้หน้า Activities หนักขึ้น
    const XLSX = await import('xlsx')
    const sheet = XLSX.utils.aoa_to_sheet([IMPORT_TEMPLATE_HEADERS, ...IMPORT_TEMPLATE_EXAMPLES])

    // รหัสนักศึกษาเป็นข้อความ: Excel ไม่ตัดเลขศูนย์นำหน้า / ไม่แปลงเป็น 6.7E+08
    for (let row = 1; row <= IMPORT_TEMPLATE_EXAMPLES.length; row += 1) {
      const cell = sheet[XLSX.utils.encode_cell({ r: row, c: 0 })]
      if (cell) {
        cell.t = 's'
        cell.z = '@'
      }
    }
    sheet['!cols'] = [{ wch: 16 }, { wch: 18 }, { wch: 18 }, { wch: 28 }, { wch: 26 }]

    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, sheet, 'students')
    XLSX.writeFile(workbook, 'participant-import-template.xlsx')
  } catch {
    importError.value = t.value.adminStudentActivities.downloadTemplateError
  } finally {
    templateDownloading.value = false
  }
}
const selectedActivity = ref(null)
const selectedFiles = ref([])
const importFileInput = ref(null)
const isDraggingFile = ref(false)
const importPreview = ref(null)
const importError = ref('')
const importLoading = ref(false)
const confirmLoading = ref(false)
const importSuccess = ref('')
const showImportIssues = ref(false)

// Manage participants / activities
const openManageMenuId = ref(null)
const openActivityMenuId = ref(null)

const showEditActivityModal = ref(false)
const editActivityLoading = ref(false)
const editActivityError = ref('')
const activityActionLoadingId = ref(null)

const editActivityForm = ref({
  name: '',
  activity_hours: 0,
  activity_type: '',
  start_at: '',
  end_at: '',
  department: '',
  responsible_person: '',
  advisor: '',
  location: '',
  description: '',
  status: 'active',
  staff_skills: {},
  participant_skills: {}
})

const editSkillTarget = ref('staff')

// แถว Skill ที่เปิดดูอยู่ในตารางกิจกรรม
const expandedSkillsId = ref(null)

function toggleSkillsRow(activityId) {
  expandedSkillsId.value =
    expandedSkillsId.value === activityId ? null : activityId
}

function activitySkillList(activity, role) {
  const saved = activity[`${role}_skills`] || {}

  return SKILLS_BY_ROLE[role]
    .filter((skill) => saved[skill.key] !== undefined)
    .map((skill) => ({
      key: skill.key,
      label: skill.label,
      level: saved[skill.key]
    }))
}

function skillCount(activity, role) {
  return Object.keys(activity[`${role}_skills`] || {}).length
}

const showAddStudentModal = ref(false)
const addStudentLoading = ref(false)
const addStudentError = ref('')
const addStudentSuccess = ref('')
const showRoleDropdown = ref(false)

const manualStudent = ref({
  student_id: '',
  first_name: '',
  last_name: '',
  email: '',
  faculty: '',
  major: '',
  role: 'participant'
})

// เพิ่ม Participant แบบพิมพ์รหัสนักศึกษา/ค้นหาชื่อ: ดึงชื่อ/คณะ/สาขาจาก
// database มาเติมให้อัตโนมัติ (ไม่ให้พิมพ์เองแล้ว เพื่อกันพิมพ์ผิด/major ไม่ตรง
// กับข้อมูลจริงเหมือนฟอร์มเดิม)
const studentQuery = ref('')
const studentSuggestions = ref([])
const showStudentSuggestions = ref(false)
const studentLookupStatus = ref('idle') // idle | loading | found | not_found
let studentSearchTimer = null

function clearStudentLookup() {
  studentQuery.value = ''
  studentSuggestions.value = []
  showStudentSuggestions.value = false
  studentLookupStatus.value = 'idle'
  manualStudent.value.student_id = ''
  manualStudent.value.first_name = ''
  manualStudent.value.last_name = ''
  manualStudent.value.email = ''
  manualStudent.value.faculty = ''
  manualStudent.value.major = ''
}

function applyStudentLookupResult(student) {
  studentQuery.value = `${student.student_id} - ${student.first_name} ${student.last_name}`
  manualStudent.value.student_id = student.student_id
  manualStudent.value.first_name = student.first_name
  manualStudent.value.last_name = student.last_name
  manualStudent.value.email = student.email || ''
  manualStudent.value.faculty = student.faculty || ''
  manualStudent.value.major = student.major || ''
  studentLookupStatus.value = 'found'
}

function selectStudentSuggestion(student) {
  showStudentSuggestions.value = false
  studentSuggestions.value = []
  applyStudentLookupResult(student)
}

function onStudentQueryInput() {
  addStudentError.value = ''
  studentLookupStatus.value = 'idle'
  manualStudent.value.student_id = ''
  manualStudent.value.first_name = ''
  manualStudent.value.last_name = ''
  manualStudent.value.email = ''
  manualStudent.value.faculty = ''
  manualStudent.value.major = ''

  clearTimeout(studentSearchTimer)

  const keyword = studentQuery.value.trim()

  if (!keyword) {
    studentSuggestions.value = []
    showStudentSuggestions.value = false
    return
  }

  studentSearchTimer = setTimeout(async () => {
    try {
      const response = await adminFetch(
        `${API_BASE}/api/admin/students/search?q=${encodeURIComponent(keyword)}`
      )

      if (!response.ok) return

      const data = await response.json()
      studentSuggestions.value = data.students || []
      showStudentSuggestions.value = studentSuggestions.value.length > 0
    } catch {
      // เงียบไว้: พิมพ์รหัสตรง ๆ แล้ว blur ยัง trigger lookup แบบเต็มได้อยู่
    }
  }, 250)
}

// พิมพ์รหัสนักศึกษาตรง ๆ แล้ว blur/submit โดยไม่ได้กดเลือกจาก suggestion
async function confirmStudentLookup() {
  const keyword = studentQuery.value.trim()

  if (!keyword || studentLookupStatus.value === 'found') return

  studentLookupStatus.value = 'loading'
  showStudentSuggestions.value = false

  try {
    const response = await adminFetch(
      `${API_BASE}/api/admin/students/lookup?student_id=${encodeURIComponent(keyword)}`
    )

    if (response.status === 404) {
      studentLookupStatus.value = 'not_found'
      return
    }

    if (!response.ok) {
      studentLookupStatus.value = 'not_found'
      return
    }

    applyStudentLookupResult(await response.json())
  } catch {
    studentLookupStatus.value = 'not_found'
  }
}

const activities = ref([])

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
      String(activity.name || '').toLowerCase().includes(mainKeyword)

    const matchQuick =
      !quickKeyword ||
      String(activity.name || '').toLowerCase().includes(quickKeyword) ||
      String(activity.organizer || '').toLowerCase().includes(quickKeyword)

    const matchCategory =
      selectedCategory.value === 'all' ||
      activity.category === selectedCategory.value

    const matchDate =
      !selectedDate.value ||
      dateOnly(activity.start_at) === selectedDate.value

    return matchMain && matchQuick && matchCategory && matchDate
  })
})

function sortTime(value) {
  const time = value ? new Date(value).getTime() : NaN
  return Number.isNaN(time) ? 0 : time
}

const sortedActivities = computed(() => {
  const key = sortField.value === 'start' ? 'start_at' : 'created_at'
  const direction = sortDirection.value === 'asc' ? 1 : -1

  // id เป็นตัวตัดสินเมื่อเวลาเท่ากัน ลำดับจึงไม่สลับไปมาตอนโหลดใหม่
  return [...filteredActivities.value].sort((a, b) =>
    (sortTime(a[key]) - sortTime(b[key]) || a.id - b.id) * direction
  )
})

function setSortField(field) {
  sortField.value = field
  // รายการล่าสุด = ใหม่ก่อน, วันที่เริ่ม = เริ่มก่อนขึ้นก่อน
  sortDirection.value = field === 'latest' ? 'desc' : 'asc'
  currentPage.value = 1
}

function toggleSortDirection() {
  sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  currentPage.value = 1
}

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredActivities.value.length / rowsPerPage))
)

const paginatedActivities = computed(() => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value
  }

  const start = (currentPage.value - 1) * rowsPerPage
  return sortedActivities.value.slice(start, start + rowsPerPage)
})

const monthlyParticipants = computed(() => {
  const now = new Date()
  const currentYear = now.getFullYear()
  const currentMonth = now.getMonth()

  return activities.value
    .filter((activity) => {
      const date = new Date(activity.start_at)
      return (
        date.getFullYear() === currentYear &&
        date.getMonth() === currentMonth
      )
    })
    .reduce((sum, activity) => sum + activity.participants, 0)
})

const activeActivities = computed(
  () =>
    activities.value.filter(
      (activity) => (activity.status || 'active') === 'active'
    ).length
)

// จำนวนคำขอประเภท Skill Validation ที่รออนุมัติ
const pendingEvaluations = ref(null)

async function fetchPendingEvaluations() {
  try {
    const params = new URLSearchParams({
      status: 'pending',
      request_type: 'skill_validation',
      page_size: '1'
    })

    const response = await adminFetch(`${API_BASE}/api/requests?${params}`)
    if (!response.ok) throw new Error('ไม่สามารถโหลดจำนวนคำขอที่รออนุมัติได้')

    const data = await response.json()
    pendingEvaluations.value = data.total ?? 0
  } catch (error) {
    console.error(error)
    pendingEvaluations.value = null
  }
}

function applyFilters() {
  currentPage.value = 1
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function formatDate(dateString) {
  if (!dateString) return '-'

  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return '-'

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: '2-digit',
    year: 'numeric'
  }).format(date)
}

function formatTime(dateString) {
  if (!dateString) return ''

  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return ''

  const pad = (number) => String(number).padStart(2, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function dateOnly(value) {
  if (!value) return ''

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
}

function toDateTimeLocal(value) {
  if (!value) return ''

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''

  const pad = (number) => String(number).padStart(2, '0')

  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  )
}

function statusLabel(status) {
  const labels = {
    active: t.value.adminStudentActivities.statusActive,
    completed: t.value.adminStudentActivities.statusCompleted,
    cancelled: t.value.adminStudentActivities.statusCancelled
  }

  return labels[status || 'active'] || status
}

function statusClass(status) {
  return `status-${status || 'active'}`
}

function participantPercent(activity) {
  if (!activity.capacity) return 0
  return Math.min(100, (activity.participants / activity.capacity) * 100)
}

async function fetchActivities() {
  activitiesError.value = ''
  pageLoading.value = true
  tableLoading.value = true

  try {
    const params = new URLSearchParams()
    if (selectedBranch.value !== ALL_BRANCHES_VALUE) {
      params.set('major', selectedBranch.value)
    }

    const response = await adminFetch(`${API_BASE}/api/activities?${params.toString()}`)
    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(data.detail || 'ไม่สามารถโหลดกิจกรรมได้')
    }

    activities.value = data.activities || []
  } catch (error) {
    console.error(error)
    activitiesError.value = error.message || t.value.adminStudentActivities.backendConnectionError
    activities.value = []
  } finally {
    pageLoading.value = false
    tableLoading.value = false
  }
}

onMounted(() => {
  fetchActivities()
  fetchPendingEvaluations()
})

// แอดมินกลางเปลี่ยน filter สาขา -> โหลดรายการกิจกรรมใหม่ตามสาขาที่เลือก
watch(selectedBranch, () => {
  currentPage.value = 1
  fetchActivities()
})

function createActivity() {
  router.push('/admin/activities/create')
}

function viewActivity(activity) {
  router.push(`/admin/activities/${activity.id}/details`)
}

function toggleManageMenu(activityId) {
  openActivityMenuId.value = null

  openManageMenuId.value =
    openManageMenuId.value === activityId
      ? null
      : activityId
}

function toggleActivityMenu(activityId) {
  openManageMenuId.value = null

  openActivityMenuId.value =
    openActivityMenuId.value === activityId
      ? null
      : activityId
}

function openEditActivity(activity) {
  openActivityMenuId.value = null
  editActivityError.value = ''

  editActivityForm.value = {
    name: activity.name || '',
    activity_hours: activity.activity_hours ?? 0,
    activity_type: activity.activity_type || activity.category || '',
    start_at: toDateTimeLocal(activity.start_at),
    end_at: toDateTimeLocal(activity.end_at),
    department: activity.department || '',
    responsible_person: activity.responsible_person || '',
    advisor: activity.advisor || '',
    location: activity.location || '',
    description: activity.description || '',
    status: activity.status || 'active',
    staff_skills: skillLevelsFromSaved(STAFF_SKILLS, activity.staff_skills),
    participant_skills: skillLevelsFromSaved(PARTICIPANT_SKILLS, activity.participant_skills)
  }

  editSkillTarget.value = 'staff'

  selectedActivity.value = activity
  showEditActivityModal.value = true
}

function closeEditActivityModal() {
  if (editActivityLoading.value) return

  showEditActivityModal.value = false
  editActivityError.value = ''
  selectedActivity.value = null
}

async function patchActivity(activityId, payload) {
  const response = await adminFetch(
    `${API_BASE}/api/activities/${activityId}`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    }
  )

  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.detail || t.value.adminStudentActivities.editActivityFailedDefault)
  }

  const index = activities.value.findIndex(
    (activity) => activity.id === activityId
  )

  if (index !== -1) {
    activities.value[index] = data
  }

  return data
}

async function saveActivityEdits() {
  if (!selectedActivity.value) return

  const form = editActivityForm.value
  if (!validHours(form.activity_hours, true)) {
    editActivityError.value = t.value.activityHours.invalidEdit
    return
  }

  if (
    !form.name.trim() ||
    !form.activity_type.trim() ||
    !form.start_at ||
    !form.end_at ||
    !form.responsible_person.trim() ||
    !form.location.trim()
  ) {
    editActivityError.value =
      t.value.adminStudentActivities.editActivityValidationError
    return
  }

  editActivityLoading.value = true
  editActivityError.value = ''

  try {
    await patchActivity(selectedActivity.value.id, {
      name: form.name.trim(),
      activity_type: form.activity_type.trim(),
      start_at: form.start_at,
      end_at: form.end_at,
      department: form.department.trim(),
      responsible_person: form.responsible_person.trim(),
      advisor: form.advisor.trim(),
      location: form.location.trim(),
      description: form.description.trim(),
      activity_hours: Number(form.activity_hours),
      status: form.status,
      staff_skills: form.staff_skills,
      participant_skills: form.participant_skills
    })

    showEditActivityModal.value = false
    selectedActivity.value = null
  } catch (error) {
    editActivityError.value =
      error.message || t.value.adminStudentActivities.backendConnectionError
  } finally {
    editActivityLoading.value = false
  }
}

async function setActivityStatus(activity, status) {
  openActivityMenuId.value = null
  activityActionLoadingId.value = activity.id

  try {
    await patchActivity(activity.id, { status })
  } catch (error) {
    window.alert(error.message || t.value.adminStudentActivities.changeStatusFailedDefault)
  } finally {
    activityActionLoadingId.value = null
  }
}

async function deleteActivity(activity) {
  openActivityMenuId.value = null

  const confirmed = window.confirm(
    t.value.adminStudentActivities.deleteActivityConfirm.replace('{name}', activity.name)
  )

  if (!confirmed) return

  activityActionLoadingId.value = activity.id

  try {
    const response = await adminFetch(
      `${API_BASE}/api/activities/${activity.id}`,
      {
        method: 'DELETE'
      }
    )

    if (!response.ok) {
      let detail = t.value.adminStudentActivities.deleteActivityFailedDefault

      try {
        const data = await response.json()
        detail = data.detail || detail
      } catch {
        // 204 / response ที่ไม่มี JSON
      }

      throw new Error(detail)
    }

    activities.value = activities.value.filter(
      (item) => item.id !== activity.id
    )
  } catch (error) {
    window.alert(error.message || t.value.adminStudentActivities.backendConnectionError)
  } finally {
    activityActionLoadingId.value = null
  }
}

function openAddStudent(activity) {
  selectedActivity.value = activity
  openManageMenuId.value = null
  openActivityMenuId.value = null

  clearStudentLookup()
  manualStudent.value.role = 'participant'

  addStudentError.value = ''
  addStudentSuccess.value = ''
  showRoleDropdown.value = false
  showAddStudentModal.value = true
}

function closeAddStudentModal() {
  if (addStudentLoading.value) return

  showAddStudentModal.value = false
  showRoleDropdown.value = false
  selectedActivity.value = null
  addStudentError.value = ''
  addStudentSuccess.value = ''
}

function selectRole(role) {
  manualStudent.value.role = role.value
  showRoleDropdown.value = false
}

function roleLabel(value) {
  return (
    roleOptions.value.find((role) => role.value === value)?.label ||
    t.value.adminStudentActivities.selectRolePlaceholder
  )
}

async function addStudentManually() {
  if (!selectedActivity.value) return

  // ยังไม่ได้ยืนยันด้วย lookup (เช่น พิมพ์รหัสแล้วกด Add ทันทีโดยไม่ blur)
  if (studentLookupStatus.value === 'idle' || studentLookupStatus.value === 'loading') {
    await confirmStudentLookup()
  }

  if (studentLookupStatus.value === 'not_found') {
    addStudentError.value = t.value.adminStudentActivities.studentIdNotFoundError
    return
  }

  if (studentLookupStatus.value !== 'found') {
    addStudentError.value =
      t.value.adminStudentActivities.addStudentValidationError
    return
  }

  const student = {
    student_id: manualStudent.value.student_id.trim(),
    first_name: manualStudent.value.first_name.trim(),
    last_name: manualStudent.value.last_name.trim(),
    email: manualStudent.value.email.trim(),
    faculty: manualStudent.value.faculty.trim(),
    major: manualStudent.value.major.trim(),
    role: manualStudent.value.role
  }

  addStudentLoading.value = true
  addStudentError.value = ''
  addStudentSuccess.value = ''

  try {
    const response = await adminFetch(
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
      throw new Error(data.detail || t.value.adminStudentActivities.addStudentFailedDefault)
    }

    selectedActivity.value.participants = data.total_participants

    if (data.duplicate_count > 0) {
      addStudentError.value =
        t.value.adminStudentActivities.studentAlreadyInActivity
      return
    }

    addStudentSuccess.value = t.value.adminStudentActivities.addStudentSuccessMessage

    clearStudentLookup()
    manualStudent.value.role = 'participant'
  } catch (error) {
    addStudentError.value =
      error.message || t.value.adminStudentActivities.backendConnectionError
  } finally {
    addStudentLoading.value = false
  }
}

function openImportParticipants(activity) {
  openManageMenuId.value = null
  openActivityMenuId.value = null
  importParticipants(activity)
}

function importParticipants(activity) {
  selectedActivity.value = activity
  selectedFiles.value = []
  isDraggingFile.value = false
  importPreview.value = null
  importError.value = ''
  importSuccess.value = ''
  showImportIssues.value = false
  showImportModal.value = true
}

function closeImportModal() {
  if (importLoading.value || confirmLoading.value) return

  showImportModal.value = false
  selectedActivity.value = null
  selectedFiles.value = []
  isDraggingFile.value = false
  importPreview.value = null
  importError.value = ''
  importSuccess.value = ''
  showImportIssues.value = false
}

function resetImportPreviewState() {
  importPreview.value = null
  importError.value = ''
  importSuccess.value = ''
  showImportIssues.value = false
}

function backToImportFiles() {
  if (importLoading.value || confirmLoading.value) return
  resetImportPreviewState()
}

function isSupportedImportFile(file) {
  const name = file?.name?.toLowerCase() || ''
  return name.endsWith('.csv') || name.endsWith('.xlsx') || name.endsWith('.xls')
}

function addImportFiles(fileList) {
  const incomingFiles = Array.from(fileList || [])
  if (!incomingFiles.length) return

  const supportedFiles = incomingFiles.filter(isSupportedImportFile)
  const rejectedFiles = incomingFiles.filter((file) => !isSupportedImportFile(file))

  const existingKeys = new Set(
    selectedFiles.value.map(
      (file) => `${file.name}-${file.size}-${file.lastModified}`
    )
  )

  const uniqueFiles = supportedFiles.filter((file) => {
    const key = `${file.name}-${file.size}-${file.lastModified}`
    if (existingKeys.has(key)) return false
    existingKeys.add(key)
    return true
  })

  selectedFiles.value = [...selectedFiles.value, ...uniqueFiles]
  resetImportPreviewState()

  if (rejectedFiles.length) {
    importError.value = t.value.adminStudentActivities.unsupportedFileTypeError
  }
}

function openImportFilePicker() {
  if (importLoading.value || confirmLoading.value) return
  importFileInput.value?.click()
}

function handleImportFile(event) {
  addImportFiles(event.target.files)
  event.target.value = ''
}

function handleImportDrop(event) {
  isDraggingFile.value = false
  addImportFiles(event.dataTransfer?.files)
}

function removeImportFile(index) {
  selectedFiles.value.splice(index, 1)
  resetImportPreviewState()
}

function toggleImportIssues() {
  if (!importIssueCount.value) return
  showImportIssues.value = !showImportIssues.value
}

const IMPORT_EDITABLE_FIELDS = ['student_id', 'first_name', 'last_name', 'email', 'major']
const IMPORT_ROLES = ['participant', 'organizer']

const importEditableColumns = computed(() => [
  { field: 'student_id', label: t.value.adminStudentActivities.previewTableStudentId, width: '130px' },
  { field: 'first_name', label: t.value.adminStudentActivities.previewTableFirstName, width: '150px' },
  { field: 'last_name', label: t.value.adminStudentActivities.previewTableLastName, width: '150px' },
  { field: 'email', label: t.value.adminStudentActivities.previewTableEmail, width: '220px' },
  { field: 'major', label: t.value.adminStudentActivities.previewTableMajor, width: '160px' }
])

/*
  ตรวจข้อมูลทุกแถวใน preview ใหม่ทุกครั้งที่แก้ในตาราง
  ใช้กฎเดียวกับ validate_students ใน backend/main.py
  (+ ตรวจรหัสนักศึกษาซ้ำในรายการ)
  คืนค่าเป็น array ของ { field: ข้อความ error } ตามลำดับแถว
*/
const importRowErrors = computed(() => {
  const labels = t.value.adminStudentActivities
  const rowErrors = (importPreview.value?.students || []).map((student) => {
    const errors = {}
    const email = String(student.email ?? '').trim()

    if (!String(student.student_id ?? '').trim()) {
      errors.student_id = labels.importMissingStudentId
    }

    if (!String(student.first_name ?? '').trim()) {
      errors.first_name = labels.importMissingFirstName
    }

    if (!String(student.last_name ?? '').trim()) {
      errors.last_name = labels.importMissingLastName
    }

    if (!email) {
      if (student._requireEmail) errors.email = labels.importMissingEmail
    } else if (!email.includes('@')) {
      errors.email = labels.invalidEmailFormat
    }

    if (!IMPORT_ROLES.includes(student.role)) {
      errors.role = labels.importInvalidRole
    }

    return errors
  })

  // รหัสซ้ำ: นับเฉพาะแถวที่ไม่มีปัญหาอื่น แถวแรกที่ถูกต้องจะถูกนำเข้า
  // แถวถัดไปที่รหัสเดียวกันถือว่าซ้ำ (backend จะ error ถ้าส่งรหัสซ้ำไปพร้อมกัน)
  const seenStudentIds = new Set()

  importPreview.value?.students.forEach((student, index) => {
    if (Object.keys(rowErrors[index]).length) return

    const studentId = String(student.student_id).trim()

    if (seenStudentIds.has(studentId)) {
      rowErrors[index].student_id = labels.importDuplicateStudentId
    } else {
      seenStudentIds.add(studentId)
    }
  })

  return rowErrors
})

function importRowHasIssue(index) {
  return Object.keys(importRowErrors.value[index] || {}).length > 0
}

const importIssueList = computed(() =>
  (importPreview.value?.students || [])
    .map((student, index) => ({
      student,
      index,
      errors: Object.values(importRowErrors.value[index] || {})
    }))
    .filter((item) => item.errors.length)
)

const importIssueCount = computed(() => importIssueList.value.length)

function validPreviewStudents() {
  if (!importPreview.value) return []

  return importPreview.value.students.filter(
    (_student, index) => !importRowHasIssue(index)
  )
}

function cleanStudentForConfirm(student) {
  const {
    _requireEmail,
    _rowKey,
    _sourceFile,
    _sourceRow,
    ...cleanStudent
  } = student

  for (const field of IMPORT_EDITABLE_FIELDS) {
    cleanStudent[field] = String(cleanStudent[field] ?? '').trim()
  }

  return cleanStudent
}

async function previewParticipantsImport() {
  if (!selectedActivity.value) return

  if (!selectedFiles.value.length) {
    importError.value = t.value.adminStudentActivities.selectFileFirstError
    return
  }

  importLoading.value = true
  importError.value = ''
  importSuccess.value = ''
  showImportIssues.value = false

  try {
    const combinedPreview = {
      students: []
    }

    for (const [fileIndex, file] of selectedFiles.value.entries()) {
      const formData = new FormData()
      formData.append('file', file)

      const response = await adminFetch(
        `${API_BASE}/api/activities/${selectedActivity.value.id}/participants/import/preview`,
        {
          method: 'POST',
          body: formData
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(`${file.name}: ${data.detail || t.value.adminStudentActivities.fileReadFailedDefault}`)
      }

      const fileStudents = data.students || []
      // ไฟล์เช็คชื่อรุ่นเก่า (.xls) ไม่มี column email จึงไม่บังคับ (เหมือน backend)
      const requireEmail = !file.name.toLowerCase().endsWith('.xls')

      // ปัญหาของแต่ละแถวคำนวณใหม่ใน importRowErrors เพื่อให้แก้ข้อมูลในตารางแล้วอัปเดตทันที
      const normalizedStudents = fileStudents.map((student, index) => {
        const editableValues = Object.fromEntries(
          IMPORT_EDITABLE_FIELDS.map((field) => [field, String(student[field] ?? '')])
        )

        return {
          ...student,
          ...editableValues,
          role: String(student.role || 'participant').trim().toLowerCase(),
          _requireEmail: requireEmail,
          _rowKey: `${fileIndex}-${index}`,
          _sourceFile: file.name,
          _sourceRow: index + 2
        }
      })

      combinedPreview.students.push(...normalizedStudents)
    }

    importPreview.value = combinedPreview
  } catch (error) {
    importError.value = error.message || t.value.adminStudentActivities.backendConnectionError
  } finally {
    importLoading.value = false
  }
}

async function confirmParticipantsImport() {
  if (!selectedActivity.value || !importPreview.value) return

  const studentsToImport = validPreviewStudents()
  const skippedIssueCount = importIssueCount.value

  if (!studentsToImport.length) {
    importError.value =
      t.value.adminStudentActivities.noValidImportDataError
    return
  }

  confirmLoading.value = true
  importError.value = ''
  importSuccess.value = ''

  try {
    const response = await adminFetch(
      `${API_BASE}/api/activities/${selectedActivity.value.id}/participants/import/confirm`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          students: studentsToImport.map(cleanStudentForConfirm)
        })
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || t.value.adminStudentActivities.importFailedDefault)
    }

    selectedActivity.value.participants = data.total_participants

    importSuccess.value =
      t.value.adminStudentActivities.importSuccessMessage.replace(
        '{count}',
        data.imported_count
      ) +
      (data.duplicate_count
        ? t.value.adminStudentActivities.importSuccessDuplicateSuffix.replace(
            '{count}',
            data.duplicate_count
          )
        : '') +
      (skippedIssueCount
        ? t.value.adminStudentActivities.importSuccessIssueSuffix.replace(
            '{count}',
            skippedIssueCount
          )
        : '')
  } catch (error) {
    importError.value =
      error.message || t.value.adminStudentActivities.backendConnectionError
  } finally {
    confirmLoading.value = false
  }
}

const previewIssueNoteText = computed(() =>
  t.value.adminStudentActivities.previewIssueNote.replace(
    '{count}',
    importIssueCount.value
  )
)

const confirmImportButtonText = computed(() =>
  t.value.adminStudentActivities.confirmImportButton.replace(
    '{count}',
    validPreviewStudents().length
  )
)
</script>

<template>
  <section class="activities-page">
    <div v-if="!pageLoading && activitiesError" class="import-message error" role="alert">
      <TriangleAlert :size="17" />
      {{ activitiesError }}
      <button type="button" @click="fetchActivities">{{ t.adminLogin.retry }}</button>
    </div>

    <!-- FULL PAGE SKELETON -->
    <div
      v-if="pageLoading"
      class="page-skeleton"
      :aria-label="t.adminStudentActivities.loadingAriaLabel"
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
        <div
          class="table-scroll"
          :class="{
            'menu-open':
              openManageMenuId !== null ||
              openActivityMenuId !== null
          }"
        >
          <table>
            <thead>
              <tr>
                <th>{{ t.adminStudentActivities.tableHeaderActivityName }}</th>
                <th>{{ t.adminStudentActivities.tableHeaderOrganizer }}</th>
                <th>{{ t.adminStudentActivities.tableHeaderStartDate }}</th>
                <th>{{ t.adminStudentActivities.tableHeaderEndDate }}</th>
                <th>{{ t.adminStudentActivities.tableHeaderParticipants }}</th>
                <th>{{ t.adminStudentActivities.tableHeaderDetails }}</th>
                <th>{{ t.adminStudentActivities.tableHeaderManageParticipants }}</th>
                <th>{{ t.adminStudentActivities.tableHeaderManageActivity }}</th>
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
        {{ t.adminStudentActivities.createActivityButton }}
      </button>
    </div>

    <!-- SUMMARY -->
    <div class="summary-grid">
      <article class="summary-card summary-card-active">
        <div class="summary-icon blue">
          <Zap :size="25" />
        </div>

        <div>
          <span class="summary-label">{{ t.adminStudentActivities.summaryActiveActivities }}</span>
          <strong class="summary-value">{{ activeActivities }}</strong>
        </div>
      </article>

      <article class="summary-card">
        <div class="summary-icon">
          <Users :size="25" />
        </div>

        <div>
          <span class="summary-label">{{ t.adminStudentActivities.summaryParticipantsMonth }}</span>
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
          <span class="summary-label">{{ t.adminStudentActivities.summaryPendingEvaluations }}</span>
          <strong class="summary-value">{{ pendingEvaluations ?? '—' }}</strong>
        </div>
      </article>
    </div>

    <!-- FILTER -->
    <section class="filter-card">
      <div class="filter-field search-activity">
        <label>{{ t.adminStudentActivities.filterSearchActivityLabel }}</label>

        <div class="input-box">
          <Search :size="16" />
          <input
            v-model="searchText"
            type="text"
            :placeholder="t.adminStudentActivities.filterSearchActivityPlaceholder"
            @keyup.enter="applyFilters"
          />
        </div>
      </div>

      <div class="filter-field">
        <label>{{ t.adminStudentActivities.filterCategoryLabel }}</label>

        <select
          v-model="selectedCategory"
          @change="applyFilters"
        >
          <option value="all">{{ t.adminStudentActivities.filterAllCategoriesOption }}</option>
          <option
            v-for="category in categories"
            :key="category"
            :value="category"
          >
            {{ category }}
          </option>
        </select>
      </div>

      <BranchFilterSelect v-model="selectedBranch" />

      <div class="filter-field filter-date-field">
        <label>{{ t.adminStudentActivities.filterDateFromLabel }}</label>

        <div class="filter-date-picker" @click.stop>
          <button
            type="button"
            class="filter-date-trigger"
            :class="{ selected: selectedDate }"
            @click="openFilterCalendar"
          >
            <CalendarDays :size="16" />
            <span :class="{ placeholder: !selectedDate }">
              {{ formatFilterDate(selectedDate) }}
            </span>
          </button>

          <div v-if="showFilterCalendar" class="filter-calendar-popover">
            <div class="filter-calendar-header">
              <button type="button" @click="changeFilterMonth(-1)">
                <ChevronLeft :size="17" />
              </button>

              <strong>{{ filterCalendarTitle }}</strong>

              <button type="button" @click="changeFilterMonth(1)">
                <ChevronRight :size="17" />
              </button>
            </div>

            <div class="filter-calendar-weekdays">
              <span v-for="dayName in filterWeekDays" :key="dayName">
                {{ dayName }}
              </span>
            </div>

            <div class="filter-calendar-days">
              <button
                v-for="day in filterCalendarDays"
                :key="day.key"
                type="button"
                :class="{
                  outside: day.outside,
                  today: isFilterToday(day),
                  selected: isFilterDateSelected(day)
                }"
                @click="selectFilterDate(day)"
              >
                {{ day.day }}
              </button>
            </div>

            <div class="filter-calendar-footer">
              <button type="button" class="clear" @click="clearFilterDate">
                {{ t.adminStudentActivities.filterClearDate }}
              </button>
              <button type="button" @click="selectFilterToday">{{ t.adminStudentActivities.filterToday }}</button>
            </div>
          </div>
        </div>
      </div>

      <button class="filter-button" @click="applyFilters">
        <SlidersHorizontal :size="17" />
        {{ t.adminStudentActivities.applyFiltersButton }}
      </button>
    </section>

    <!-- QUICK SEARCH -->
    <div class="quick-search-row">
      <div class="quick-search">
        <Search :size="15" />
        <input
          v-model="quickSearch"
          type="text"
          :placeholder="t.adminStudentActivities.quickSearchPlaceholder"
          @input="currentPage = 1"
        />
      </div>
    </div>

    <!-- TABLE -->
    <section class="activities-table-card">
      <div
        class="table-scroll"
        :class="{
          'menu-open':
            openManageMenuId !== null ||
            openActivityMenuId !== null
        }"
      >
        <table>
          <thead>
            <tr>
              <th class="name-header">
                <div class="name-header-inner">
                  <span>{{ t.adminStudentActivities.tableHeaderActivityName }}</span>

                  <div class="sort-control" role="group" :aria-label="t.adminStudentActivities.sortAriaLabel">
                    <select
                      :value="sortField"
                      class="sort-select"
                      :aria-label="t.adminStudentActivities.sortAriaLabel"
                      data-testid="activity-sort-field"
                      @change="setSortField($event.target.value)"
                    >
                      <option value="latest">{{ t.adminStudentActivities.sortByLatest }}</option>
                      <option value="start">{{ t.adminStudentActivities.sortByStartDate }}</option>
                    </select>

                    <button
                      type="button"
                      class="sort-direction"
                      :title="sortDirection === 'asc' ? t.adminStudentActivities.sortDirectionAsc : t.adminStudentActivities.sortDirectionDesc"
                      :aria-label="sortDirection === 'asc' ? t.adminStudentActivities.sortDirectionAsc : t.adminStudentActivities.sortDirectionDesc"
                      data-testid="activity-sort-direction"
                      @click="toggleSortDirection"
                    >
                      <ArrowUp v-if="sortDirection === 'asc'" :size="14" />
                      <ArrowDown v-else :size="14" />
                    </button>
                  </div>
                </div>
              </th>
              <th>{{ t.adminStudentActivities.tableHeaderOrganizer }}</th>
              <th>{{ t.adminStudentActivities.tableHeaderStartDate }}</th>
              <th>{{ t.adminStudentActivities.tableHeaderEndDate }}</th>
              <th>{{ t.adminStudentActivities.tableHeaderParticipants }}</th>
              <th>{{ t.adminStudentActivities.tableHeaderDetails }}</th>
              <th>{{ t.adminStudentActivities.tableHeaderManageParticipants }}</th>
              <th>{{ t.adminStudentActivities.tableHeaderManageActivity }}</th>
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

                <td>
                  <div class="skeleton skeleton-button"></div>
                </td>
              </tr>
            </template>

            <template v-else>
            <template
              v-for="activity in paginatedActivities"
              :key="activity.id"
            >
            <tr>
              <td>
                <div class="activity-name">
                  <strong>{{ activity.name }}</strong>
                  <small>{{ activity.activity_hours ?? 0 }} {{ t.activityHours.unit }}</small>
                  <div class="activity-meta">
                    <span
                      class="activity-status"
                      :class="statusClass(activity.status)"
                    >
                      {{ statusLabel(activity.status) }}
                    </span>

                    <button
                      type="button"
                      class="skills-toggle"
                      :class="{ open: expandedSkillsId === activity.id }"
                      :aria-expanded="expandedSkillsId === activity.id"
                      @click="toggleSkillsRow(activity.id)"
                    >
                      {{ t.adminStudentActivities.skillsToggleLabel }}
                      <span>S {{ skillCount(activity, 'staff') }} · P {{ skillCount(activity, 'participant') }}</span>
                      <ChevronDown :size="11" />
                    </button>
                  </div>
                </div>
              </td>

              <td class="organizer">
                {{ activity.organizer }}
              </td>

              <td>
                <div class="date-cell">
                  <span>{{ formatDate(activity.start_at) }}</span>
                  <small>{{ formatTime(activity.start_at) }}</small>
                </div>
              </td>

              <td>
                <div class="date-cell">
                  <span>{{ formatDate(activity.end_at) }}</span>
                  <small>{{ formatTime(activity.end_at) }}</small>
                </div>
              </td>

              <td>
                <div class="participant-cell">
                  <strong>
                    {{ activity.participants }}
                    <span v-if="activity.capacity">/{{ activity.capacity }}</span>
                  </strong>

                  <div v-if="activity.capacity" class="progress-track">
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
                  {{ t.adminStudentActivities.viewDetailButton }}
                </button>
              </td>

              <td>
                <div class="manage-participants">
                  <button
                    class="manage-button"
                    @click="toggleManageMenu(activity.id)"
                  >
                    {{ t.adminStudentActivities.manageButton }}
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
                      {{ t.adminStudentActivities.addStudentAction }}
                    </button>

                    <button
                      class="manage-menu-item"
                      @click="openImportParticipants(activity)"
                    >
                      <Upload :size="15" />
                      {{ t.adminStudentActivities.importFromFileMenuItem }}
                    </button>
                  </div>
                </div>
              </td>

              <td>
                <div class="manage-participants">
                  <button
                    class="manage-button activity-manage-button"
                    :disabled="activityActionLoadingId === activity.id"
                    @click="toggleActivityMenu(activity.id)"
                  >
                    <Settings2 :size="14" />
                    {{ t.adminStudentActivities.manageButton }}
                    <ChevronDown :size="14" />
                  </button>

                  <div
                    v-if="openActivityMenuId === activity.id"
                    class="manage-menu activity-manage-menu"
                  >
                    <button
                      class="manage-menu-item"
                      @click="openEditActivity(activity)"
                    >
                      <Pencil :size="15" />
                      {{ t.adminStudentActivities.editActivityMenuItem }}
                    </button>

                    <button
                      v-if="(activity.status || 'active') !== 'completed'"
                      class="manage-menu-item"
                      @click="setActivityStatus(activity, 'completed')"
                    >
                      <CircleCheckBig :size="15" />
                      {{ t.adminStudentActivities.markAsCompletedMenuItem }}
                    </button>

                    <button
                      v-else
                      class="manage-menu-item"
                      @click="setActivityStatus(activity, 'active')"
                    >
                      <RotateCcw :size="15" />
                      {{ t.adminStudentActivities.reopenActivityMenuItem }}
                    </button>

                    <button
                      v-if="(activity.status || 'active') !== 'cancelled'"
                      class="manage-menu-item"
                      @click="setActivityStatus(activity, 'cancelled')"
                    >
                      <Ban :size="15" />
                      {{ t.adminStudentActivities.cancelActivityMenuItem }}
                    </button>

                    <button
                      class="manage-menu-item danger"
                      @click="deleteActivity(activity)"
                    >
                      <Trash2 :size="15" />
                      {{ t.adminStudentActivities.deleteActivityMenuItem }}
                    </button>
                  </div>
                </div>
              </td>
            </tr>

            <tr
              v-if="expandedSkillsId === activity.id"
              class="skills-detail-row"
            >
              <td colspan="8">
                <div class="skills-detail">
                  <section
                    v-for="role in ['staff', 'participant']"
                    :key="role"
                    class="skills-detail-group"
                    :data-role="role"
                  >
                    <h4>{{ role === 'staff' ? t.adminStudentActivities.staffSkillsHeading : t.adminStudentActivities.participantSkillsHeading }}</h4>

                    <ul v-if="activitySkillList(activity, role).length">
                      <li
                        v-for="skill in activitySkillList(activity, role)"
                        :key="skill.key"
                        :data-skill="skill.key"
                      >
                        <span>{{ skill.label }}</span>
                        <strong>{{ t.adminStudentActivities.skillLevelLabel }} {{ skill.level }}</strong>
                      </li>
                    </ul>

                    <p v-else class="skills-empty">{{ t.adminStudentActivities.noRelatedSkillsText }}</p>
                  </section>
                </div>
              </td>
            </tr>
            </template>

            <tr v-if="!paginatedActivities.length">
              <td colspan="8">
                <div class="empty-table">
                  {{ t.adminStudentActivities.emptyActivitiesTableText }}
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
          {{ t.adminStudentActivities.paginationShowing }}
          {{ filteredActivities.length ? (currentPage - 1) * rowsPerPage + 1 : 0 }}
          -
          {{
            Math.min(currentPage * rowsPerPage, filteredActivities.length)
          }}
          {{ t.adminStudentActivities.paginationOf }} {{ filteredActivities.length }}
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
            <p class="modal-eyebrow">{{ t.adminStudentActivities.addStudentModalEyebrow }}</p>
            <h2>{{ t.adminStudentActivities.addStudentModalTitle }}</h2>
            <p v-if="selectedActivity" class="selected-activity">
              {{ selectedActivity.name }}
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
          <label class="student-search-field">
            <span>{{ t.adminStudentActivities.studentIdLabel }}</span>

            <div class="student-search-wrapper">
              <input
                v-model="studentQuery"
                type="text"
                autocomplete="off"
                :placeholder="t.adminStudentActivities.studentSearchPlaceholder"
                @input="onStudentQueryInput"
                @focus="showStudentSuggestions = studentSuggestions.length > 0"
                @blur="confirmStudentLookup"
              />

              <ul
                v-if="showStudentSuggestions"
                class="student-suggestions"
              >
                <li
                  v-for="student in studentSuggestions"
                  :key="student.student_id"
                  @mousedown.prevent="selectStudentSuggestion(student)"
                >
                  <strong>{{ student.student_id }}</strong>
                  <span>{{ student.first_name }} {{ student.last_name }}</span>
                  <small>{{ student.major || t.adminStudentActivities.noMajorLabel }}</small>
                </li>
              </ul>
            </div>

            <p v-if="studentLookupStatus === 'loading'" class="student-lookup-status">
              {{ t.adminStudentActivities.studentLookupLoading }}
            </p>
            <p v-else-if="studentLookupStatus === 'not_found'" class="student-lookup-status error">
              {{ t.adminStudentActivities.studentIdNotFoundError }}
            </p>
          </label>

          <div v-if="studentLookupStatus === 'found'" class="student-found-card">
            <div class="student-found-row">
              <span class="student-found-label">{{ t.adminStudentActivities.firstNameLabel }} / {{ t.adminStudentActivities.lastNameLabel }}</span>
              <strong>{{ manualStudent.first_name }} {{ manualStudent.last_name }}</strong>
            </div>
            <div class="student-found-row">
              <span class="student-found-label">{{ t.adminStudentActivities.emailLabel }}</span>
              <strong>{{ manualStudent.email }}</strong>
            </div>
            <div class="student-found-row">
              <span class="student-found-label">{{ t.adminStudentActivities.facultyLabel }}</span>
              <strong>{{ manualStudent.faculty || '-' }}</strong>
            </div>
            <div class="student-found-row">
              <span class="student-found-label">{{ t.adminStudentActivities.majorLabel }}</span>
              <strong>{{ manualStudent.major || t.adminStudentActivities.noMajorLabel }}</strong>
            </div>
          </div>

          <label>
            <span>{{ t.adminStudentActivities.roleFieldLabel }}</span>

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
            {{ t.adminStudentActivities.cancelButton }}
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
                ? t.adminStudentActivities.addingStudentLoading
                : t.adminStudentActivities.addStudentAction
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
      <div
          class="import-modal import-participants-modal"
          :class="{ 'review-mode': importPreview }"
        >
        <div class="modal-header">
          <div>
            <p class="modal-eyebrow">
              {{ importPreview ? t.adminStudentActivities.importPreviewEyebrow : t.adminStudentActivities.importFromFileEyebrow }}
            </p>
            <h2>
              {{ importPreview ? t.adminStudentActivities.reviewParticipantsTitle : t.adminStudentActivities.importStudentListTitle }}
            </h2>
            <p v-if="selectedActivity" class="selected-activity">
              {{ selectedActivity.name }}
            </p>
          </div>

          <div class="modal-header-actions">
            <button
              v-if="!importPreview"
              type="button"
              class="template-download-button"
              :disabled="templateDownloading"
              data-testid="download-import-template"
              @click="downloadImportTemplate"
            >
              <LoaderCircle v-if="templateDownloading" class="spin" :size="16" />
              <Download v-else :size="16" />
              {{ t.adminStudentActivities.downloadTemplateButton }}
            </button>

            <button
              class="modal-close"
              @click="closeImportModal"
            >
              <X :size="20" />
            </button>
          </div>
        </div>

        <!-- STEP 1: FILES -->
        <template v-if="!importPreview">
          <div
            class="file-dropzone"
            :class="{ dragging: isDraggingFile, 'has-files': selectedFiles.length }"
            @dragenter.prevent="isDraggingFile = true"
            @dragover.prevent="isDraggingFile = true"
            @dragleave.prevent="isDraggingFile = false"
            @drop.prevent="handleImportDrop"
          >
            <button
              type="button"
              class="dropzone-heading dropzone-select-button"
              :disabled="importLoading || confirmLoading"
              @click="openImportFilePicker"
            >
              <FileSpreadsheet :size="34" />

              <div>
                <strong>{{ t.adminStudentActivities.dropzoneHeading }}</strong>
                <span>{{ t.adminStudentActivities.dropzoneSubtext }}</span>
              </div>
            </button>

            <div
              v-if="selectedFiles.length"
              class="selected-file-list"
            >
              <div
                v-for="(file, index) in selectedFiles"
                :key="`${file.name}-${file.size}-${file.lastModified}`"
                class="selected-file-item"
              >
                <div class="selected-file-info">
                  <div class="selected-file-icon">
                    <FileSpreadsheet :size="18" />
                  </div>

                  <div class="selected-file-text">
                    <strong>{{ file.name }}</strong>
                    <span>{{ Math.max(1, Math.ceil(file.size / 1024)) }} KB</span>
                  </div>
                </div>

                <button
                  type="button"
                  class="remove-file-button"
                  :title="t.adminStudentActivities.removeFileTooltip"
                  @click="removeImportFile(index)"
                >
                  <X :size="16" />
                </button>
              </div>
            </div>

            <input
              ref="importFileInput"
              type="file"
              accept=".csv,.xlsx,.xls"
              multiple
              hidden
              @change="handleImportFile"
            />
          </div>
        </template>

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

        <!-- STEP 2: PREVIEW ONLY -->
        <div
          v-if="importPreview"
          class="preview-panel import-review-panel"
        >
          <div class="preview-summary">
            <div class="preview-summary-item">
              <span>{{ t.adminStudentActivities.previewFoundLabel }}</span>
              <strong>{{ importPreview.students.length }}</strong>
            </div>

            <div class="preview-summary-item">
              <span>{{ t.adminStudentActivities.previewReadyLabel }}</span>
              <strong>
                {{
                  importPreview.students.length -
                  importIssueCount
                }}
              </strong>
            </div>

            <button
              type="button"
              class="preview-summary-item issue-summary-button"
              :class="{ active: showImportIssues }"
              :disabled="!importIssueCount"
              @click="toggleImportIssues"
            >
              <span>{{ t.adminStudentActivities.previewIssuesLabel }}</span>
              <strong>{{ importIssueCount }}</strong>
              <small v-if="importIssueCount">
                {{ showImportIssues ? t.adminStudentActivities.hideDetailsText : t.adminStudentActivities.showDetailsText }}
              </small>
            </button>
          </div>

          <div
            v-if="showImportIssues && importIssueCount"
            class="import-issues-panel"
          >
            <div class="issues-panel-heading">
              <TriangleAlert :size="17" />
              <div>
                <strong>{{ t.adminStudentActivities.importIssuesHeading }}</strong>
                <span>{{ t.adminStudentActivities.importIssuesSubtext }}</span>
              </div>
            </div>

            <div class="issue-list">
              <div
                v-for="issue in importIssueList"
                :key="issue.student._rowKey"
                class="issue-item"
              >
                <div class="issue-item-top">
                  <strong>
                    {{
                      issue.student.student_id ||
                      t.adminStudentActivities.unknownStudentFallback
                    }}
                  </strong>
                  <span>{{ issue.student._sourceFile }} • {{ t.adminStudentActivities.previewIssueRowLabel }} {{ issue.student._sourceRow }}</span>
                </div>

                <ul>
                  <li
                    v-for="(error, errorIndex) in issue.errors"
                    :key="`${issue.student._rowKey}-${errorIndex}`"
                  >
                    {{ error }}
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <p class="preview-edit-hint">
            <Pencil :size="13" />
            {{ t.adminStudentActivities.previewEditHint }}
          </p>

          <div class="preview-table-wrapper preview-participants-scroll">
            <table class="preview-table participants-preview-table">
              <thead>
                <tr>
                  <th
                    v-for="column in importEditableColumns"
                    :key="column.field"
                    :style="{ width: column.width }"
                  >
                    {{ column.label }}
                  </th>
                  <th>{{ t.adminStudentActivities.previewTableRole }}</th>
                  <th>{{ t.adminStudentActivities.previewTableStatus }}</th>
                </tr>
              </thead>

              <tbody>
                <!-- key ต้องคงที่ (ไม่ใช้ student_id) ไม่งั้นแก้รหัสแล้ว input จะหลุด focus -->
                <tr
                  v-for="(student, index) in importPreview.students"
                  :key="student._rowKey"
                  :class="{ 'preview-row-issue': importRowHasIssue(index) }"
                >
                  <td
                    v-for="column in importEditableColumns"
                    :key="column.field"
                  >
                    <input
                      v-model="student[column.field]"
                      type="text"
                      class="preview-cell-input"
                      :class="{ invalid: importRowErrors[index]?.[column.field] }"
                      :aria-label="column.label"
                      :inputmode="column.field === 'email' ? 'email' : undefined"
                      :disabled="confirmLoading"
                      spellcheck="false"
                    />

                    <small
                      v-if="importRowErrors[index]?.[column.field]"
                      class="preview-cell-error"
                    >
                      {{ importRowErrors[index][column.field] }}
                    </small>
                  </td>

                  <td>
                    <select
                      v-model="student.role"
                      class="preview-role-select"
                      :class="{ invalid: importRowErrors[index]?.role }"
                      :disabled="confirmLoading"
                    >
                      <option value="participant">{{ t.adminStudentActivities.participantLabel }}</option>
                      <option value="organizer">{{ t.adminStudentActivities.organizerLabel }}</option>
                    </select>

                    <small
                      v-if="importRowErrors[index]?.role"
                      class="preview-cell-error"
                    >
                      {{ importRowErrors[index].role }}
                    </small>
                  </td>

                  <td>
                    <button
                      v-if="importRowHasIssue(index)"
                      type="button"
                      class="preview-status issue"
                      @click="
                        showImportIssues = true
                      "
                    >
                      {{ t.adminStudentActivities.issueStatusLabel }}
                    </button>

                    <span
                      v-else
                      class="preview-status ready"
                    >
                      {{ t.adminStudentActivities.readyStatusLabel }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p
            v-if="importIssueCount"
            class="preview-note preview-issue-note"
          >
            {{ previewIssueNoteText }}
          </p>
        </div>

        <div class="modal-actions">
          <button
            class="modal-secondary-button"
            :disabled="importLoading || confirmLoading"
            @click="closeImportModal"
          >
            {{ t.adminStudentActivities.cancelButton }}
          </button>

          <button
            v-if="importPreview"
            class="modal-secondary-button"
            :disabled="importLoading || confirmLoading"
            @click="backToImportFiles"
          >
            <ChevronLeft :size="17" />
            {{ t.adminStudentActivities.backButton }}
          </button>

          <button
            v-else
            class="modal-preview-button"
            :disabled="
              importLoading ||
              confirmLoading ||
              !selectedFiles.length
            "
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
                ? t.adminStudentActivities.readingLoadingText
                : t.adminStudentActivities.previewImportButton
            }}
          </button>

          <button
            v-if="importPreview"
            class="modal-confirm-button"
            :disabled="
              confirmLoading ||
              validPreviewStudents().length === 0
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
                ? t.adminStudentActivities.importingLoadingText
                : confirmImportButtonText
            }}
          </button>
        </div>
      </div>
    </div>

    <!-- EDIT ACTIVITY MODAL -->
    <div
      v-if="showEditActivityModal"
      class="modal-backdrop"
      @click.self="closeEditActivityModal"
    >
      <div class="import-modal edit-activity-modal">
        <div class="modal-header">
          <div>
            <p class="modal-eyebrow">{{ t.adminStudentActivities.manageActivityEyebrow }}</p>
            <h2>{{ t.adminStudentActivities.editActivityTitle }}</h2>
            <p v-if="selectedActivity" class="selected-activity">
              {{ selectedActivity.name }}
            </p>
          </div>

          <button
            class="modal-close"
            :disabled="editActivityLoading"
            @click="closeEditActivityModal"
          >
            <X :size="20" />
          </button>
        </div>

        <div class="activity-edit-grid">
          <label class="edit-field"><span>{{ t.activityHours.label }}</span><input v-model="editActivityForm.activity_hours" name="activity_hours" type="number" min="0" max="99999999.99" step="0.01" required /></label>
          <label class="edit-field full">
            <span>{{ t.adminStudentActivities.activityNameLabel }}</span>
            <input
              v-model="editActivityForm.name"
              type="text"
              :placeholder="t.adminStudentActivities.activityNamePlaceholder"
            />
          </label>

          <label class="edit-field">
            <span>{{ t.adminStudentActivities.activityTypeLabel }}</span>
            <input
              v-model="editActivityForm.activity_type"
              type="text"
              :placeholder="t.adminStudentActivities.activityTypePlaceholder"
            />
          </label>

          <label class="edit-field">
            <span>{{ t.adminStudentActivities.statusFieldLabel }}</span>
            <select v-model="editActivityForm.status">
              <option value="active">{{ t.adminStudentActivities.statusActive }}</option>
              <option value="completed">{{ t.adminStudentActivities.statusCompleted }}</option>
              <option value="cancelled">{{ t.adminStudentActivities.statusCancelled }}</option>
            </select>
          </label>

          <label class="edit-field">
            <span>{{ t.adminStudentActivities.startDateTimeLabel }}</span>
            <input
              v-model="editActivityForm.start_at"
              type="datetime-local"
            />
          </label>

          <label class="edit-field">
            <span>{{ t.adminStudentActivities.endDateTimeLabel }}</span>
            <input
              v-model="editActivityForm.end_at"
              type="datetime-local"
            />
          </label>

          <label class="edit-field">
            <span>{{ t.adminStudentActivities.departmentLabel }}</span>
            <input
              v-model="editActivityForm.department"
              type="text"
            />
          </label>

          <label class="edit-field">
            <span>{{ t.adminStudentActivities.responsiblePersonLabel }}</span>
            <input
              v-model="editActivityForm.responsible_person"
              type="text"
            />
          </label>

          <label class="edit-field">
            <span>{{ t.adminStudentActivities.advisorLabel }}</span>
            <input
              v-model="editActivityForm.advisor"
              type="text"
            />
          </label>

          <label class="edit-field">
            <span>{{ t.adminStudentActivities.locationLabel }}</span>
            <input
              v-model="editActivityForm.location"
              type="text"
            />
          </label>

          <label class="edit-field full">
            <span>{{ t.adminStudentActivities.descriptionLabel }}</span>
            <textarea
              v-model="editActivityForm.description"
              rows="4"
            ></textarea>
          </label>

          <div class="edit-field full edit-skills">
            <div class="edit-skills-heading">
              <span>{{ t.adminStudentActivities.skillsLabel }}</span>

              <div class="edit-skill-tabs">
                <button
                  type="button"
                  :class="{ active: editSkillTarget === 'staff' }"
                  @click="editSkillTarget = 'staff'"
                >
                  {{ t.adminStudentActivities.staffLabel }}
                </button>
                <button
                  type="button"
                  :class="{ active: editSkillTarget === 'participant' }"
                  @click="editSkillTarget = 'participant'"
                >
                  {{ t.adminStudentActivities.participantLabel }}
                </button>
              </div>
            </div>

            <SkillLevelEditor
              v-if="editSkillTarget === 'staff'"
              v-model="editActivityForm.staff_skills"
              :definitions="STAFF_SKILLS"
              compact
            />
            <SkillLevelEditor
              v-else
              v-model="editActivityForm.participant_skills"
              :definitions="PARTICIPANT_SKILLS"
              compact
            />
          </div>
        </div>

        <div
          v-if="editActivityError"
          class="import-message error"
        >
          <TriangleAlert :size="17" />
          {{ editActivityError }}
        </div>

        <div class="modal-actions">
          <button
            class="modal-secondary-button"
            :disabled="editActivityLoading"
            @click="closeEditActivityModal"
          >
            {{ t.adminStudentActivities.cancelButton }}
          </button>

          <button
            class="modal-confirm-button"
            :disabled="editActivityLoading"
            @click="saveActivityEdits"
          >
            <LoaderCircle
              v-if="editActivityLoading"
              class="spin"
              :size="17"
            />
            <Pencil v-else :size="17" />

            {{
              editActivityLoading
                ? t.adminStudentActivities.savingLoadingText
                : t.adminStudentActivities.saveChangesButton
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
  font-size: var(--fs-small);
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
  font-size: var(--fs-small);
  font-weight: 700;
  letter-spacing: 0.06em;
}

.filter-date-field {
  position: relative;
  z-index: 40;
}

.filter-date-picker {
  position: relative;
}

.filter-date-trigger {
  width: 100%;
  height: 42px;
  padding: 0 12px;
  border: 1px solid #dfe7f2;
  border-radius: 9px;
  background: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #3c4b60;
  font-family: inherit;
  font-size: var(--fs-body);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.18s, box-shadow 0.18s;
}

.filter-date-trigger:hover,
.filter-date-trigger.selected {
  border-color: #b9c9dd;
}

.filter-date-trigger:focus-visible {
  outline: none;
  border-color: #8f7cf1;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.filter-date-trigger svg {
  flex: 0 0 auto;
  color: #91a2b9;
}

.filter-date-trigger span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.filter-date-trigger .placeholder {
  color: #98a5b6;
}

.filter-calendar-popover {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  z-index: 120;
  width: 320px;
  padding: 13px;
  border: 1px solid #e0e6ef;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 18px 48px rgba(30, 42, 62, 0.16);
}

.filter-calendar-header {
  margin-bottom: 10px;
  display: grid;
  grid-template-columns: 34px 1fr 34px;
  align-items: center;
  gap: 8px;
}

.filter-calendar-header strong {
  color: #29394f;
  font-size: var(--fs-body);
  text-align: center;
}

.filter-calendar-header button {
  width: 34px;
  height: 34px;
  border: 0;
  border-radius: 9px;
  background: #f5f7fa;
  display: grid;
  place-items: center;
  color: #5b6b80;
  cursor: pointer;
}

.filter-calendar-header button:hover {
  background: #f0ebfb;
  color: #7137b8;
}

.filter-calendar-weekdays,
.filter-calendar-days {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 4px;
}

.filter-calendar-weekdays {
  margin-bottom: 5px;
}

.filter-calendar-weekdays span {
  min-height: 23px;
  display: grid;
  place-items: center;
  color: #98a5b6;
  font-size: var(--fs-badge);
  font-weight: 800;
}

.filter-calendar-days button {
  aspect-ratio: 1;
  min-width: 0;
  border: 0;
  border-radius: 9px;
  background: transparent;
  display: grid;
  place-items: center;
  color: #415168;
  font-family: inherit;
  font-size: var(--fs-small);
  font-weight: 700;
  cursor: pointer;
}

.filter-calendar-days button:hover:not(.selected) {
  background: #f3effb;
  color: #6b2fa8;
}

.filter-calendar-days button.outside {
  color: #c5ccd6;
}

.filter-calendar-days button.today:not(.selected) {
  box-shadow: inset 0 0 0 1px #b9a3e6;
  color: #6b2fa8;
}

.filter-calendar-days button.selected {
  background: linear-gradient(135deg, #2563eb, #8613bd);
  color: #fff;
  box-shadow: 0 4px 10px rgba(109, 40, 217, 0.2);
}

.filter-calendar-footer {
  margin-top: 9px;
  padding-top: 9px;
  border-top: 1px solid #eef1f5;
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.filter-calendar-footer button {
  padding: 6px 10px;
  border: 0;
  border-radius: 8px;
  background: #f1ebff;
  color: #6d35aa;
  font-family: inherit;
  font-size: var(--fs-small);
  font-weight: 800;
  cursor: pointer;
}

.filter-calendar-footer button.clear {
  background: #f5f7fa;
  color: #66758a;
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
  font-size: var(--fs-body);
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
  white-space: nowrap;
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
  font-size: var(--fs-small);
}

.activities-table-card {
  overflow: visible;
  border: 1px solid #e5ebf3;
  border-radius: 14px;
  background: #fff;
}

.table-scroll {
  overflow-x: auto;
  transition: padding-bottom 0.18s ease;
  scrollbar-width: thin;
  scrollbar-color: #cfd8e5 #ffffff;
}

.table-scroll::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.table-scroll::-webkit-scrollbar-track {
  background: #ffffff;
  border-radius: 999px;
}

.table-scroll::-webkit-scrollbar-thumb {
  border: 2px solid #ffffff;
  border-radius: 999px;
  background: #cfd8e5;
}

.table-scroll::-webkit-scrollbar-thumb:hover {
  background: #b9c5d4;
}

.table-scroll.menu-open {
  padding-bottom: 118px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

/*
  ตารางกิจกรรมมี 8 คอลัมน์: ลด min-width + padding แนวนอน
  ให้พอดีจอ 1280px ขึ้นไปโดยไม่ต้องเลื่อนหาคอลัมน์ MANAGE ACTIVITY
  จอเล็กกว่านั้นยังเลื่อนแนวนอนใน .table-scroll ได้เหมือนเดิม
*/
.activities-table-card table {
  min-width: 980px;
}

.activities-table-card th,
.activities-table-card td {
  padding-left: 14px;
  padding-right: 14px;
}

thead {
  background: #f8fafc;
}

th {
  padding: 17px 20px;
  color: #8ea0b8;
  font-size: var(--fs-small);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-align: left;
}

td {
  height: 92px;
  padding: 15px 20px;
  border-top: 1px solid #edf1f6;
  color: #415269;
  font-size: var(--fs-body);
  vertical-align: middle;
}

.activity-name {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.activity-name strong {
  color: #1d2a3f;
  font-size: var(--fs-body);
  line-height: 1.6;
}

.activity-name small {
  color: #93a5bc;
  font-size: var(--fs-badge);
}

.activity-meta {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-wrap: wrap;
}

.date-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.date-cell small {
  color: #93a5bc;
  font-size: var(--fs-small);
}

.skills-toggle {
  padding: 3px 7px;
  border: 1px solid #dde5f0;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #fff;
  color: #4b5d76;
  font: inherit;
  font-size: var(--fs-badge);
  font-weight: 800;
  cursor: pointer;
}

.skills-toggle span {
  color: #8b9ab0;
  font-weight: 700;
}

.skills-toggle svg {
  transition: transform 0.15s ease;
}

.skills-toggle.open {
  border-color: #b9cdf3;
  background: #eef4ff;
  color: #1f5fcf;
}

.skills-toggle.open svg {
  transform: rotate(180deg);
}

.skills-detail-row td {
  height: auto;
  padding: 0 14px 16px;
  border-top: 0;
  background: #fbfcfe;
}

.skills-detail {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.skills-detail-group {
  padding: 12px 14px;
  border: 1px solid #e7ecf3;
  border-radius: 10px;
  background: #fff;
}

.skills-detail-group h4 {
  margin: 0 0 8px;
  color: #8ea0b8;
  font-size: var(--fs-caption);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.skills-detail-group ul {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 5px;
}

.skills-detail-group li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: var(--fs-small);
}

.skills-detail-group li strong {
  color: #17864d;
  font-size: var(--fs-small);
  white-space: nowrap;
}

.skills-empty {
  margin: 0;
  color: #93a5bc;
  font-size: var(--fs-small);
}

.edit-skills-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.edit-skills-heading > span {
  color: #66758c;
  font-size: var(--fs-small);
  font-weight: 700;
}

.edit-skill-tabs {
  padding: 3px;
  border-radius: 9px;
  display: inline-flex;
  background: #f1f4f9;
}

.edit-skill-tabs button {
  padding: 6px 12px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: #66758c;
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 700;
  cursor: pointer;
}

.edit-skill-tabs button.active {
  background: #fff;
  color: #1f5fcf;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

.activity-status {
  padding: 3px 7px;
  border-radius: 999px;
  font-size: var(--fs-badge);
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.activity-status.status-active {
  background: #eaf3ff;
  color: #1667d9;
}

.activity-status.status-completed {
  background: #e9f8ef;
  color: #238454;
}

.activity-status.status-cancelled {
  background: #fff0f0;
  color: #bd3b3b;
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
  font-size: var(--fs-small);
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
  font-size: var(--fs-small);
  white-space: nowrap;
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
  font-size: var(--fs-small);
  font-weight: 700;
}

.manage-button:hover {
  background: #dfebff;
}

.manage-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.activity-manage-button {
  background: #f3efff;
  color: #7335ba;
}

.activity-manage-button:hover {
  background: #ebe2ff;
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
  font-size: var(--fs-small);
  text-align: left;
}

.manage-menu-item:hover {
  background: #f3f7fc;
  color: #1769dc;
}

.activity-manage-menu {
  width: 195px;
}

.manage-menu-item.danger {
  color: #b94242;
}

.manage-menu-item.danger:hover {
  background: #fff0f0;
  color: #a92f2f;
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
  font-size: var(--fs-small);
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

.import-modal.review-mode {
  width: min(1180px, calc(100vw - 48px));
  max-height: 92vh;
  padding: 26px;
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
  font-size: var(--fs-caption);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.modal-header h2 {
  margin: 0;
  color: #1b283d;
  font-size: 23px;
}

.selected-activity {
  margin: 7px 0 0;
  color: #53647c;
  font-size: var(--fs-body);
  font-weight: 600;
}

.selected-activity span {
  color: #96a5b9;
  font-weight: 500;
}

.modal-header-actions {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  flex-shrink: 0;
}

/* outline: แยกจากปุ่มหลัก (นำเข้า / ยืนยัน) ที่เป็นปุ่มทึบ */
.template-download-button {
  min-height: 36px;
  padding: 0 14px;
  border: 1.5px solid #c9d6ee;
  border-radius: 9px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: #fff;
  color: #2f5fdb;
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
}

.template-download-button:not(:disabled):hover {
  border-color: #2f5fdb;
  background: #f3f7ff;
}

.template-download-button:disabled {
  opacity: 0.6;
  cursor: progress;
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
  font-size: var(--fs-body);
}

.file-dropzone span {
  color: #92a2b8;
  font-size: var(--fs-small);
}

.file-dropzone.dragging {
  border-color: #7d8df5;
  background: #f4f6ff;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.08);
}

.file-dropzone.has-files {
  align-items: stretch;
  justify-content: flex-start;
  cursor: pointer;
}

.dropzone-heading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.dropzone-select-button {
  width: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.dropzone-select-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.dropzone-heading > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.selected-file-list {
  width: 100%;
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selected-file-item {
  width: 100%;
  min-height: 58px;
  padding: 9px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 11px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  box-sizing: border-box;
}

.selected-file-info {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.selected-file-icon {
  width: 36px;
  height: 36px;
  flex: 0 0 auto;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: #edf4ff;
  color: #1769dc;
}

.selected-file-text {
  min-width: 0;
  text-align: left;
}

.selected-file-text strong {
  display: block;
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #34445c;
  font-size: var(--fs-body);
}

.selected-file-text span {
  display: block;
  margin-top: 2px;
  color: #92a2b8;
  font-size: var(--fs-small);
}

.remove-file-button {
  width: 32px;
  height: 32px;
  flex: 0 0 auto;
  border: 0;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: #f5f7fa;
  color: #7a8798;
  cursor: pointer;
}

.remove-file-button:hover {
  background: #fff0f0;
  color: #dc4c4c;
}

.import-message {
  margin-top: 14px;
  padding: 11px 13px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--fs-small);
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
  font-size: var(--fs-badge);
  font-weight: 700;
  letter-spacing: 0.07em;
}

.preview-summary strong {
  display: block;
  margin-top: 3px;
  color: #24344a;
  font-size: 20px;
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
  font-size: var(--fs-small);
}

.preview-note {
  margin: 0;
  padding: 9px 13px 12px;
  color: #8b9bb0;
  font-size: var(--fs-caption);
}

/* Import review */
.import-participants-modal {
  scrollbar-width: thin;
  scrollbar-color: #d7dee8 #ffffff;
}

.import-participants-modal::-webkit-scrollbar {
  width: 10px;
}

.import-participants-modal::-webkit-scrollbar-track {
  background: #ffffff;
  border-radius: 999px;
}

.import-participants-modal::-webkit-scrollbar-thumb {
  border: 2px solid #ffffff;
  border-radius: 999px;
  background: #d7dee8;
}

.import-participants-modal::-webkit-scrollbar-thumb:hover {
  background: #c5cfdb;
}

.import-review-panel {
  margin-top: 0;
}

.preview-summary > .preview-summary-item {
  min-width: 0;
  padding: 13px 15px;
  text-align: left;
}

.issue-summary-button {
  border: 0;
  border-left: 1px solid #e8edf4;
  background: transparent;
  font: inherit;
  cursor: pointer;
  transition: 0.18s ease;
}

.issue-summary-button:not(:disabled):hover,
.issue-summary-button.active {
  background: #fff8f8;
}

.issue-summary-button:disabled {
  cursor: default;
}

.issue-summary-button small {
  display: block;
  margin-top: 2px;
  color: #bd6262;
  font-size: var(--fs-badge);
  font-weight: 600;
}

.import-issues-panel {
  padding: 14px;
  border-bottom: 1px solid #e8edf4;
  background: #fffafb;
}

.issues-panel-heading {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  color: #b94d4d;
}

.issues-panel-heading > div {
  min-width: 0;
}

.issues-panel-heading strong {
  display: block;
  color: #8f3434;
  font-size: var(--fs-small);
}

.issues-panel-heading span {
  display: block;
  margin-top: 2px;
  color: #b16a6a;
  font-size: var(--fs-caption);
}

.issue-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.issue-item {
  padding: 9px 10px;
  border: 1px solid #f0d5d5;
  border-radius: 9px;
  background: #fff;
}

.issue-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.issue-item-top strong {
  color: #3f4c60;
  font-size: var(--fs-small);
}

.issue-item-top span {
  color: #9c7880;
  font-size: var(--fs-badge);
}

.issue-item ul {
  margin: 6px 0 0 16px;
  padding: 0;
  color: #b24f4f;
  font-size: var(--fs-caption);
  line-height: 1.6;
}

.preview-participants-scroll {
  max-height: 500px;
  overflow: auto;
  scrollbar-width: thin;
  scrollbar-color: #d7dee8 #ffffff;
}

.preview-participants-scroll::-webkit-scrollbar {
  width: 9px;
  height: 9px;
}

.preview-participants-scroll::-webkit-scrollbar-track {
  background: #ffffff;
}

.preview-participants-scroll::-webkit-scrollbar-thumb {
  border: 2px solid #ffffff;
  border-radius: 999px;
  background: #d7dee8;
}

.participants-preview-table {
  min-width: 1080px;
}

.participants-preview-table td {
  vertical-align: top;
}

.preview-edit-hint {
  margin: 0;
  padding: 10px 13px;
  display: flex;
  align-items: center;
  gap: 6px;
  border-bottom: 1px solid #edf1f5;
  color: #6f7f96;
  font-size: var(--fs-caption);
}

.preview-cell-input {
  width: 100%;
  height: 32px;
  padding: 0 9px;
  border: 1px solid #dce5ef;
  border-radius: 8px;
  outline: none;
  background: #fff;
  color: #40516a;
  font: inherit;
  font-size: var(--fs-small);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.preview-cell-input:focus {
  border-color: #8b7ee8;
  box-shadow: 0 0 0 3px rgba(139, 126, 232, 0.08);
}

.preview-cell-input:disabled {
  background: #f8fafc;
  cursor: not-allowed;
}

.preview-cell-input.invalid,
.preview-role-select.invalid {
  border-color: #eeb4b4;
}

.preview-cell-input.invalid:focus,
.preview-role-select.invalid:focus {
  border-color: #d86a6a;
  box-shadow: 0 0 0 3px rgba(216, 106, 106, 0.1);
}

.preview-cell-error {
  display: block;
  margin-top: 4px;
  padding-left: 2px;
  color: #bd4b4b;
  font-size: var(--fs-badge);
  font-weight: 600;
  line-height: 1.6;
}

.participants-preview-table thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  background: #f8fafc;
}

.preview-row-issue {
  background: #fffafa;
}

.preview-role-select {
  min-width: 118px;
  height: 32px;
  padding: 0 28px 0 9px;
  border: 1px solid #dce5ef;
  border-radius: 8px;
  outline: none;
  background: #fff;
  color: #40516a;
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 700;
  cursor: pointer;
}

.preview-role-select:focus {
  border-color: #8b7ee8;
  box-shadow: 0 0 0 3px rgba(139, 126, 232, 0.08);
}

.preview-status {
  min-width: 54px;
  min-height: 25px;
  padding: 0 8px;
  border: 0;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--fs-badge);
  font-weight: 800;
}

.preview-status.ready {
  background: #eaf8f0;
  color: #218154;
}

.preview-status.issue {
  background: #fff0f0;
  color: #bd4b4b;
  cursor: pointer;
}

.preview-issue-note {
  border-top: 1px solid #edf1f5;
  background: #fffdfd;
  color: #9c6570;
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
  font-size: var(--fs-small);
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
  font-size: var(--fs-body);
}

.manual-form input:focus {
  border-color: #7bb1f5;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}


.student-search-wrapper {
  position: relative;
}

.student-suggestions {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  z-index: 20;

  max-height: 220px;
  overflow-y: auto;

  margin: 0;
  padding: 6px;
  list-style: none;

  background: #fff;
  border: 1px solid #dce5ef;
  border-radius: 9px;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12);
}

.student-suggestions li {
  display: flex;
  flex-direction: column;
  gap: 1px;

  padding: 8px 10px;
  border-radius: 7px;

  cursor: pointer;
}

.student-suggestions li:hover {
  background: #f1f6fd;
}

.student-suggestions li strong {
  color: #1f2937;
  font-size: var(--fs-body);
}

.student-suggestions li span {
  color: #4b5563;
  font-size: var(--fs-small);
}

.student-suggestions li small {
  color: #8c929c;
  font-size: var(--fs-small);
}

.student-lookup-status {
  margin: 4px 0 0;
  font-size: var(--fs-small);
  color: #66758c;
}

.student-lookup-status.error {
  color: #b42318;
}

.student-found-card {
  display: flex;
  flex-direction: column;
  gap: 8px;

  padding: 12px 14px;

  background: #f6fbf7;
  border: 1px solid #bfe3c6;
  border-radius: 9px;
}

.student-found-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;

  font-size: var(--fs-body);
}

.student-found-label {
  color: #66758c;
  font-size: var(--fs-small);
  font-weight: 700;
  white-space: nowrap;
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
  font-size: var(--fs-body);
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
  font-size: var(--fs-small);
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


  .filter-calendar-popover {
    width: min(320px, calc(100vw - 48px));
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


/* ============================= */
/* EDIT ACTIVITY MODAL */
/* ============================= */

.edit-activity-modal {
  width: min(760px, 100%);
}

.activity-edit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.edit-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.edit-field.full {
  grid-column: 1 / -1;
}

.edit-field > span {
  color: #66758c;
  font-size: var(--fs-small);
  font-weight: 700;
}

.edit-field input,
.edit-field select,
.edit-field textarea {
  width: 100%;
  border: 1px solid #dce5ef;
  border-radius: 9px;
  outline: none;
  background: #fff;
  color: #34445a;
  font: inherit;
  font-size: var(--fs-body);
}

.edit-field input,
.edit-field select {
  height: 42px;
  padding: 0 12px;
}

.edit-field textarea {
  min-height: 105px;
  padding: 11px 12px;
  resize: vertical;
}

.edit-field input:focus,
.edit-field select:focus,
.edit-field textarea:focus {
  border-color: #7bb1f5;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

@media (max-width: 700px) {
  .activity-edit-grid {
    grid-template-columns: 1fr;
  }

  .edit-field.full {
    grid-column: auto;
  }
}


@media (max-width: 760px) {
  .import-modal.review-mode {
    width: 100%;
    padding: 18px;
  }

  .preview-participants-scroll {
    max-height: 420px;
  }
}


/* =========================
   Sort (หัวคอลัมน์ชื่อกิจกรรม)
========================= */
.name-header-inner {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 10px;
}

.sort-control {
  display: inline-flex;
  align-items: stretch;
  border: 1px solid #dce5ef;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}

.sort-select {
  height: 30px;
  padding: 0 26px 0 10px;
  border: 0;
  outline: none;
  background: #fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' fill='none' stroke='%237b8ba3' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M1 1l4 4 4-4'/%3E%3C/svg%3E") no-repeat right 9px center;
  color: #34445a;
  font: inherit;
  font-size: var(--fs-caption);
  font-weight: 600;
  letter-spacing: 0;
  text-transform: none;
  appearance: none;
  cursor: pointer;
}

.sort-direction {
  width: 30px;
  border: 0;
  border-left: 1px solid #dce5ef;
  display: grid;
  place-items: center;
  background: #f5f8fc;
  color: #2f5fdb;
  cursor: pointer;
}

.sort-select:hover,
.sort-direction:hover {
  background-color: #eef3fb;
}

.sort-control:focus-within {
  border-color: #7bb1f5;
  box-shadow: 0 0 0 3px rgba(47, 95, 219, 0.12);
}
</style>
