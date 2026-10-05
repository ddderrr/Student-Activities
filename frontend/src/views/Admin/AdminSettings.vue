<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Download,
  Eye,
  FileSpreadsheet,
  FileText,
  LoaderCircle,
  RotateCcw,
  Save,
  Search,
  Info,
  ShieldCheck,
  Trash2,
  TriangleAlert,
  Upload,
  UserPlus,
  Users,
  X
} from 'lucide-vue-next'

import { useLanguage } from '../../composables/useLanguage'
import { adminFetch, getAdminSession } from '../../constants/currentAdmin'
import { BRANCHES } from '../../constants/branches'
import { API_BASE } from '../../config/api'

const { t, currentLanguage } = useLanguage()

// หน้า Settings ใช้ได้เฉพาะแอดมินกลาง (backend ตรวจซ้ำด้วย require_central_admin)
const isCentral = computed(() => Boolean(getAdminSession()?.is_central))
// แอดมินสาขา: จัดการได้เฉพาะนักศึกษาสาขาตัวเอง (backend กรองให้) และไม่มีส่วนจัดการแอดมิน
const adminMajor = computed(() => getAdminSession()?.major || '')

/* =========================
   เมนูแบบ accordion: เปิดได้ทีละหัวข้อ (null = ปิดหมด)
========================= */
const openSection = ref(null)

function toggleSection(key) {
  openSection.value = openSection.value === key ? null : key
  if (openSection.value === 'transcript' && !transcriptLoaded.value) loadTranscriptSettings()
}

/* =========================
   หัวเอกสาร Transcript (แก้แล้วมีผลกับ PDF ที่สร้างหลังบันทึก)
   แต่ละช่องมีภาษาไทย + อังกฤษ เพราะ PDF ออกได้สองภาษา
========================= */
const TRANSCRIPT_FIELDS = [
  { key: 'university_name', label: 'transcriptUniversity' },
  { key: 'faculty_name', label: 'transcriptFaculty' },
  { key: 'document_title', label: 'transcriptTitle' },
  { key: 'signer_name', label: 'transcriptSignerName' },
  { key: 'signer_position', label: 'transcriptSignerPosition' }
]

const transcriptForm = ref({})
const transcriptDefaults = ref({})
const transcriptSaved = ref({})
const transcriptMaxLength = ref(200)
const transcriptLoaded = ref(false)
const transcriptLoading = ref(false)
const transcriptSaving = ref(false)
const transcriptError = ref('')
const transcriptNotice = ref('')

const transcriptDirty = computed(() =>
  Object.keys(transcriptForm.value).some((key) => (transcriptForm.value[key] || '').trim() !== (transcriptSaved.value[key] || ''))
)

function applyTranscriptSettings(data) {
  transcriptDefaults.value = data.defaults
  transcriptSaved.value = { ...data.values }
  transcriptForm.value = { ...data.values }
  transcriptMaxLength.value = data.max_length
  transcriptLoaded.value = true
}

async function loadTranscriptSettings() {
  transcriptLoading.value = true
  transcriptError.value = ''

  try {
    const response = await adminFetch(`${API_BASE}/api/admin/settings/transcript`)
    if (!response.ok) throw new Error()
    applyTranscriptSettings(await response.json())
    loadPreview()
  } catch {
    transcriptError.value = t.value.adminSettings.transcriptLoadError
  } finally {
    transcriptLoading.value = false
  }
}

async function saveTranscriptSettings() {
  if (transcriptSaving.value) return
  transcriptSaving.value = true
  transcriptError.value = ''
  transcriptNotice.value = ''

  try {
    const response = await adminFetch(`${API_BASE}/api/admin/settings/transcript`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(transcriptForm.value)
    })
    const data = await response.json().catch(() => null)
    if (!response.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : t.value.adminSettings.transcriptSaveFailed)

    applyTranscriptSettings(data)
    transcriptNotice.value = t.value.adminSettings.transcriptSaved
  } catch (error) {
    transcriptError.value = error.message || t.value.adminSettings.transcriptSaveFailed
  } finally {
    transcriptSaving.value = false
  }
}

function resetTranscriptToDefaults() {
  transcriptForm.value = { ...transcriptDefaults.value }
  transcriptNotice.value = ''
}

/* ตัวอย่าง PDF: นักศึกษาสมมติ + ค่าที่กรอกอยู่ (ยังไม่บันทึก) อัปเดตเองหลังหยุดพิมพ์ */
const PREVIEW_DELAY_MS = 900
const previewStyle = ref('A')
const previewLang = ref('th')
const previewUrl = ref('')
const previewLoading = ref(false)
const previewError = ref('')
let previewTimer = null
let previewRequest = 0
// ค่าที่ส่งไปทำตัวอย่างล่าสุด: ฟอร์มถูกตั้งค่าใหม่แต่ค่าเท่าเดิม (เช่น หลังบันทึก) ไม่ต้องทำซ้ำ
let previewFormKey = ''

function clearPreview() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
}

