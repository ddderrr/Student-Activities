<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  Pencil,
  Save,
  X,
  Users,
  ShieldCheck
} from 'lucide-vue-next'

const API_BASE = 'http://127.0.0.1:8000'

const route = useRoute()
const router = useRouter()

const activityId = computed(() => Number(route.params.activityId || 1))

const roleOptions = [
  { value: 'participant', label: 'Participant' },
  { value: 'organizer', label: 'Organizer' }
]

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

const activity = ref({
  id: activityId.value,
  uid: '',
  name: '',
  activity_type: '',
  start_at: null,
  end_at: null,
  department: '',
  responsible_person: '',
  advisor: '',
  location: '',
  description: ''
})

const participants = ref([])
const pageLoading = ref(true)
const loadError = ref('')

const editingRowId = ref(null)
const editDraft = ref(null)
const savingRowId = ref(null)
const saveMessage = ref('')

const descriptionModalOpen = ref(false)
const descriptionTextRef = ref(null)
const descriptionIsOverflowing = ref(false)

// รวมค่า major ที่บันทึกไว้ (เช่นจากไฟล์ import) ที่ไม่อยู่ใน list ด้วย
// เพื่อให้ dropdown แสดงค่าปัจจุบันได้
const editMajorOptions = computed(() => {
  const saved = participants.value.find(
    (student) => student.student_id === editingRowId.value
  )?.major

  if (!saved || majorOptions.includes(saved)) return majorOptions

  return [saved, ...majorOptions]
})

const memberCount = computed(() => participants.value.length)
const participantCount = computed(
  () => participants.value.filter((student) => student.role === 'participant').length
)
const organizerCount = computed(
  () => participants.value.filter((student) => student.role === 'organizer').length
)

function formatActivityDate(value) {
  if (!value) return '—'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'

  return date.toLocaleDateString('th-TH', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}

function checkDescriptionOverflow() {
  nextTick(() => {
    const element = descriptionTextRef.value
    descriptionIsOverflowing.value = Boolean(
      element && element.scrollHeight > element.clientHeight + 1
    )
  })
}

function openDescriptionModal() {
  descriptionModalOpen.value = true
}

function closeDescriptionModal() {
  descriptionModalOpen.value = false
}

function handleModalEscape(event) {
  if (event.key === 'Escape' && descriptionModalOpen.value) {
    closeDescriptionModal()
  }
}

const activityDateRange = computed(() => {
  const start = formatActivityDate(activity.value.start_at)
  const end = formatActivityDate(activity.value.end_at)

  if (start === '—' && end === '—') return '—'
  if (start === end) return start

  return `${start} – ${end}`
})

async function fetchParticipants() {
  pageLoading.value = true
  loadError.value = ''

  try {
    const [participantsResponse, activityResponse] = await Promise.all([
      fetch(`${API_BASE}/api/activities/${activityId.value}/participants`),
      fetch(`${API_BASE}/api/activities/${activityId.value}`)
    ])

    if (!participantsResponse.ok || !activityResponse.ok) {
      throw new Error('โหลดข้อมูลไม่สำเร็จ')
    }

    const [participantsData, activityData] = await Promise.all([
      participantsResponse.json(),
      activityResponse.json()
    ])

    activity.value = activityData
    participants.value = participantsData.students
    checkDescriptionOverflow()
  } catch (error) {
    loadError.value = error.message || 'โหลดข้อมูลไม่สำเร็จ'
  } finally {
    pageLoading.value = false
  }
}

onMounted(() => {
  fetchParticipants()
  window.addEventListener('resize', checkDescriptionOverflow)
  window.addEventListener('keydown', handleModalEscape)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkDescriptionOverflow)
  window.removeEventListener('keydown', handleModalEscape)
})

function goBack() {
  router.push('/admin/activities')
}

function startEdit(student) {
  editingRowId.value = student.student_id
  editDraft.value = { ...student }
  saveMessage.value = ''
}

