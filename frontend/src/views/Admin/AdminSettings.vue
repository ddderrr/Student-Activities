<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Download,
  FileSpreadsheet,
  LoaderCircle,
  RotateCcw,
  Search,
  ShieldAlert,
  Trash2,
  TriangleAlert,
  Upload,
  Users,
  X
} from 'lucide-vue-next'

import { useLanguage } from '../../composables/useLanguage'
import { adminFetch, getAdminSession } from '../../constants/currentAdmin'
import { API_BASE } from '../../constants/currentStudent'

const { t, currentLanguage } = useLanguage()

// หน้า Settings ใช้ได้เฉพาะแอดมินกลาง (backend ตรวจซ้ำด้วย require_central_admin)
const isCentral = computed(() => Boolean(getAdminSession()?.is_central))

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

const PAGE_SIZE = 20

const students = ref([])
const studentsTotal = ref(0)
const studentsAllTotal = ref(0)
const studentsPage = ref(1)
const studentsLoading = ref(false)
const studentsError = ref('')
const studentSearch = ref('')
const notice = ref('')

const studentsPages = computed(() => Math.max(1, Math.ceil(studentsTotal.value / PAGE_SIZE)))

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

  const params = new URLSearchParams({ page: studentsPage.value, page_size: PAGE_SIZE })
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
      studentsPage.value = Math.max(1, Math.ceil(data.total / PAGE_SIZE))
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

function goToStudentsPage(page) {
  if (page < 1 || page > studentsPages.value || page === studentsPage.value) return
  studentsPage.value = page
  loadStudents()
}

// ---- ลบ: { mode: 'one', student } | { mode: 'all' }
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

  const url = target.mode === 'all'
    ? `${API_BASE}/api/admin/students?confirm=all`
    : `${API_BASE}/api/admin/students/${encodeURIComponent(target.student.student_id)}`

  try {
    const response = await adminFetch(url, { method: 'DELETE' })
    const data = await response.json().catch(() => null)
    if (!response.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : '')

    notice.value = target.mode === 'all'
      ? fill(t.value.adminSettings.deletedAll, { count: data.students })
      : fill(t.value.adminSettings.deletedOne, { name: fullName(target.student) })
    deleting.value = false
    deleteTarget.value = null
    if (target.mode === 'all') studentsPage.value = 1
    loadStudents()
  } catch (error) {
    deleteError.value = error.message || t.value.adminSettings.deleteFailed
  } finally {
    deleting.value = false
  }
}

function onKeydown(event) {
  if (event.key === 'Escape' && deleteTarget.value) closeDelete()
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  if (isCentral.value) loadStudents()
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  clearTimeout(searchTimer)
})
</script>

<template>
  <div class="settings-page">
    <header class="page-header">
      <h1>{{ t.adminSettings.title }}</h1>
      <p v-if="isCentral">{{ t.adminSettings.subtitle }}</p>
    </header>

    <!-- แอดมินสาขา -->
    <section v-if="!isCentral" class="card no-permission" data-testid="settings-no-permission">
      <span class="no-permission-icon"><ShieldAlert :size="28" /></span>
      <h2>{{ t.adminSettings.noPermissionTitle }}</h2>
      <p>{{ t.adminSettings.noPermissionText }}</p>
    </section>

    <!-- แอดมินกลาง: นำเข้าข้อมูลนักศึกษา -->
    <template v-else>
    <section class="card import-card" data-testid="student-import">
      <div class="card-header">
        <div class="card-title">
          <span class="card-icon"><Users :size="18" /></span>
          <div>
            <h2>{{ t.adminSettings.importTitle }}</h2>
            <p>{{ t.adminSettings.importDescription }}</p>
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
              {{ t.adminSettings.studentsDescription }} ·
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

      <div v-if="studentsTotal > PAGE_SIZE" class="pagination">
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
    </template>

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
          {{ deleteTarget.mode === 'all' ? t.adminSettings.deleteAllTitle : t.adminSettings.deleteOneTitle }}
        </h3>

        <div id="delete-modal-message" class="modal-text">
          <template v-if="deleteTarget.mode === 'one'">
            <p>{{ fill(t.adminSettings.deleteOneMessage, { name: fullName(deleteTarget.student), id: deleteTarget.student.student_id }) }}</p>
            <p
              v-if="deleteTarget.student.activity_count || deleteTarget.student.external_activity_count"
              class="modal-warning"
            >
              {{ fill(t.adminSettings.deleteRelatedWarning, { faculty: deleteTarget.student.activity_count, external: deleteTarget.student.external_activity_count }) }}
            </p>
          </template>

          <template v-else>
            <p>{{ fill(t.adminSettings.deleteAllMessage, { count: studentsAllTotal }) }}</p>
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

/* ไม่มีสิทธิ์ */
.no-permission {
  max-width: 560px;
  padding: 40px 28px;
  text-align: center;
}

.no-permission-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #fdf0e6;
  color: #c2410c;
}

.no-permission h2 {
  margin: 0 0 8px;
  font-size: 20px;
}

.no-permission p {
  margin: 0;
  color: #6b7a90;
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
  .card-header .secondary-button {
    width: 100%;
  }
}
</style>
