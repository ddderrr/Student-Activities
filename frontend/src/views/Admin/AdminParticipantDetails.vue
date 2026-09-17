<script setup>
import { computed, onMounted, ref } from 'vue'
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
  name: ''
})

const participants = ref([])
const pageLoading = ref(true)
const loadError = ref('')

const editingRowId = ref(null)
const editDraft = ref(null)
const savingRowId = ref(null)
const saveMessage = ref('')

const memberCount = computed(() => participants.value.length)
const participantCount = computed(
  () => participants.value.filter((student) => student.role === 'participant').length
)
const organizerCount = computed(
  () => participants.value.filter((student) => student.role === 'organizer').length
)

async function fetchParticipants() {
  pageLoading.value = true
  loadError.value = ''

  try {
    const response = await fetch(
      `${API_BASE}/api/activities/${activityId.value}/participants`
    )

    if (!response.ok) throw new Error('โหลดข้อมูลไม่สำเร็จ')

    const data = await response.json()

    activity.value = data.activity
    participants.value = data.students
  } catch (error) {
    loadError.value = error.message || 'โหลดข้อมูลไม่สำเร็จ'
  } finally {
    pageLoading.value = false
  }
}

onMounted(fetchParticipants)

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
                      v-for="major in majorOptions"
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
}
</style>