function cancelEdit() {
  editingRowId.value = null
  editDraft.value = null
  saveMessage.value = ''
}

function validateDraft() {
  if (!editDraft.value) return false

  return Boolean(
    editDraft.value.student_id.trim() &&
    editDraft.value.first_name.trim() &&
    editDraft.value.last_name.trim() &&
    editDraft.value.faculty.trim() &&
    editDraft.value.major &&
    editDraft.value.role
  )
}

async function saveRow() {
  if (!validateDraft()) {
    saveMessage.value = 'กรุณากรอกข้อมูลให้ครบ'
    return
  }

  const rowId = editingRowId.value
  savingRowId.value = rowId
  saveMessage.value = ''

  try {
    const response = await fetch(
      `${API_BASE}/api/activities/${activityId.value}/participants/${rowId}`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          first_name: editDraft.value.first_name,
          last_name: editDraft.value.last_name,
          email: editDraft.value.email,
          faculty: editDraft.value.faculty,
          major: editDraft.value.major,
          role: editDraft.value.role
        })
      }
    )

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null)
      throw new Error(errorBody?.detail || 'บันทึกข้อมูลไม่สำเร็จ')
    }

    const updated = await response.json()

    const index = participants.value.findIndex(
      (student) => student.student_id === rowId
    )

    if (index !== -1) {
      participants.value[index] = updated
    }

    editingRowId.value = null
    editDraft.value = null
  } catch (error) {
    saveMessage.value = error.message || 'ไม่สามารถบันทึกข้อมูลได้'
  } finally {
    savingRowId.value = null
  }
}

function roleLabel(role) {
  return role === 'organizer' ? 'Organizer' : 'Participant'
}
</script>

