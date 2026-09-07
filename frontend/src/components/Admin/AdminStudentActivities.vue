<script setup>
import { computed, ref } from 'vue'
import {
  Upload,
  Search,
  FileSpreadsheet,
  Users,
  CircleCheck,
  TriangleAlert,
  X,
  LoaderCircle
} from 'lucide-vue-next'

const API_BASE = 'http://localhost:8000'

const search = ref('')
const selectedFile = ref(null)
const previewRows = ref([])
const totalRows = ref(0)
const columns = ref([])
const errorMessage = ref('')
const loading = ref(false)
const showImportModal = ref(false)

const filteredRows = computed(() => {
  const keyword = search.value.trim().toLowerCase()

  if (!keyword) return previewRows.value

  return previewRows.value.filter((student) => {
    return Object.values(student).some((value) =>
      String(value ?? '').toLowerCase().includes(keyword)
    )
  })
})

function openImportModal() {
  errorMessage.value = ''
  showImportModal.value = true
}

function closeImportModal() {
  if (loading.value) return
  showImportModal.value = false
}

function handleFile(event) {
  const file = event.target.files?.[0] ?? null
  selectedFile.value = file
  errorMessage.value = ''
}

async function previewImport() {
  if (!selectedFile.value) {
    errorMessage.value = 'กรุณาเลือกไฟล์ CSV หรือ Excel ก่อน'
    return
  }

  loading.value = true
  errorMessage.value = ''

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const response = await fetch(`${API_BASE}/api/students/import/preview`, {
      method: 'POST',
      body: formData
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'ไม่สามารถอ่านไฟล์ได้')
    }

    previewRows.value = data.students
    totalRows.value = data.total
    columns.value = data.columns
    showImportModal.value = false
  } catch (error) {
    errorMessage.value = error.message || 'เกิดข้อผิดพลาดในการเชื่อมต่อ Backend'
  } finally {
    loading.value = false
  }
}

function clearPreview() {
  previewRows.value = []
  totalRows.value = 0
  columns.value = []
  selectedFile.value = null
}
</script>

<template>
  <section class="student-activities-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">ACTIVITY MANAGEMENT</p>
        <h1>Student Activities</h1>
        <p class="subtitle">
          จัดการรายชื่อนักศึกษาที่ลงทะเบียนเข้าร่วมกิจกรรม
        </p>
      </div>

      <button class="primary-button" @click="openImportModal">
        <Upload :size="18" />
        Import Students
      </button>
    </header>

    <div class="summary-grid">
      <article class="summary-card">
        <div class="summary-icon">
          <Users :size="21" />
        </div>
        <div>
          <span>IMPORTED STUDENTS</span>
          <strong>{{ totalRows }}</strong>
        </div>
      </article>

      <article class="summary-card">
        <div class="summary-icon">
          <CircleCheck :size="21" />
        </div>
        <div>
          <span>READY TO IMPORT</span>
          <strong>{{ previewRows.length }}</strong>
        </div>
      </article>

      <article class="summary-card">
        <div class="summary-icon">
          <TriangleAlert :size="21" />
        </div>
        <div>
          <span>VALIDATION ISSUES</span>
          <strong>0</strong>
        </div>
      </article>
    </div>

    <div class="toolbar-card">
      <div class="search-box">
        <Search :size="17" />
        <input
          v-model="search"
          type="text"
          placeholder="Search student ID, name or email..."
        />
      </div>

      <div class="toolbar-actions">
        <span v-if="selectedFile" class="file-name">
          {{ selectedFile.name }}
        </span>

        <button
          v-if="previewRows.length"
          class="secondary-button"
          @click="clearPreview"
        >
          Clear preview
        </button>
      </div>
    </div>

    <div class="table-card">
      <div class="table-heading">
        <div>
          <h2>Student List</h2>
          <p>Preview ข้อมูลจากไฟล์ก่อนบันทึกลงฐานข้อมูลจริง</p>
        </div>
      </div>

      <div v-if="!previewRows.length" class="empty-state">
        <div class="empty-icon">
          <FileSpreadsheet :size="31" />
        </div>

        <h3>No student data yet</h3>
        <p>
          กด Import Students แล้วเลือกไฟล์ที่ export จาก Google Forms
          เพื่อทดลองอ่านข้อมูล
        </p>

        <button class="empty-import-button" @click="openImportModal">
          <Upload :size="17" />
          Choose file
        </button>
      </div>

      <div v-else class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Student ID</th>
              <th>First name</th>
              <th>Last name</th>
              <th>CMU Email</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="(student, index) in filteredRows"
              :key="student.student_id || index"
            >
              <td class="student-id">{{ student.student_id || '-' }}</td>
              <td>{{ student.first_name || '-' }}</td>
              <td>{{ student.last_name || '-' }}</td>
              <td>{{ student.email || '-' }}</td>
              <td>
                <span class="status-badge">Ready</span>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="!filteredRows.length" class="no-results">
          ไม่พบข้อมูลที่ตรงกับการค้นหา
        </div>
      </div>
    </div>

    <div
      v-if="showImportModal"
      class="modal-backdrop"
      @click.self="closeImportModal"
    >
      <div class="modal">
        <div class="modal-header">
          <div>
            <p class="eyebrow">IMPORT PARTICIPANTS</p>
            <h2>Import Student List</h2>
          </div>

          <button class="icon-button" @click="closeImportModal">
            <X :size="20" />
          </button>
        </div>

        <label class="dropzone">
          <FileSpreadsheet :size="34" />
          <strong>
            {{ selectedFile ? selectedFile.name : 'Select CSV or Excel file' }}
          </strong>
          <span>
            รองรับ .csv, .xlsx และ .xls
          </span>

          <input
            type="file"
            accept=".csv,.xlsx,.xls"
            hidden
            @change="handleFile"
          />
        </label>

        <div v-if="errorMessage" class="error-box">
          <TriangleAlert :size="17" />
          {{ errorMessage }}
        </div>

        <div class="modal-actions">
          <button
            class="secondary-button"
            :disabled="loading"
            @click="closeImportModal"
          >
            Cancel
          </button>

          <button
            class="primary-button"
            :disabled="loading"
            @click="previewImport"
          >
            <LoaderCircle
              v-if="loading"
              class="spin"
              :size="18"
            />
            <Upload v-else :size="18" />

            {{ loading ? 'Reading file...' : 'Preview Import' }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.student-activities-page {
  min-height: 100vh;
  padding: 34px 38px 48px;
  background: #f7f8fc;
  color: #172033;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 28px;
}

.eyebrow {
  margin: 0 0 7px;
  color: #8ea0bb;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.09em;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  line-height: 1.2;
}

.subtitle {
  margin: 7px 0 0;
  color: #77859a;
  font-size: 14px;
}

.primary-button,
.secondary-button,
.empty-import-button,
.icon-button {
  border: 0;
  font-family: inherit;
  cursor: pointer;
}

.primary-button {
  min-height: 42px;
  padding: 0 18px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  background: #8613bd;
  color: white;
  font-weight: 700;
  box-shadow: 0 5px 14px rgba(134, 19, 189, 0.18);
}

.primary-button:disabled,
.secondary-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 22px;
}