async function loadPreview() {
  clearTimeout(previewTimer)
  const request = ++previewRequest
  previewFormKey = JSON.stringify(transcriptForm.value)
  previewLoading.value = true
  previewError.value = ''

  try {
    const params = new URLSearchParams({ style: previewStyle.value, lang: previewLang.value })
    const response = await adminFetch(`${API_BASE}/api/admin/settings/transcript/preview?${params}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(transcriptForm.value)
    })
    if (!response.ok) {
      const data = await response.json().catch(() => null)
      throw new Error(typeof data?.detail === 'string' ? data.detail : t.value.adminSettings.transcriptPreviewFailed)
    }
    const blob = await response.blob()
    // คำขอเก่าที่ตอบช้ากว่าคำขอใหม่ ทิ้งไป
    if (request !== previewRequest) return
    clearPreview()
    previewUrl.value = URL.createObjectURL(blob)
  } catch (error) {
    if (request === previewRequest) previewError.value = error.message || t.value.adminSettings.transcriptPreviewFailed
  } finally {
    if (request === previewRequest) previewLoading.value = false
  }
}

function schedulePreview() {
  clearTimeout(previewTimer)
  previewTimer = setTimeout(loadPreview, PREVIEW_DELAY_MS)
}

watch([previewStyle, previewLang], () => {
  if (transcriptLoaded.value) loadPreview()
})

watch(transcriptForm, () => {
  if (!transcriptLoaded.value || openSection.value !== 'transcript') return
  if (JSON.stringify(transcriptForm.value) !== previewFormKey) schedulePreview()
}, { deep: true })

watch(openSection, (key) => {
  if (key !== 'transcript') {
    clearTimeout(previewTimer)
    previewRequest++
    previewLoading.value = false
    clearPreview()
  } else if (transcriptLoaded.value) {
    loadPreview()
  }
})

const MAX_BYTES = 5 * 1024 * 1024
const ACCEPTED_EXTENSIONS = ['.xlsx', '.xls', '.csv']
const TEMPLATE_COLUMNS = ['รหัสนักศึกษา', 'ชื่อ', 'นามสกุล', 'อีเมล', 'สาขาวิชา']

// ขั้นตอน: select -> preview (dry run) -> result
const step = ref('select')
const selectedFile = ref(null)
const preview = ref(null)
const result = ref(null)
const busy = ref(false)
const errorMessage = ref('')
const isDragging = ref(false)
const fileInput = ref(null)
const templateDownloading = ref(false)

const statusLabels = computed(() => ({
  new: t.value.adminSettings.statusNew,
  duplicate: t.value.adminSettings.statusDuplicate,
  invalid: t.value.adminSettings.statusInvalid
}))

const issueRows = computed(() => result.value?.errors || [])

function resetImport() {
  step.value = 'select'
  selectedFile.value = null
  preview.value = null
  result.value = null
  errorMessage.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

function openFilePicker() {
  if (!busy.value) fileInput.value?.click()
}

function fileExtension(name) {
  const dot = name.lastIndexOf('.')
  return dot === -1 ? '' : name.slice(dot).toLowerCase()
}

async function postImport(file, dryRun) {
  const body = new FormData()
  body.append('file', file)

  const response = await adminFetch(
    `${API_BASE}/api/admin/students/import${dryRun ? '?dry_run=true' : ''}`,
    { method: 'POST', body }
  )
  const data = await response.json().catch(() => null)

  if (!response.ok) {
    throw new Error(typeof data?.detail === 'string' ? data.detail : t.value.adminSettings.requestError)
  }

  return data
}

async function handleFile(file) {
  if (!file || busy.value) return

  errorMessage.value = ''

  if (!ACCEPTED_EXTENSIONS.includes(fileExtension(file.name))) {
    errorMessage.value = t.value.adminSettings.fileTypeError
    return
  }

  if (file.size > MAX_BYTES) {
    errorMessage.value = t.value.adminSettings.fileSizeError
    return
  }

  busy.value = true

  try {
    preview.value = await postImport(file, true)
    selectedFile.value = file
    step.value = 'preview'
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    busy.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

function onFileChange(event) {
  handleFile(event.target.files?.[0])
}

function onDrop(event) {
  isDragging.value = false
  handleFile(event.dataTransfer.files?.[0])
}

async function confirmImport() {
  if (!selectedFile.value || busy.value || !preview.value?.success) return

  busy.value = true
  errorMessage.value = ''

  try {
    result.value = await postImport(selectedFile.value, false)
    step.value = 'result'
    loadStudents()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    busy.value = false
  }
}

async function downloadTemplate() {
  if (templateDownloading.value) return

  templateDownloading.value = true
  errorMessage.value = ''

  try {
    const response = await adminFetch(`${API_BASE}/api/admin/students/import/template`)
    if (!response.ok) throw new Error()

    const url = URL.createObjectURL(await response.blob())
    const link = document.createElement('a')
    link.href = url
    link.download = 'student-import-template.xlsx'
    document.body.appendChild(link)
    link.click()
    link.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch {
    errorMessage.value = t.value.adminSettings.templateError
  } finally {
    templateDownloading.value = false
  }
}


/* =========================
   นักศึกษาทั้งหมด
========================= */

// ปกติแสดง 5 คนล่าสุด กด "ดูทั้งหมด" แล้วจึงแบ่งหน้า หน้าละ 20 คน
const PREVIEW_SIZE = 5
const PAGE_SIZE = 20
const showAllStudents = ref(false)
const studentsPageSize = computed(() => (showAllStudents.value ? PAGE_SIZE : PREVIEW_SIZE))

const students = ref([])
const studentsTotal = ref(0)
const studentsAllTotal = ref(0)
const studentsPage = ref(1)
const studentsLoading = ref(false)
const studentsError = ref('')
const studentSearch = ref('')
const notice = ref('')

const studentsPages = computed(() => Math.max(1, Math.ceil(studentsTotal.value / studentsPageSize.value)))

const fill = (text, values) =>
  Object.entries(values).reduce((out, [key, value]) => out.replaceAll(`{${key}}`, value), text)

const fullName = (student) => `${student.first_name} ${student.last_name}`.trim()

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleDateString(currentLanguage.value === 'TH' ? 'th-TH' : 'en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}

// คำขอที่ตอบกลับช้ากว่าคำขอล่าสุด (เช่นพิมพ์ค้นหาเร็ว ๆ) ไม่ต้องเอามาแสดง
let studentsRequest = 0

async function loadStudents() {
  const request = ++studentsRequest
  studentsLoading.value = true
  studentsError.value = ''

  const params = new URLSearchParams({ page: studentsPage.value, page_size: studentsPageSize.value })
  if (studentSearch.value.trim()) params.set('search', studentSearch.value.trim())

  try {
    const response = await adminFetch(`${API_BASE}/api/admin/students?${params}`)
    const data = await response.json().catch(() => null)
    if (!response.ok) throw new Error()
    if (request !== studentsRequest) return

    students.value = data.students
    studentsTotal.value = data.total
    studentsAllTotal.value = data.all_total

    // ลบรายการสุดท้ายของหน้าสุดท้าย: ถอยไปหน้าก่อนหน้าแทนการแสดงหน้าว่าง
    if (!data.students.length && studentsPage.value > 1) {
      studentsPage.value = Math.max(1, Math.ceil(data.total / studentsPageSize.value))
      return loadStudents()
    }
  } catch {
    if (request === studentsRequest) studentsError.value = t.value.adminSettings.studentsLoadError
  } finally {
    if (request === studentsRequest) studentsLoading.value = false
  }
}

let searchTimer = null
watch(studentSearch, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    studentsPage.value = 1
    loadStudents()
  }, 300)
})

function toggleShowAllStudents() {
  showAllStudents.value = !showAllStudents.value
  studentsPage.value = 1
  loadStudents()
}

function goToStudentsPage(page) {
  if (page < 1 || page > studentsPages.value || page === studentsPage.value) return
  studentsPage.value = page
  loadStudents()
}

// ---- ลบ: { mode: 'one', student } | { mode: 'all' } | { mode: 'admin', admin }
const deleteTarget = ref(null)
const deleteConfirmText = ref('')
const deleting = ref(false)
const deleteError = ref('')
const deleteCancelButton = ref(null)

const deleteAllReady = computed(() =>
  deleteConfirmText.value.trim() === t.value.adminSettings.deleteConfirmWord
)

async function openDelete(target) {
  deleteTarget.value = target
  deleteConfirmText.value = ''
  deleteError.value = ''
  notice.value = ''
  adminNotice.value = ''
  await nextTick()
  deleteCancelButton.value?.focus()
}

function closeDelete() {
  if (deleting.value) return
  deleteTarget.value = null
}

async function confirmDelete() {
  const target = deleteTarget.value
  if (!target || deleting.value) return
  if (target.mode === 'all' && !deleteAllReady.value) return

  deleting.value = true
  deleteError.value = ''

  const url = {
    all: `${API_BASE}/api/admin/students?confirm=all`,
    one: () => `${API_BASE}/api/admin/students/${encodeURIComponent(target.student.student_id)}`,
    admin: () => `${API_BASE}/api/admin/admins/${target.admin.id}`
  }[target.mode]

  try {
    const response = await adminFetch(typeof url === 'function' ? url() : url, { method: 'DELETE' })
    const data = await response.json().catch(() => null)
    if (!response.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : '')

    deleting.value = false
    deleteTarget.value = null

    if (target.mode === 'admin') {
      adminNotice.value = fill(t.value.adminSettings.adminDeleted, { name: target.admin.name || target.admin.email })
      loadAdmins()
      return
    }

    notice.value = target.mode === 'all'
      ? fill(t.value.adminSettings.deletedAll, { count: data.students })
      : fill(t.value.adminSettings.deletedOne, { name: fullName(target.student) })
    if (target.mode === 'all') studentsPage.value = 1
    loadStudents()
  } catch (error) {
    deleteError.value = error.message || t.value.adminSettings.deleteFailed
  } finally {
    deleting.value = false
  }
}

/* =========================
   แอดมินสาขา
========================= */

const admins = ref([])
const adminsLoading = ref(false)
const adminsError = ref('')
const adminNotice = ref('')

async function loadAdmins() {
  adminsLoading.value = true
  adminsError.value = ''

  try {
    const response = await adminFetch(`${API_BASE}/api/admin/admins`)
    const data = await response.json().catch(() => null)
    if (!response.ok) throw new Error()
    admins.value = data.admins
  } catch {
    adminsError.value = t.value.adminSettings.adminsLoadError
  } finally {
    adminsLoading.value = false
  }
}

// กรอกแค่อีเมล + สาขา: backend ตั้งชื่อ "แอดมินสาขา <สาขา>" และรหัสผ่านเริ่มต้นให้
const emptyAdminForm = () => ({ email: '', major: '' })

const showAddAdmin = ref(false)
const adminForm = ref(emptyAdminForm())
const adminFormError = ref('')
const savingAdmin = ref(false)
const adminEmailField = ref(null)

async function openAddAdmin() {
  adminForm.value = emptyAdminForm()
  adminFormError.value = ''
  adminNotice.value = ''
  showAddAdmin.value = true
  await nextTick()
  adminEmailField.value?.focus()
}

function closeAddAdmin() {
  if (!savingAdmin.value) showAddAdmin.value = false
}

async function saveAdmin() {
  if (savingAdmin.value) return

  const form = adminForm.value
  const email = form.email.trim()

  if (!email || !form.major) {
    adminFormError.value = t.value.adminSettings.adminRequiredError
    return
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    adminFormError.value = t.value.adminSettings.adminEmailError
    return
  }

  savingAdmin.value = true
  adminFormError.value = ''

  try {
    const response = await adminFetch(`${API_BASE}/api/admin/admins`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form, email })
    })
    const data = await response.json().catch(() => null)
    if (!response.ok) {
      throw new Error(typeof data?.detail === 'string' ? data.detail : t.value.adminSettings.adminSaveFailed)
    }

    adminNotice.value = fill(t.value.adminSettings.adminCreated, { name: data.name || data.email })
    savingAdmin.value = false
    showAddAdmin.value = false
    loadAdmins()
  } catch (error) {
    adminFormError.value = error.message || t.value.adminSettings.adminSaveFailed
  } finally {
    savingAdmin.value = false
  }
}

function onKeydown(event) {
  if (event.key !== 'Escape') return
  if (deleteTarget.value) closeDelete()
  else if (showAddAdmin.value) closeAddAdmin()
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  loadStudents()
  if (isCentral.value) loadAdmins()
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  clearTimeout(searchTimer)
  clearTimeout(previewTimer)
  clearPreview()
})
</script>

<template>
  <div class="settings-page">
    <header class="page-header">
      <h1>{{ t.adminSettings.title }}</h1>
      <p>{{ isCentral ? t.adminSettings.subtitle : fill(t.adminSettings.subtitleBranch, { major: adminMajor }) }}</p>
    </header>

    <!-- เมนูแบบ accordion เปิดได้ทีละหัวข้อ (แอดมินสาขา: ไม่มีส่วนจัดการแอดมิน) -->
    <div class="settings-menu">

    <!-- 1) จัดการนักศึกษา -->
    <section class="settings-panel" :class="{ open: openSection === 'students' }" data-section="students">
      <div class="panel-header">
        <span class="panel-icon students"><Users :size="22" /></span>
        <div class="panel-text">
          <h2 id="panel-students-title">{{ t.adminSettings.sectionStudents }}</h2>
          <p>{{ isCentral ? t.adminSettings.sectionStudentsDescription : fill(t.adminSettings.sectionStudentsDescriptionBranch, { major: adminMajor }) }}</p>
        </div>
        <span class="panel-meta">{{ fill(t.adminSettings.studentsCount, { count: studentsAllTotal }) }}</span>
        <button
          type="button"
          class="panel-toggle"
          :aria-expanded="openSection === 'students'"
          aria-controls="panel-students-body"
          data-testid="toggle-students"
          @click="toggleSection('students')"
        >
          {{ openSection === 'students' ? t.adminSettings.closeSection : t.adminSettings.manageSection }}
          <ChevronDown :size="16" class="chevron" />
        </button>
      </div>

      <div v-show="openSection === 'students'" id="panel-students-body" class="panel-body" role="region" aria-labelledby="panel-students-title">
    <section class="card import-card" data-testid="student-import">
      <div class="card-header">
        <div class="card-title">
          <span class="card-icon"><Users :size="18" /></span>
          <div>
            <h2>{{ t.adminSettings.importTitle }}</h2>
            <p>{{ t.adminSettings.importDescription }}</p>
            <p v-if="!isCentral" class="branch-scope-note" data-testid="import-branch-note">{{ fill(t.adminSettings.importBranchNote, { major: adminMajor }) }}</p>
          </div>
        </div>

        <button
          type="button"
          class="secondary-button"
          :disabled="templateDownloading"
          data-testid="download-template"
          @click="downloadTemplate"
        >
          <LoaderCircle v-if="templateDownloading" class="spin" :size="16" />
          <Download v-else :size="16" />
          {{ t.adminSettings.downloadTemplate }}
        </button>
      </div>

      <div class="column-list">
        <span class="column-list-label">{{ t.adminSettings.requiredColumns }}:</span>
        <code v-for="column in TEMPLATE_COLUMNS" :key="column">{{ column }}</code>
      </div>

      <div v-if="errorMessage" class="alert error" role="alert">
        <TriangleAlert :size="16" />
        <span>{{ errorMessage }}</span>
      </div>

      <!-- 1) เลือกไฟล์ -->
      <div
        v-if="step === 'select'"
        class="dropzone"
        :class="{ dragging: isDragging, busy }"
        role="button"
        tabindex="0"
        :aria-label="t.adminSettings.dropzoneTitle"
        data-testid="import-dropzone"
        @click="openFilePicker"
        @keydown.enter.prevent="openFilePicker"
        @keydown.space.prevent="openFilePicker"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="onDrop"
      >
        <input
          ref="fileInput"
          class="file-input"
          type="file"
          accept=".xlsx,.xls,.csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,text/csv"
          @click.stop
          @change="onFileChange"
        />

        <span class="dropzone-icon">
          <LoaderCircle v-if="busy" class="spin" :size="26" />
          <Upload v-else :size="26" />
        </span>
        <strong>{{ busy ? t.adminSettings.reading : t.adminSettings.dropzoneTitle }}</strong>
        <p>{{ t.adminSettings.dropzoneHint }}</p>
        <span class="pill-button">{{ t.adminSettings.chooseFile }}</span>
      </div>

      <!-- 2) พรีวิว -->
      <template v-else-if="step === 'preview' && preview">
        <div class="preview-header">
          <div class="file-chip">
            <FileSpreadsheet :size="18" />
            <span>{{ selectedFile?.name }}</span>
          </div>

          <div class="summary-row">
            <span class="summary-chip">{{ t.adminSettings.summaryTotal }} <b>{{ preview.total }}</b></span>
            <span class="summary-chip new">{{ t.adminSettings.summaryNew }} <b>{{ preview.success }}</b></span>
            <span class="summary-chip duplicate">{{ t.adminSettings.summarySkipped }} <b>{{ preview.skipped }}</b></span>
            <span class="summary-chip invalid">{{ t.adminSettings.summaryFailed }} <b>{{ preview.failed }}</b></span>
          </div>
        </div>

        <h3 class="section-title">{{ t.adminSettings.previewTitle }}</h3>
        <p class="section-hint">{{ t.adminSettings.previewHint }}</p>

        <p v-if="!preview.total" class="empty-state">{{ t.adminSettings.emptyFile }}</p>

        <div v-else class="table-wrap" data-testid="import-preview">
          <table>
            <thead>
              <tr>
                <th>{{ t.adminSettings.columnRow }}</th>
                <th>{{ t.adminSettings.columnStudentId }}</th>
                <th>{{ t.adminSettings.columnFirstName }}</th>
                <th>{{ t.adminSettings.columnLastName }}</th>
                <th>{{ t.adminSettings.columnEmail }}</th>
                <th>{{ t.adminSettings.columnMajor }}</th>
                <th>{{ t.adminSettings.columnStatus }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in preview.rows" :key="row.row" :class="`row-${row.status}`">
                <td class="muted">{{ row.row }}</td>
                <td class="mono">{{ row.student_id || '—' }}</td>
                <td>{{ row.first_name || '—' }}</td>
                <td>{{ row.last_name || '—' }}</td>
                <td>{{ row.email || '—' }}</td>
                <td>{{ row.major || '—' }}</td>
                <td>
                  <span class="status-badge" :class="row.status">{{ statusLabels[row.status] }}</span>
                  <small v-if="row.message" class="status-reason">{{ row.message }}</small>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="actions">
          <button type="button" class="secondary-button" :disabled="busy" @click="resetImport">
            <RotateCcw :size="16" />
            {{ t.adminSettings.chooseAnotherFile }}
          </button>

          <button
            type="button"
            class="primary-button"
            :disabled="busy || !preview.success"
            :title="preview.success ? '' : t.adminSettings.noNewRows"
            data-testid="confirm-import"
            @click="confirmImport"
          >
            <LoaderCircle v-if="busy" class="spin" :size="16" />
            <CheckCircle2 v-else :size="16" />
            {{ busy ? t.adminSettings.importing : t.adminSettings.confirmImport }}
          </button>
        </div>
        <p v-if="!preview.success && preview.total" class="no-new-rows">{{ t.adminSettings.noNewRows }}</p>
      </template>

      <!-- 3) ผลลัพธ์ -->
      <div v-else-if="step === 'result' && result" class="result" data-testid="import-result">
        <div class="result-heading">
          <span class="result-icon"><CheckCircle2 :size="28" /></span>
          <h3>{{ t.adminSettings.resultTitle }}</h3>
        </div>

        <div class="result-grid">
          <div class="result-stat">
            <span>{{ t.adminSettings.summaryTotal }}</span>
            <strong>{{ result.total }}</strong>
          </div>
          <div class="result-stat new">
            <span>{{ t.adminSettings.summarySuccess }}</span>
            <strong>{{ result.success }}</strong>
          </div>
          <div class="result-stat duplicate">
            <span>{{ t.adminSettings.summarySkipped }}</span>
            <strong>{{ result.skipped }}</strong>
          </div>
          <div class="result-stat invalid">
            <span>{{ t.adminSettings.summaryFailed }}</span>
            <strong>{{ result.failed }}</strong>
          </div>
        </div>

        <div v-if="issueRows.length" class="issues">
          <h4>{{ t.adminSettings.issuesTitle }}</h4>
          <ul>
            <li v-for="issue in issueRows" :key="issue.row" :class="issue.type">
              <span class="status-badge" :class="issue.type">{{ statusLabels[issue.type] }}</span>
              <span>{{ t.adminSettings.columnRow }} {{ issue.row }}</span>
              <span class="mono">{{ issue.student_id || '—' }}</span>
              <span class="muted">{{ issue.message }}</span>
            </li>
          </ul>
        </div>

        <div class="actions">
          <button type="button" class="primary-button" @click="resetImport">
            <X :size="16" />
            {{ t.adminSettings.importAnother }}
          </button>
        </div>
      </div>
    </section>

    <!-- นักศึกษาทั้งหมด -->
    <section class="card students-card" data-testid="students-list">
      <div class="card-header">
        <div class="card-title">
          <span class="card-icon"><Users :size="18" /></span>
          <div>
            <h2>{{ t.adminSettings.studentsTitle }}</h2>
            <p>
              {{ isCentral ? t.adminSettings.studentsDescription : fill(t.adminSettings.studentsDescriptionBranch, { major: adminMajor }) }} ·
              <strong>
                {{
                  studentSearch.trim()
                    ? fill(t.adminSettings.studentsFound, { count: studentsTotal, all: studentsAllTotal })
                    : fill(t.adminSettings.studentsCount, { count: studentsAllTotal })
                }}
              </strong>
            </p>
          </div>
        </div>

        <button
          type="button"
          class="danger-outline-button"
          :disabled="!studentsAllTotal || deleting"
          data-testid="delete-all-students"
          @click="openDelete({ mode: 'all' })"
        >
          <Trash2 :size="16" />
          {{ t.adminSettings.deleteAllButton }}
        </button>
      </div>

      <label class="search-box">
        <Search :size="16" />
        <input
          v-model="studentSearch"
          type="search"
          :placeholder="t.adminSettings.searchPlaceholder"
          :aria-label="t.adminSettings.searchPlaceholder"
          data-testid="student-search"
        />
      </label>

      <div v-if="notice" class="alert success" role="status">
        <CheckCircle2 :size="16" />
        <span>{{ notice }}</span>
      </div>

      <div v-if="studentsError" class="alert error" role="alert">
        <TriangleAlert :size="16" />
        <span>{{ studentsError }}</span>
        <button type="button" class="link-button" @click="loadStudents">{{ t.adminSettings.retry }}</button>
      </div>

      <p v-else-if="studentsLoading && !students.length" class="empty-state">{{ t.adminSettings.studentsLoading }}</p>

      <p v-else-if="!students.length" class="empty-state">
        {{ studentSearch.trim() ? t.adminSettings.studentsNoMatch : t.adminSettings.studentsEmpty }}
      </p>

      <div v-else class="table-wrap students-table" :class="{ loading: studentsLoading }">
        <table>
          <thead>
            <tr>
              <th>{{ t.adminSettings.columnStudentId }}</th>
              <th>{{ t.adminSettings.columnName }}</th>
              <th>{{ t.adminSettings.columnEmail }}</th>
              <th>{{ t.adminSettings.columnMajor }}</th>
              <th>{{ t.adminSettings.columnActivities }}</th>
              <th>{{ t.adminSettings.columnAdded }}</th>
              <th class="actions-column">{{ t.adminSettings.columnActions }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="student in students" :key="student.student_id" :data-student="student.student_id">
              <td class="mono">{{ student.student_id }}</td>
              <td>{{ fullName(student) || '—' }}</td>
              <td>{{ student.email || '—' }}</td>
              <td>
                <span v-if="student.major">{{ student.major }}</span>
                <span v-else class="status-badge duplicate" :title="t.adminSettings.noMajorHint">
                  {{ t.adminSettings.noMajor }}
                </span>
              </td>
              <td class="muted">
                {{ fill(t.adminSettings.activitySummary, { faculty: student.activity_count, external: student.external_activity_count }) }}
              </td>
              <td class="muted">{{ formatDate(student.created_at) }}</td>
              <td class="actions-column">
                <button
                  type="button"
                  class="icon-danger-button"
                  :aria-label="fill(t.adminSettings.deleteStudentAria, { name: fullName(student) })"
                  :title="fill(t.adminSettings.deleteStudentAria, { name: fullName(student) })"
                  @click="openDelete({ mode: 'one', student })"
                >
                  <Trash2 :size="16" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="studentsTotal > PREVIEW_SIZE" class="view-all-row">
        <button
          type="button"
          class="secondary-button"
          :aria-expanded="showAllStudents"
          data-testid="toggle-all-students"
          @click="toggleShowAllStudents"
        >
          {{
            showAllStudents
              ? t.adminSettings.showLess
              : fill(t.adminSettings.viewAll, { count: studentsTotal })
          }}
        </button>
      </div>

      <div v-if="showAllStudents && studentsTotal > PAGE_SIZE" class="pagination">
        <button
          type="button"
          class="secondary-button square"
          :disabled="studentsPage === 1 || studentsLoading"
          :aria-label="t.adminSettings.previousPage"
          @click="goToStudentsPage(studentsPage - 1)"
        >
          <ChevronLeft :size="16" />
        </button>
        <span>{{ fill(t.adminSettings.pageInfo, { page: studentsPage, pages: studentsPages }) }}</span>
        <button
          type="button"
          class="secondary-button square"
          :disabled="studentsPage === studentsPages || studentsLoading"
          :aria-label="t.adminSettings.nextPage"
          @click="goToStudentsPage(studentsPage + 1)"
        >
          <ChevronRight :size="16" />
        </button>
      </div>
    </section>

      </div>
    </section>

    <!-- 2) จัดการแอดมิน -->
    <section v-if="isCentral" class="settings-panel" :class="{ open: openSection === 'admins' }" data-section="admins">
      <div class="panel-header">
        <span class="panel-icon admins"><ShieldCheck :size="22" /></span>
        <div class="panel-text">
          <h2 id="panel-admins-title">{{ t.adminSettings.sectionAdmins }}</h2>
          <p>{{ t.adminSettings.sectionAdminsDescription }}</p>
        </div>
        <span class="panel-meta">{{ fill(t.adminSettings.adminsCount, { count: admins.length }) }}</span>
        <button
          type="button"
          class="panel-toggle"
          :aria-expanded="openSection === 'admins'"
          aria-controls="panel-admins-body"
          data-testid="toggle-admins"
          @click="toggleSection('admins')"
        >
          {{ openSection === 'admins' ? t.adminSettings.closeSection : t.adminSettings.manageSection }}
          <ChevronDown :size="16" class="chevron" />
        </button>
      </div>

      <div v-show="openSection === 'admins'" id="panel-admins-body" class="panel-body" role="region" aria-labelledby="panel-admins-title">
    <section class="card admins-card" data-testid="admins-list">
      <div class="card-header">
        <div class="card-title">
          <span class="card-icon"><ShieldCheck :size="18" /></span>
          <div>
            <h2>{{ t.adminSettings.adminsTitle }}</h2>
            <p>
              {{ t.adminSettings.adminsDescription }} ·
              <strong>{{ fill(t.adminSettings.adminsCount, { count: admins.length }) }}</strong>
            </p>
          </div>
        </div>

        <button type="button" class="primary-button" data-testid="add-admin" @click="openAddAdmin">
          <UserPlus :size="16" />
          {{ t.adminSettings.addAdminButton }}
        </button>
      </div>

      <div v-if="adminNotice" class="alert success" role="status">
        <CheckCircle2 :size="16" />
        <span>{{ adminNotice }}</span>
      </div>

      <div v-if="adminsError" class="alert error" role="alert">
        <TriangleAlert :size="16" />
        <span>{{ adminsError }}</span>
        <button type="button" class="link-button" @click="loadAdmins">{{ t.adminSettings.retry }}</button>
      </div>

      <p v-else-if="adminsLoading && !admins.length" class="empty-state">{{ t.adminSettings.adminsLoading }}</p>

      <p v-else-if="!admins.length" class="empty-state">{{ t.adminSettings.adminsEmpty }}</p>

      <div v-else class="table-wrap admins-table">
        <table>
          <thead>
            <tr>
              <th>{{ t.adminSettings.columnName }}</th>
              <th>{{ t.adminSettings.columnEmail }}</th>
              <th>{{ t.adminSettings.columnBranch }}</th>
              <th class="actions-column">{{ t.adminSettings.columnActions }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="admin in admins" :key="admin.id" :data-admin="admin.email">
              <td>{{ admin.name || '—' }}</td>
              <td>{{ admin.email }}</td>
              <td><span class="branch-chip">{{ admin.major }}</span></td>
              <td class="actions-column">
                <button
                  type="button"
                  class="icon-danger-button"
                  :aria-label="fill(t.adminSettings.deleteAdminAria, { name: admin.name || admin.email })"
                  :title="fill(t.adminSettings.deleteAdminAria, { name: admin.name || admin.email })"
                  @click="openDelete({ mode: 'admin', admin })"
                >
                  <Trash2 :size="16" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
      </div>
    </section>

    <!-- 3) จัดการทรานสคริปต์ -->
    <section class="settings-panel" :class="{ open: openSection === 'transcript' }" data-section="transcript">
      <div class="panel-header">
        <span class="panel-icon transcript"><FileText :size="22" /></span>
        <div class="panel-text">
          <h2 id="panel-transcript-title">{{ t.adminSettings.sectionTranscript }}</h2>
          <p>{{ t.adminSettings.sectionTranscriptDescription }}</p>
        </div>
        <button
          type="button"
          class="panel-toggle"
          :aria-expanded="openSection === 'transcript'"
          aria-controls="panel-transcript-body"
          data-testid="toggle-transcript"
          @click="toggleSection('transcript')"
        >
          {{ openSection === 'transcript' ? t.adminSettings.closeSection : t.adminSettings.manageSection }}
          <ChevronDown :size="16" class="chevron" />
        </button>
      </div>

      <div v-if="openSection === 'transcript'" id="panel-transcript-body" class="panel-body" role="region" aria-labelledby="panel-transcript-title">
        <form class="card transcript-card" novalidate data-testid="transcript-settings" @submit.prevent="saveTranscriptSettings" @input="transcriptNotice = ''">
          <div class="card-header">
            <div class="card-title">
              <span class="card-icon"><FileText :size="18" /></span>
              <div>
                <h2>{{ t.adminSettings.transcriptHeaderTitle }}</h2>
                <p>{{ t.adminSettings.transcriptHeaderDescription }}</p>
              </div>
            </div>
          </div>

          <p v-if="transcriptLoading && !transcriptLoaded" class="empty-state">{{ t.adminSettings.transcriptLoading }}</p>

          <template v-else-if="transcriptLoaded">
            <div class="transcript-grid">
              <span class="grid-head"></span>
              <span class="grid-head">{{ t.adminSettings.transcriptThai }}</span>
              <span class="grid-head">{{ t.adminSettings.transcriptEnglish }}</span>

              <template v-for="field in TRANSCRIPT_FIELDS" :key="field.key">
                <span class="field-label">{{ t.adminSettings[field.label] }}</span>
                <input
                  v-model="transcriptForm[field.key]"
                  type="text"
                  :name="field.key"
                  :maxlength="transcriptMaxLength"
                  :placeholder="transcriptDefaults[field.key]"
                  :aria-label="`${t.adminSettings[field.label]} (${t.adminSettings.transcriptThai})`"
                />
                <input
                  v-model="transcriptForm[`${field.key}_en`]"
                  type="text"
                  :name="`${field.key}_en`"
                  :maxlength="transcriptMaxLength"
                  :placeholder="transcriptDefaults[`${field.key}_en`]"
                  :aria-label="`${t.adminSettings[field.label]} (${t.adminSettings.transcriptEnglish})`"
                />
              </template>
            </div>

            <p class="transcript-hint">
              <Info :size="15" />
              {{ t.adminSettings.transcriptHint }}
            </p>
          </template>

          <div v-if="transcriptError" class="alert error" role="alert">
            <TriangleAlert :size="16" />
            <span>{{ transcriptError }}</span>
            <button v-if="!transcriptLoaded" type="button" class="link-button" @click="loadTranscriptSettings">{{ t.adminSettings.retry }}</button>
          </div>

          <div v-if="transcriptNotice" class="alert success" role="status">
            <CheckCircle2 :size="16" />
            <span>{{ transcriptNotice }}</span>
          </div>

          <div v-if="transcriptLoaded" class="actions">
            <button type="button" class="secondary-button" :disabled="transcriptSaving" @click="resetTranscriptToDefaults">
              <RotateCcw :size="16" />
              {{ t.adminSettings.transcriptResetDefaults }}
            </button>
            <button type="submit" class="primary-button" :disabled="transcriptSaving || !transcriptDirty" data-testid="save-transcript-settings">
              <LoaderCircle v-if="transcriptSaving" class="spin" :size="16" />
              <Save v-else :size="16" />
              {{ transcriptSaving ? t.adminSettings.saving : t.adminSettings.saveButton }}
            </button>
          </div>
        </form>

        <div v-if="transcriptLoaded" class="card preview-card" data-testid="transcript-preview">
          <div class="card-header">
            <div class="card-title">
              <span class="card-icon"><Eye :size="20" /></span>
              <div>
                <h2>{{ t.adminSettings.transcriptPreviewTitle }}</h2>
                <p>{{ t.adminSettings.transcriptPreviewDescription }}</p>
              </div>
            </div>
          </div>

          <div class="preview-toolbar">
            <div class="segmented" role="group" :aria-label="t.adminSettings.transcriptPreviewStyle">
              <span class="segmented-label">{{ t.adminSettings.transcriptPreviewStyle }}</span>
              <button
                v-for="style in ['A', 'B']"
                :key="style"
                type="button"
                :class="{ active: previewStyle === style }"
                :aria-pressed="previewStyle === style"
                :data-testid="`preview-style-${style}`"
                @click="previewStyle = style"
              >
                {{ style === 'A' ? t.adminSettings.transcriptStyleA : t.adminSettings.transcriptStyleB }}
              </button>
            </div>
            <div class="segmented" role="group" :aria-label="t.adminSettings.transcriptPreviewLanguage">
              <span class="segmented-label">{{ t.adminSettings.transcriptPreviewLanguage }}</span>
              <button
                v-for="lang in ['th', 'en']"
                :key="lang"
                type="button"
                :class="{ active: previewLang === lang }"
                :aria-pressed="previewLang === lang"
                :data-testid="`preview-lang-${lang}`"
                @click="previewLang = lang"
              >
                {{ lang === 'th' ? t.adminSettings.transcriptThai : 'English' }}
              </button>
            </div>
            <button type="button" class="secondary-button refresh-preview" :disabled="previewLoading" @click="loadPreview">
              <LoaderCircle v-if="previewLoading" class="spin" :size="16" />
              <RotateCcw v-else :size="16" />
              {{ t.adminSettings.transcriptPreviewRefresh }}
            </button>
          </div>

          <div v-if="previewError" class="alert error" role="alert">
            <TriangleAlert :size="16" />
            <span>{{ previewError }}</span>
          </div>

          <div class="preview-frame" :class="{ loading: previewLoading }">
            <iframe
              v-if="previewUrl"
              :src="`${previewUrl}#view=FitH`"
              :title="t.adminSettings.transcriptPreviewTitle"
              data-testid="transcript-preview-frame"
            ></iframe>
            <div v-if="previewLoading" class="preview-overlay">
              <LoaderCircle class="spin" :size="22" />
              <span>{{ t.adminSettings.transcriptPreviewLoading }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
    </div>

    <!-- เพิ่มแอดมินสาขา: คลิกนอกกรอบไม่ปิด (Esc / ยกเลิก = ปิด) -->
    <div v-if="showAddAdmin" class="modal-backdrop" data-testid="add-admin-modal">
      <form
        class="modal form-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="add-admin-title"
        novalidate
        @submit.prevent="saveAdmin"
        @input="adminFormError = ''"
      >
        <div class="form-modal-header">
          <span class="form-modal-icon" aria-hidden="true"><UserPlus :size="22" /></span>
          <div>
            <h3 id="add-admin-title">{{ t.adminSettings.addAdminTitle }}</h3>
            <p>{{ t.adminSettings.addAdminSubtitle }}</p>
          </div>
        </div>

        <div class="form-grid">
          <label class="form-field full">
            <span>{{ t.adminSettings.fieldEmail }} <b>*</b></span>
            <input ref="adminEmailField" v-model="adminForm.email" type="email" maxlength="255" autocomplete="off" name="email" placeholder="name@example.com" />
          </label>
          <label class="form-field full">
            <span>{{ t.adminSettings.fieldBranch }} <b>*</b></span>
            <select v-model="adminForm.major" name="major">
              <option disabled value="">{{ t.adminSettings.selectBranch }}</option>
              <option v-for="branch in BRANCHES" :key="branch" :value="branch">{{ branch }}</option>
            </select>
          </label>
        </div>

        <p class="default-password-note">
          <Info :size="16" />
          <span>{{ t.adminSettings.defaultPasswordNote }}</span>
        </p>

        <div v-if="adminFormError" class="alert error" role="alert">
          <TriangleAlert :size="16" />
          <span>{{ adminFormError }}</span>
        </div>

        <div class="modal-actions">
          <button type="button" class="secondary-button" :disabled="savingAdmin" @click="closeAddAdmin">
            {{ t.adminSettings.cancelButton }}
          </button>
          <button type="submit" class="primary-button" :disabled="savingAdmin" data-testid="save-admin">
            <LoaderCircle v-if="savingAdmin" class="spin" :size="16" />
            {{ savingAdmin ? t.adminSettings.saving : t.adminSettings.saveButton }}
          </button>
        </div>
      </form>
    </div>

    <!-- ยืนยันการลบ: คลิกนอกกรอบไม่ปิด (Esc = ยกเลิก) -->
    <div v-if="deleteTarget" class="modal-backdrop" data-testid="delete-modal">
      <div
        class="modal"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="delete-modal-title"
        aria-describedby="delete-modal-message"
      >
        <span class="modal-icon" aria-hidden="true"><Trash2 :size="26" /></span>

        <h3 id="delete-modal-title">
          {{
            deleteTarget.mode === 'all'
              ? t.adminSettings.deleteAllTitle
              : deleteTarget.mode === 'admin' ? t.adminSettings.deleteAdminTitle : t.adminSettings.deleteOneTitle
          }}
        </h3>

        <div id="delete-modal-message" class="modal-text">
          <template v-if="deleteTarget.mode === 'admin'">
            <p>{{ fill(t.adminSettings.deleteAdminMessage, { name: deleteTarget.admin.name || deleteTarget.admin.email, email: deleteTarget.admin.email }) }}</p>
            <p class="modal-warning">{{ t.adminSettings.deleteAdminWarning }}</p>
          </template>

          <template v-else-if="deleteTarget.mode === 'one'">
            <p>{{ fill(t.adminSettings.deleteOneMessage, { name: fullName(deleteTarget.student), id: deleteTarget.student.student_id }) }}</p>
            <p
              v-if="deleteTarget.student.activity_count || deleteTarget.student.external_activity_count"
              class="modal-warning"
            >
              {{ fill(t.adminSettings.deleteRelatedWarning, { faculty: deleteTarget.student.activity_count, external: deleteTarget.student.external_activity_count }) }}
            </p>
          </template>

          <template v-else>
            <p>{{ isCentral ? fill(t.adminSettings.deleteAllMessage, { count: studentsAllTotal }) : fill(t.adminSettings.deleteAllMessageBranch, { count: studentsAllTotal, major: adminMajor }) }}</p>
            <p class="muted">{{ t.adminSettings.deleteAllKeepsActivities }}</p>
            <label class="confirm-field">
              <span>{{ fill(t.adminSettings.deleteAllConfirmLabel, { word: t.adminSettings.deleteConfirmWord }) }}</span>
              <input
                v-model="deleteConfirmText"
                type="text"
                autocomplete="off"
                spellcheck="false"
                :placeholder="t.adminSettings.deleteConfirmWord"
                data-testid="delete-all-confirm-input"
                @keydown.enter.prevent="confirmDelete"
              />
            </label>
          </template>

          <p class="cannot-undo">{{ t.adminSettings.cannotUndo }}</p>
        </div>

        <div v-if="deleteError" class="alert error" role="alert">
          <TriangleAlert :size="16" />
          <span>{{ deleteError }}</span>
        </div>

        <div class="modal-actions">
          <button
            ref="deleteCancelButton"
            type="button"
            class="secondary-button"
            :disabled="deleting"
            @click="closeDelete"
          >
            {{ t.adminSettings.cancelButton }}
          </button>
          <button
            type="button"
            class="danger-button"
            :disabled="deleting || (deleteTarget.mode === 'all' && !deleteAllReady)"
            data-testid="confirm-delete"
            @click="confirmDelete"
          >
            <LoaderCircle v-if="deleting" class="spin" :size="16" />
            {{
              deleting
                ? t.adminSettings.deleting
                : deleteTarget.mode === 'all' ? t.adminSettings.deleteAllButton : t.adminSettings.deleteButton
            }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  min-height: 100vh;
  padding: 32px;
  background: #f7f8fc;
  color: #1c293d;
}

/* หัวข้อทุกระดับในหน้านี้เป็นสีเข้ม (ไม่ใช้สีจาก style.css ที่เคยเปลี่ยนตาม dark mode ของเครื่อง) */
.settings-page h2,
.settings-page h3,
.settings-page h4 {
  color: #1c293d;
}

.page-header {
  max-width: 1100px;
  margin: 0 auto 24px;
}

.page-header h1 {
  margin: 0;
  color: #1d3268;
  font-size: 28px;
}

.page-header p {
  margin: 6px 0 0;
  color: #7b8ba3;
}

.card {
  max-width: 1100px;
  margin: 0 auto;
  padding: 26px 28px;
  border: 1px solid #e3e8f0;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(29, 50, 104, 0.04), 0 6px 20px rgba(29, 50, 104, 0.04);
}

/* แอดมินสาขา: บอกขอบเขตการนำเข้า */
.branch-scope-note {
  margin-top: 6px;
  color: #b45f06;
  font-weight: 500;
}

/* หัวการ์ด */
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.card-title {
  display: flex;
  gap: 14px;
  min-width: 0;
  flex: 1 1 320px;
}

.card-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  background: #eaf0ff;
  color: #2f5fdb;
}

.card-title h2 {
  margin: 0;
  color: #1c293d;
  font-size: 20px;
}

.card-title p {
  margin: 4px 0 0;
  color: #6b7a90;
  font-size: var(--fs-small);
}

.column-list {
  margin: 18px 0 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: var(--fs-small);
}

.column-list-label {
  color: #6b7a90;
}

.column-list code {
  padding: 3px 10px;
  border: 1px solid #dfe6f2;
  border-radius: 999px;
  background: #f6f8fc;
  color: #34445a;
  font-family: inherit;
  font-size: var(--fs-caption);
}

/* ปุ่ม */
.primary-button,
.secondary-button {
  min-height: 42px;
  padding: 0 18px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.primary-button {
  border: none;
  background: #2f5fdb;
  color: #fff;
  box-shadow: 0 6px 14px rgba(47, 95, 219, 0.22);
}

.primary-button:not(:disabled):hover {
  background: #244ec0;
}

.secondary-button {
  border: 1px solid #d6e0f0;
  background: #fff;
  color: #2f5fdb;
}

.secondary-button:not(:disabled):hover {
  background: #f3f7ff;
}

.primary-button:disabled,
.secondary-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
}

.alert {
  margin-top: 18px;
  padding: 11px 14px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--fs-small);
}

.alert.error {
  background: #fdeeee;
  color: #b42318;
}

/* dropzone */
.dropzone {
  margin-top: 20px;
  padding: 40px 24px;
  border: 2px dashed #c8d5ef;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  background: linear-gradient(180deg, #fafcff 0%, #f2f6ff 100%);
  text-align: center;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.dropzone:hover,
.dropzone:focus-visible {
  border-color: #7d9ce8;
  outline: none;
}

.dropzone.dragging {
  border-color: #2f5fdb;
  background: #eaf0ff;
}

.dropzone.busy {
  cursor: progress;
}

.file-input {
  display: none;
}

.dropzone-icon {
  width: 56px;
  height: 56px;
  margin-bottom: 4px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: #fff;
  color: #2f5fdb;
  box-shadow: 0 4px 12px rgba(47, 95, 219, 0.14);
}

.dropzone strong {
  font-size: var(--fs-body);
}

.dropzone p {
  margin: 0;
  color: #6b7a90;
  font-size: var(--fs-small);
}

.pill-button {
  margin-top: 6px;
  padding: 8px 20px;
  border: 1px solid #d6e0f0;
  border-radius: 999px;
  background: #fff;
  color: #2f5fdb;
  font-size: var(--fs-small);
  font-weight: 600;
}

/* พรีวิว */
.preview-header {
  margin-top: 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.file-chip {
  min-width: 0;
  padding: 8px 14px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #eef7f1;
  color: #15803d;
  font-weight: 600;
  font-size: var(--fs-small);
}

.file-chip span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.summary-chip {
  padding: 6px 12px;
  border-radius: 999px;
  background: #f1f4f9;
  color: #52617a;
  font-size: var(--fs-caption);
}

.summary-chip b {
  margin-left: 4px;
  color: #1c293d;
}

.summary-chip.new { background: #e8f7ee; color: #15803d; }
.summary-chip.duplicate { background: #fff5e0; color: #a15c00; }
.summary-chip.invalid { background: #fdeeee; color: #b42318; }
.summary-chip.new b,
.summary-chip.duplicate b,
.summary-chip.invalid b { color: inherit; }

.section-title {
  margin: 22px 0 4px;
  font-size: var(--fs-lead);
}

.section-hint {
  margin: 0 0 14px;
  color: #6b7a90;
  font-size: var(--fs-small);
}

.empty-state {
  padding: 24px;
  border-radius: 12px;
  background: #f7f8fc;
  color: #6b7a90;
  text-align: center;
}

.table-wrap {
  max-height: 440px;
  overflow: auto;
  border: 1px solid #e3e8f0;
  border-radius: 12px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-small);
}

th {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 11px 14px;
  background: #f6f8fc;
  color: #7b8ba3;
  font-size: var(--fs-caption);
  font-weight: 700;
  text-align: left;
  white-space: nowrap;
}

td {
  padding: 10px 14px;
  border-top: 1px solid #eef1f6;
  vertical-align: top;
}

tr.row-duplicate td { background: #fffbf2; }
tr.row-invalid td { background: #fff7f7; }

.mono {
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.02em;
}

.muted {
  color: #8a97ab;
}

.status-badge {
  padding: 3px 10px;
  border-radius: 999px;
  display: inline-block;
  font-size: var(--fs-badge);
  font-weight: 700;
  white-space: nowrap;
}

.status-badge.new { background: #e8f7ee; color: #15803d; }
.status-badge.duplicate { background: #fff1d6; color: #a15c00; }
.status-badge.invalid { background: #fde3e3; color: #b42318; }

.status-reason {
  margin-top: 4px;
  display: block;
  color: #8a5a00;
  font-size: var(--fs-caption);
}

tr.row-invalid .status-reason {
  color: #b42318;
}

.actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.no-new-rows {
  margin: 8px 0 0;
  color: #a15c00;
  font-size: var(--fs-small);
  text-align: right;
}

/* ผลลัพธ์ */
.result {
  margin-top: 22px;
}

.result-heading {
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #e8f7ee;
  color: #16a34a;
}

.result-heading h3 {
  margin: 0;
  font-size: 20px;
}

.result-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.result-stat {
  padding: 16px 18px;
  border: 1px solid #e3e8f0;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: #fafbfd;
}

.result-stat span {
  color: #6b7a90;
  font-size: var(--fs-small);
}

.result-stat strong {
  font-size: 28px;
  line-height: 1.2;
}

.result-stat.new strong { color: #15803d; }
.result-stat.duplicate strong { color: #a15c00; }
.result-stat.invalid strong { color: #b42318; }

.issues {
  margin-top: 20px;
}

.issues h4 {
  margin: 0 0 10px;
  font-size: var(--fs-body);
}

.issues ul {
  max-height: 280px;
  margin: 0;
  padding: 0;
  overflow: auto;
  list-style: none;
  border: 1px solid #e3e8f0;
  border-radius: 12px;
}

.issues li {
  padding: 10px 14px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 12px;
  font-size: var(--fs-small);
}

.issues li + li {
  border-top: 1px solid #eef1f6;
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* =========================
   นักศึกษาทั้งหมด
========================= */
.students-card {
  margin-top: 24px;
}

.search-box {
  margin-top: 18px;
  height: 44px;
  padding: 0 14px;
  border: 1px solid #dce5ef;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #8a97ab;
  background: #fff;
}

.search-box:focus-within {
  border-color: #7bb1f5;
  box-shadow: 0 0 0 3px rgba(47, 95, 219, 0.12);
}

.search-box input {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: none;
  background: transparent;
  color: #1c293d;
  font: inherit;
}

.students-card .empty-state,
.students-table {
  margin-top: 16px;
}

.students-table {
  max-height: 560px;
  transition: opacity 0.15s ease;
}

.students-table.loading {
  opacity: 0.55;
}

.actions-column {
  width: 1%;
  text-align: center;
}

.alert.success {
  background: #e8f7ee;
  color: #15803d;
}

.link-button {
  margin-left: auto;
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  font-weight: 700;
  text-decoration: underline;
  cursor: pointer;
}

.danger-outline-button,
.danger-button {
  min-height: 42px;
  padding: 0 18px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.danger-outline-button {
  border: 1px solid #f3c4c4;
  background: #fff;
  color: #c62828;
}

.danger-outline-button:not(:disabled):hover {
  background: #fff4f4;
}

.danger-button {
  border: none;
  background: #dc2626;
  color: #fff;
}

.danger-button:not(:disabled):hover {
  background: #b91c1c;
}

.danger-outline-button:disabled,
.danger-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon-danger-button {
  width: 34px;
  height: 34px;
  border: 1px solid #f1d4d4;
  border-radius: 9px;
  display: inline-grid;
  place-items: center;
  background: #fff;
  color: #c62828;
  cursor: pointer;
}

.icon-danger-button:hover {
  background: #fff1f1;
  border-color: #e9a9a9;
}

.pagination {
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  color: #52617a;
  font-size: var(--fs-small);
}

.secondary-button.square {
  width: 38px;
  min-height: 38px;
  padding: 0;
}

.view-all-row {
  margin-top: 14px;
  display: flex;
  justify-content: center;
}

.admins-table {
  margin-top: 16px;
}

.branch-chip {
  padding: 3px 10px;
  border-radius: 999px;
  display: inline-block;
  background: #eaf0ff;
  color: #2f5fdb;
  font-size: var(--fs-caption);
  font-weight: 600;
}

/* popup เพิ่มแอดมิน (.modal.form-modal: ชนะ .modal ที่ประกาศทีหลัง) */
.modal.form-modal {
  width: min(520px, 100%);
  align-items: stretch;
  text-align: left;
}

.form-modal-header {
  margin-bottom: 18px;
  display: flex;
  gap: 14px;
}

.form-modal-icon {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: #eaf0ff;
  color: #2f5fdb;
}

.form-modal-header h3 {
  margin: 0 0 2px;
  font-size: 20px;
}

.form-modal-header p {
  margin: 0;
  color: #6b7a90;
  font-size: var(--fs-small);
}

.form-grid {
  margin-bottom: 14px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.form-field {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: var(--fs-small);
  font-weight: 600;
}

.form-field.full {
  grid-column: 1 / -1;
}

.form-field b {
  color: #dc2626;
}

.form-field small {
  color: #8a97ab;
  font-weight: 400;
}

.form-field input,
.form-field select {
  height: 44px;
  padding: 0 12px;
  border: 1px solid #dce5ef;
  border-radius: 10px;
  background: #fff;
  color: #1c293d;
  font: inherit;
  font-weight: 400;
}

.form-field input:focus,
.form-field select:focus {
  outline: none;
  border-color: #7bb1f5;
  box-shadow: 0 0 0 3px rgba(47, 95, 219, 0.12);
}

.default-password-note {
  margin: 0 0 14px;
  padding: 10px 12px;
  border-radius: 10px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #eef4ff;
  color: #1e45c8;
  font-size: var(--fs-small);
}

.default-password-note svg {
  flex-shrink: 0;
  margin-top: 2px;
}

/* =========================
   เมนู accordion
========================= */
.settings-menu {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.settings-panel {
  border: 1px solid #e3e8f0;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(29, 50, 104, 0.04), 0 6px 20px rgba(29, 50, 104, 0.04);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.settings-panel.open {
  border-color: #c9d6ee;
  box-shadow: 0 1px 2px rgba(29, 50, 104, 0.05), 0 10px 28px rgba(47, 95, 219, 0.08);
}

.panel-header {
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.panel-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: #eaf0ff;
  color: #2f5fdb;
}

.panel-icon.admins {
  background: #ecf8f1;
  color: #15803d;
}

.panel-icon.transcript {
  background: #f4ecff;
  color: #7e10c6;
}

.panel-text {
  flex: 1;
  min-width: 0;
}

.panel-text h2 {
  margin: 0;
  color: #1c293d;
  font-size: 19px;
  font-weight: 700;
}

.panel-text p {
  margin: 3px 0 0;
  color: #6b7a90;
  font-size: var(--fs-small);
}

.panel-meta {
  flex-shrink: 0;
  padding: 5px 12px;
  border-radius: 999px;
  background: #f1f4f9;
  color: #52617a;
  font-size: var(--fs-caption);
  font-weight: 600;
  white-space: nowrap;
}

.panel-toggle {
  flex-shrink: 0;
  min-height: 40px;
  padding: 0 14px 0 18px;
  border: 1.5px solid #c9d6ee;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #fff;
  color: #2f5fdb;
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 600;
  cursor: pointer;
}

.panel-toggle:hover {
  background: #f3f7ff;
}

.panel-toggle .chevron {
  transition: transform 0.2s ease;
}

.settings-panel.open .panel-toggle {
  border-color: #2f5fdb;
  background: #2f5fdb;
  color: #fff;
}

.settings-panel.open .panel-toggle .chevron {
  transform: rotate(180deg);
}

.panel-body {
  padding: 4px 24px 24px;
  border-top: 1px solid #eef1f6;
  display: flex;
  flex-direction: column;
  gap: 18px;
  background: #fafbfd;
  border-radius: 0 0 16px 16px;
}

/* การ์ดเดิมที่อยู่ในแผง: ไม่ต้องจำกัดความกว้าง/จัดกลางซ้ำ */
.panel-body > .card {
  max-width: none;
  margin: 18px 0 0;
}

.panel-body > .card + .card {
  margin-top: 0;
}

/* ฟอร์มหัวเอกสาร Transcript */
.transcript-grid {
  margin-top: 20px;
  display: grid;
  grid-template-columns: minmax(160px, 0.8fr) minmax(0, 1.6fr) minmax(0, 1.6fr);
  align-items: center;
  gap: 12px 14px;
}

.grid-head {
  color: #7b8ba3;
  font-size: var(--fs-caption);
  font-weight: 700;
  letter-spacing: 0.04em;
}

.field-label {
  color: #1c293d;
  font-size: var(--fs-small);
  font-weight: 600;
}

.transcript-grid input {
  height: 44px;
  padding: 0 12px;
  border: 1px solid #dce5ef;
  border-radius: 10px;
  background: #fff;
  color: #1c293d;
  font: inherit;
}

.transcript-grid input::placeholder {
  color: #a3aebf;
}

.transcript-grid input:focus {
  outline: none;
  border-color: #7bb1f5;
  box-shadow: 0 0 0 3px rgba(47, 95, 219, 0.12);
}

.transcript-hint {
  margin: 16px 0 0;
  padding: 10px 12px;
  border-radius: 10px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #eef4ff;
  color: #1e45c8;
  font-size: var(--fs-small);
}

.transcript-hint svg {
  flex-shrink: 0;
  margin-top: 2px;
}

/* ตัวอย่าง Transcript */
.preview-toolbar {
  margin-top: 18px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 18px;
}

.segmented {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.segmented-label {
  margin-right: 6px;
  color: #5b6b82;
  font-size: var(--fs-small);
  font-weight: 600;
}

.segmented button {
  height: 36px;
  padding: 0 14px;
  border: 1px solid #dce5ef;
  border-radius: 9px;
  background: #fff;
  color: #42526b;
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 600;
  cursor: pointer;
}

.segmented button.active {
  border-color: #2f5fdb;
  background: #eef4ff;
  color: #1e45c8;
}

.refresh-preview {
  margin-left: auto;
}

.preview-card .alert {
  margin-top: 14px;
}

.preview-frame {
  position: relative;
  margin-top: 16px;
  height: 900px;
  border: 1px solid #dce5ef;
  border-radius: 12px;
  overflow: hidden;
  background: #eef1f6;
}

.preview-frame iframe {
  width: 100%;
  height: 100%;
  border: 0;
  display: block;
}

.preview-frame.loading iframe {
  opacity: 0.45;
}

.preview-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #42526b;
  font-size: var(--fs-small);
  font-weight: 600;
}

/* popup ยืนยันการลบ */
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  padding: 20px;
  display: grid;
  place-items: center;
  background: rgba(28, 41, 61, 0.45);
}

.modal {
  width: min(460px, 100%);
  padding: 30px 28px 24px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #fff;
  box-shadow: 0 24px 60px rgba(28, 41, 61, 0.25);
  text-align: center;
}

.modal-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 14px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #fdecec;
  color: #dc2626;
}

.modal h3 {
  margin: 0 0 10px;
  font-size: 20px;
}

.modal-text {
  width: 100%;
  color: #52617a;
  font-size: var(--fs-body);
  line-height: 1.6;
  overflow-wrap: anywhere;
}

.modal-text p {
  margin: 0 0 10px;
}

.modal-warning {
  padding: 10px 12px;
  border-radius: 10px;
  background: #fff5e0;
  color: #8a5a00;
  font-size: var(--fs-small);
  text-align: left;
}

.cannot-undo {
  color: #c62828;
  font-size: var(--fs-small);
  font-weight: 600;
}

.confirm-field {
  margin: 6px 0 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: left;
  font-size: var(--fs-small);
}

.confirm-field input {
  height: 44px;
  padding: 0 12px;
  border: 1px solid #dce5ef;
  border-radius: 10px;
  font: inherit;
  letter-spacing: 0.08em;
}

.confirm-field input:focus {
  outline: none;
  border-color: #e9a9a9;
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.12);
}

.modal .alert {
  width: 100%;
  margin: 0 0 12px;
  box-sizing: border-box;
}

.modal-actions {
  width: 100%;
  margin-top: 6px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.modal-actions button {
  min-height: 46px;
}

@media (max-width: 700px) {
  .settings-page {
    padding: 20px 16px;
  }

  .card {
    padding: 20px 16px;
  }

  .result-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .actions > button,
  .card-header .secondary-button,
  .card-header .primary-button,
  .card-header .danger-outline-button {
    width: 100%;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .panel-header {
    padding: 16px;
    flex-wrap: wrap;
  }

  .panel-meta {
    order: 3;
  }

  .panel-toggle {
    order: 4;
    margin-left: auto;
  }

  .panel-body {
    padding: 4px 12px 16px;
  }

  .transcript-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .grid-head {
    display: none;
  }

  .refresh-preview {
    margin-left: 0;
  }

  .preview-frame {
    height: 600px;
  }

  .field-label {
    margin-top: 10px;
  }
}
</style>