<template>
  <section class="details-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">ACTIVITY MANAGEMENT</p>
        <h1>Participant Details</h1>
        <p class="subtitle">
          ตรวจสอบและแก้ไขข้อมูลผู้เข้าร่วมกิจกรรม
        </p>
      </div>

      <button class="back-button" @click="goBack">
        <ArrowLeft :size="17" />
        Back to Activities
      </button>
    </header>

    <section class="activity-summary">
      <div class="summary-item activity-info">
        <span>ACTIVITY</span>
        <strong>{{ activity.name }}</strong>
        <small>{{ activity.uid }}</small>
      </div>

      <div class="summary-divider"></div>

      <div class="summary-item">
        <span>PARTICIPANTS</span>
        <strong class="summary-number">{{ participantCount }}</strong>
      </div>

      <div class="summary-divider"></div>

      <div class="summary-item">
        <span>ORGANIZERS</span>
        <div class="summary-with-icon">
          <ShieldCheck :size="17" />
          <strong class="summary-number">{{ organizerCount }}</strong>
        </div>
      </div>

      <div class="summary-divider"></div>

      <div class="summary-item">
        <span>TOTAL MEMBERS</span>
        <div class="summary-with-icon">
          <Users :size="17" />
          <strong class="summary-number">{{ memberCount }}</strong>
        </div>
      </div>

      <div class="summary-divider detail-divider"></div>

      <div class="activity-detail-panel">
        <span class="detail-heading">ACTIVITY DETAILS</span>

        <div class="activity-detail-grid">
          <div class="activity-detail-item">
            <small>TYPE</small>
            <strong>{{ activity.activity_type || '—' }}</strong>
          </div>

          <div class="activity-detail-item">
            <small>DATE</small>
            <strong>{{ activityDateRange }}</strong>
          </div>

          <div class="activity-detail-item">
            <small>LOCATION</small>
            <strong>{{ activity.location || '—' }}</strong>
          </div>

          <div class="activity-detail-item">
            <small>RESPONSIBLE</small>
            <strong>{{ activity.responsible_person || '—' }}</strong>
          </div>

          <div class="activity-detail-item activity-description">
            <small>DESCRIPTION</small>
            <strong ref="descriptionTextRef">
              {{ activity.description || 'ไม่มีรายละเอียดเพิ่มเติม' }}
            </strong>
            <button
              v-if="activity.description && descriptionIsOverflowing"
              class="read-more-button"
              type="button"
              @click="openDescriptionModal"
            >
              อ่านเพิ่มเติม
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="table-card">
      <div class="table-heading">
        <div>
          <h2>Students in Activity</h2>
          <p>
            กด Edit เพื่อแก้ไขข้อมูลทั้งแถวได้พร้อมกัน
          </p>
        </div>

        <span class="row-count">
          {{ memberCount }} students
        </span>
      </div>

      <p v-if="pageLoading" class="load-status">กำลังโหลดข้อมูล...</p>
      <p v-else-if="loadError" class="load-status load-status-error">{{ loadError }}</p>

      <div v-else class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>STUDENT ID</th>
              <th>STUDENT NAME</th>
              <th>FACULTY</th>
              <th>MAJOR</th>
              <th>ROLE</th>
              <th>ACTIONS</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="student in participants"
              :key="student.student_id"
              :class="{ editing: editingRowId === student.student_id }"
            >
              <!-- EDIT MODE -->
              <template v-if="editingRowId === student.student_id && editDraft">
                <td>
                  <input
                    v-model="editDraft.student_id"
                    class="row-input student-id-input"
                    type="text"
                    disabled
                  />
                </td>

                <td>
                  <div class="name-inputs">
                    <input
                      v-model="editDraft.first_name"
                      class="row-input"
                      type="text"
                      placeholder="First name"
                    />

                    <input
                      v-model="editDraft.last_name"
                      class="row-input"
                      type="text"
                      placeholder="Last name"
                    />
                  </div>
                </td>

                <td>
                  <input
                    v-model="editDraft.faculty"
                    class="row-input"
                    type="text"
                  />
                </td>

                <td>
                  <select
                    v-model="editDraft.major"
                    class="row-select"
                  >
                    <option
                      v-for="major in editMajorOptions"
                      :key="major"
                      :value="major"
                    >
                      {{ major }}
                    </option>
                  </select>
                </td>

                <td>
                  <select
                    v-model="editDraft.role"
                    class="row-select role-select"
                  >
                    <option
                      v-for="role in roleOptions"
                      :key="role.value"
                      :value="role.value"
                    >
                      {{ role.label }}
                    </option>
                  </select>
                </td>

                <td>
                  <div class="edit-actions">
                    <button
                      class="save-button"
                      :disabled="savingRowId === student.student_id"
                      @click="saveRow"
                    >
                      <span
                        v-if="savingRowId === student.student_id"
                        class="mini-spinner"
                      ></span>

                      <Save v-else :size="14" />

                      {{ savingRowId === student.student_id ? 'Saving' : 'Save' }}
                    </button>

                    <button
                      class="cancel-button"
                      :disabled="savingRowId === student.student_id"
                      @click="cancelEdit"
                    >
                      <X :size="14" />
                    </button>
                  </div>
                </td>
              </template>

              <!-- VIEW MODE -->
              <template v-else>
                <td class="student-id">
                  {{ student.student_id }}
                </td>

                <td class="student-name">
                  {{ student.first_name }} {{ student.last_name }}
                </td>

                <td>{{ student.faculty }}</td>

                <td>{{ student.major }}</td>

                <td>
                  <span
                    class="role-badge"
                    :class="student.role"
                  >
                    {{ roleLabel(student.role) }}
                  </span>
                </td>

                <td>
                  <button
                    class="edit-button"
                    :disabled="editingRowId !== null"
                    @click="startEdit(student)"
                  >
                    <Pencil :size="14" />
                    Edit
                  </button>
                </td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="saveMessage" class="save-error">
        {{ saveMessage }}
      </div>
    </section>

    <div
      v-if="descriptionModalOpen"
      class="description-modal-overlay"
      @click.self="closeDescriptionModal"
    >
      <div class="description-modal" role="dialog" aria-modal="true" aria-label="รายละเอียดกิจกรรม">
        <div class="description-modal-header">
          <div>
            <span>ACTIVITY DESCRIPTION</span>
            <h3>รายละเอียดกิจกรรม</h3>
          </div>

          <button
            class="description-modal-close"
            type="button"
            aria-label="ปิด"
            @click="closeDescriptionModal"
          >
            <X :size="18" />
          </button>
        </div>

        <div class="description-modal-body">
          {{ activity.description || 'ไม่มีรายละเอียดเพิ่มเติม' }}
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.details-page {
  min-height: 100vh;
  padding: 32px 34px 48px;
  background: #f7f8fc;
  color: #1c293d;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 24px;
}