.summary-card {
  min-height: 92px;
  padding: 18px;
  border: 1px solid #e9edf4;
  border-radius: 14px;
  background: white;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.02);
}

.summary-icon {
  width: 43px;
  height: 43px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  background: #eef5ff;
  color: #2671e8;
}

.summary-card span {
  display: block;
  margin-bottom: 4px;
  color: #91a0b7;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.summary-card strong {
  font-size: 24px;
}

.toolbar-card,
.table-card {
  border: 1px solid #e8edf4;
  background: white;
  border-radius: 14px;
}

.toolbar-card {
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.search-box {
  width: min(380px, 100%);
  height: 40px;
  padding: 0 13px;
  border: 1px solid #dfe6f0;
  border-radius: 9px;
  display: flex;
  align-items: center;
  gap: 9px;
  color: #93a4bb;
  background: #fbfcfe;
}

.search-box input {
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: #334155;
  font: inherit;
  font-size: 13px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-name {
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #718096;
  font-size: 12px;
}

.secondary-button {
  min-height: 38px;
  padding: 0 14px;
  border: 1px solid #dfe6f0;
  border-radius: 9px;
  background: white;
  color: #52617a;
  font-weight: 600;
}

.table-card {
  overflow: hidden;
  min-height: 430px;
}

.table-heading {
  padding: 20px 22px;
  border-bottom: 1px solid #edf1f6;
}

.table-heading h2 {
  margin: 0;
  font-size: 16px;
}

.table-heading p {
  margin: 5px 0 0;
  color: #8a98ad;
  font-size: 12px;
}

.empty-state {
  min-height: 330px;
  padding: 35px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-icon {
  width: 68px;
  height: 68px;
  margin-bottom: 17px;
  border-radius: 17px;
  display: grid;
  place-items: center;
  background: #eef5ff;
  color: #2671e8;
}

.empty-state h3 {
  margin: 0;
  font-size: 17px;
}

.empty-state p {
  max-width: 430px;
  margin: 9px 0 20px;
  color: #8896aa;
  font-size: 13px;
  line-height: 1.7;
}

.empty-import-button {
  min-height: 39px;
  padding: 0 15px;
  border-radius: 9px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #edf4ff;
  color: #2168d8;
  font-weight: 700;
}

.table-wrapper {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 15px 20px;
  border-bottom: 1px solid #edf1f6;
  text-align: left;
  font-size: 13px;
}

th {
  background: #fafbfd;
  color: #8a9bb4;
  font-size: 10px;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

td {
  color: #4b5b73;
}

.student-id {
  font-weight: 700;
  color: #25334a;
}

.status-badge {
  padding: 5px 9px;
  border-radius: 999px;
  background: #ebf8f1;
  color: #21875a;
  font-size: 11px;
  font-weight: 700;
}

.no-results {
  padding: 30px;
  text-align: center;
  color: #8796ab;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1200;
  padding: 20px;
  display: grid;
  place-items: center;
  background: rgba(15, 23, 42, 0.33);
}

.modal {
  width: min(520px, 100%);
  padding: 22px;
  border-radius: 16px;
  background: white;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.18);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
}

.icon-button {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: #f4f6f9;
  color: #66758b;
}

.dropzone {
  min-height: 180px;
  padding: 25px;
  border: 1.5px dashed #ccd7e6;
  border-radius: 13px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 9px;
  background: #fafcff;
  color: #60718a;
  cursor: pointer;
}

.dropzone svg {
  color: #2873e7;
}

.dropzone strong {
  color: #344259;
  font-size: 14px;
}

.dropzone span {
  color: #94a2b6;
  font-size: 12px;
}

.error-box {
  margin-top: 14px;
  padding: 11px 13px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff2f2;
  color: #bb3b3b;
  font-size: 12px;
}

.modal-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 800px) {
  .student-activities-page {
    padding: 24px 18px 40px;
  }

  .page-header,
  .toolbar-card {
    flex-direction: column;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .toolbar-actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>