.eyebrow {
  margin: 0 0 6px;
  color: #8ea0ba;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
}

.subtitle {
  margin: 7px 0 0;
  color: #8291a6;
  font-size: 13px;
}

.back-button {
  min-height: 40px;
  padding: 0 16px;
  border: 0;
  border-radius: 999px;
  background: #1465db;
  color: #fff;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-family: inherit;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.activity-summary {
  min-height: 94px;
  margin-bottom: 20px;
  padding: 18px 20px;
  border: 1px solid #e0e7f0;
  border-radius: 13px;
  background: #fff;
  display: flex;
  align-items: center;
  gap: 20px;
  overflow: hidden;
}

.summary-item {
  min-width: 120px;
}

.summary-item.activity-info {
  min-width: 250px;
}

.summary-item span {
  display: block;
  margin-bottom: 5px;
  color: #7f8fa5;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.07em;
}

.summary-item strong {
  color: #233248;
  font-size: 15px;
}

.summary-item small {
  display: block;
  margin-top: 3px;
  color: #9aa9bc;
  font-size: 9px;
}

.summary-number {
  font-size: 20px !important;
}

.summary-with-icon {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #246ad7;
}

.summary-divider {
  width: 1px;
  height: 42px;
  background: #e4e9f0;
}


.activity-detail-panel {
  flex: 1 1 0;
  min-width: 0;
  max-width: 100%;
  padding-left: 2px;
  overflow: hidden;
}

.detail-heading {
  display: block;
  margin-bottom: 9px;
  color: #7f8fa5;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.07em;
}

.activity-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 22px;
  row-gap: 9px;
}

.activity-detail-item {
  min-width: 0;
}

.activity-detail-item small {
  display: block;
  margin-bottom: 2px;
  color: #9aa9bc;
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.activity-detail-item strong {
  display: block;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  color: #33445a;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.activity-description {
  grid-column: 1 / -1;
}

.activity-description strong {
  display: -webkit-box;
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}


.read-more-button {
  margin-top: 5px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #1769dc;
  font-family: inherit;
  font-size: 10px;
  font-weight: 700;
  cursor: pointer;
}

.read-more-button:hover {
  text-decoration: underline;
}

.description-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(20, 32, 50, 0.38);
  backdrop-filter: blur(2px);
}

.description-modal {
  width: min(640px, 100%);
  max-height: min(70vh, 620px);
  overflow: hidden;
  border: 1px solid #e0e7f0;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 24px 60px rgba(29, 44, 68, 0.18);
}

.description-modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 20px 22px 16px;
  border-bottom: 1px solid #edf1f5;
}

.description-modal-header span {
  display: block;
  margin-bottom: 4px;
  color: #8ea0ba;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.description-modal-header h3 {
  margin: 0;
  color: #233248;
  font-size: 18px;
}

.description-modal-close {
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  border: 0;
  border-radius: 9px;
  background: #f3f6fa;
  color: #6d7d91;
  display: grid;
  place-items: center;
  cursor: pointer;
}

.description-modal-close:hover {
  background: #eaf0f7;
  color: #33445a;
}

.description-modal-body {
  max-height: calc(min(70vh, 620px) - 78px);
  overflow-y: auto;
  padding: 20px 22px 24px;
  color: #425268;
  font-size: 13px;
  line-height: 1.75;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.table-card {
  overflow: hidden;
  border: 1px solid #e0e7f0;
  border-radius: 13px;
  background: #fff;
}

.table-heading {
  padding: 17px 20px;
  border-bottom: 1px solid #e8edf4;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.table-heading h2 {
  margin: 0;
  font-size: 16px;
}

.table-heading p {
  margin: 4px 0 0;
  color: #8a99ae;
  font-size: 11px;
}

.row-count {
  padding: 6px 9px;
  border-radius: 999px;
  background: #eef4fc;
  color: #55708f;
  font-size: 10px;
  font-weight: 700;
}

.table-scroll {
  overflow-x: auto;
}

table {
  width: 100%;
  min-width: 1080px;
  border-collapse: collapse;
}

thead {
  background: #fafbfd;
}

th {
  padding: 14px 16px;
  color: #66758a;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-align: left;
}

td {
  min-height: 58px;
  padding: 13px 16px;
  border-top: 1px solid #edf1f5;
  color: #425268;
  font-size: 12px;
  vertical-align: middle;
}

tr.editing {
  background: #f8fbff;
}

.student-id,
.student-name {
  color: #1f3045;
  font-weight: 600;
}

.role-badge {
  display: inline-flex;
  min-height: 25px;
  padding: 0 9px;
  border-radius: 999px;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
}

.role-badge.participant {
  background: #eaf2ff;
  color: #1264d8;
}

.role-badge.organizer {
  background: #efeaff;
  color: #6744c4;
}

.edit-button,
.save-button,
.cancel-button {
  border: 0;
  font-family: inherit;
  cursor: pointer;
}

.edit-button {
  min-height: 30px;
  padding: 0 10px;
  border-radius: 7px;
  background: #edf4ff;
  color: #1769dc;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 700;
}

.edit-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.row-input,
.row-select {
  width: 100%;
  min-width: 120px;
  height: 36px;
  padding: 0 9px;
  border: 1px solid #cad7e7;
  border-radius: 7px;
  outline: none;
  background: #fff;
  color: #34455b;
  font: inherit;
  font-size: 11px;
}

.row-input:focus,
.row-select:focus {
  border-color: #76aaf1;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

.student-id-input {
  min-width: 105px;
}

.name-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  min-width: 230px;
}

.role-select {
  min-width: 115px;
}

.edit-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.save-button {
  min-height: 31px;
  padding: 0 10px;
  border-radius: 7px;
  background: #1769dc;
  color: #fff;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 700;
}

.cancel-button {
  width: 31px;
  height: 31px;
  border-radius: 7px;
  background: #f2f5f8;
  color: #6d7d91;
  display: grid;
  place-items: center;
}

.save-button:disabled,
.cancel-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.mini-spinner {
  width: 13px;
  height: 13px;
  border: 2px solid rgba(255, 255, 255, 0.45);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.save-error {
  padding: 10px 16px;
  border-top: 1px solid #f0dcdc;
  background: #fff2f2;
  color: #bd3c3c;
  font-size: 11px;
}

.load-status {
  padding: 32px 16px;
  text-align: center;
  color: #8ea0ba;
  font-size: 13px;
}

.load-status-error {
  color: #bd3c3c;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 800px) {
  .details-page {
    padding: 22px 16px 36px;
  }

  .page-header {
    flex-direction: column;
  }

  .activity-summary {
    align-items: flex-start;
    flex-direction: column;
  }

  .summary-divider {
    width: 100%;
    height: 1px;
  }

  .summary-item,
  .summary-item.activity-info {
    min-width: 0;
  }

  .activity-detail-panel {
    width: 100%;
    min-width: 0;
    padding-left: 0;
  }

  .detail-divider {
    display: none;
  }

  .activity-detail-grid {
    grid-template-columns: 1fr;
  }

  .activity-description {
    grid-column: auto;
  }
}
</style>