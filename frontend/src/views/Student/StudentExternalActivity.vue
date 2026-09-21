<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  CheckCircle2,
  ImagePlus,
  Info,
  LoaderCircle,
  Paperclip,
  TrendingUp,
  TriangleAlert,
  X
} from 'lucide-vue-next'
import SkillLevelEditor from '../../components/Admin/SkillLevelEditor.vue'
import DatePicker from '../../components/common/DatePicker.vue'
import { useLanguage } from '../../composables/useLanguage'
import {
  API_BASE,
  EVIDENCE_EXTENSIONS,
  EVIDENCE_MAX_BYTES,
  EXTERNAL_ACTIVITY_CATEGORIES,
  EXTERNAL_ROLE_OPTIONS,
  formatFileSize,
  studentHeaders
} from '../../constants/currentStudent'
import {
  PARTICIPANT_SKILLS,
  STAFF_SKILLS
} from '../../constants/activitySkills'

// role ของนักศึกษากำหนดชุด Skill: participant -> Participant skills, organizer -> Staff skills
const { t } = useLanguage()

const SKILLS_BY_ROLE = {
  participant: PARTICIPANT_SKILLS,
  organizer: STAFF_SKILLS
}

const DEFAULT_SKILL_LEVEL = 3

const defaultLevels = (definitions) =>
  Object.fromEntries(definitions.map((skill) => [skill.key, DEFAULT_SKILL_LEVEL]))

// เก็บแยกตาม role เพื่อให้สลับบทบาทไปมาแล้วค่าที่ตั้งไว้ไม่หาย
// เริ่มจาก Level 3 ทั้งหมด นักศึกษาปรับระดับ หรือปิดเป็น "ไม่เกี่ยวข้อง" เองได้
const emptySkillLevels = () => ({
  participant: defaultLevels(PARTICIPANT_SKILLS),
  organizer: defaultLevels(STAFF_SKILLS)
})

/* =========================
   Form
========================= */
const emptyForm = () => ({
  title: '',
  organization: '',
  activity_type: '',
  role: 'participant',
  start_date: '',
  end_date: '',
  location: '',
  description: ''
})

const route = useRoute()

const form = ref(emptyForm())
const skillLevels = ref(emptySkillLevels())
const evidenceFile = ref(null)
const fileInput = ref(null)
const isDragging = ref(false)

const formError = ref('')
const successMessage = ref('')
const submitting = ref(false)

// แก้ไข+ส่งใหม่กิจกรรมที่ถูกไม่อนุมัติ: /student/external-activity?edit=<id>
const editingId = ref(null)
const existingEvidence = ref(null)

onMounted(async () => {
  const editId = Number(route.query.edit)
  if (!editId) return

  try {
    const response = await fetch(`${API_BASE}/api/student/me/external-activities`, {
      headers: studentHeaders()
    })

    if (!response.ok) throw new Error(t.value.studentExternalActivity.loadEditFailed)

    const data = await response.json()
    const item = (data.external_activities || []).find((activity) => activity.id === editId)

    if (!item || item.status !== 'rejected') {
      formError.value = t.value.studentExternalActivity.editNotFound
      return
    }

    editingId.value = item.id

    form.value = {
      title: item.title,
      organization: item.organization,
      activity_type: item.activity_type,
      role: item.role,
      start_date: item.start_date,
      end_date: item.end_date,
      location: item.location,
      description: item.description || ''
    }

    const definitions = SKILLS_BY_ROLE[item.role]
    skillLevels.value = {
      ...emptySkillLevels(),
      [item.role]: Object.fromEntries(
        definitions.map((skill) => [skill.key, item.skills?.[skill.key] ?? null])
      )
    }

    existingEvidence.value = item.evidence
  } catch (error) {
    formError.value = error.message || t.value.studentExternalActivity.loadEditFailed
  }
})

/* =========================
   Skill Mapping
========================= */
const skillDefinitions = computed(() => SKILLS_BY_ROLE[form.value.role])

const activeSkillLevels = computed({
  get: () => skillLevels.value[form.value.role],
  set: (value) => {
    skillLevels.value = { ...skillLevels.value, [form.value.role]: value }
  }
})

const relatedSkillCount = computed(() =>
  Object.values(activeSkillLevels.value).filter((level) => level !== null).length
)

// ตรวจทันทีที่เลือกวันที่ ไม่ต้องรอกด Submit ก่อนจะรู้ว่าช่วงวันที่ผิด
const dateRangeError = computed(() => {
  if (!form.value.start_date || !form.value.end_date) return ''

  return form.value.end_date < form.value.start_date
    ? t.value.studentExternalActivity.dateRangeError
    : ''
})

/* =========================
   Evidence file
========================= */
function openFilePicker() {
  fileInput.value?.click()
}

function fileProblem(file) {
  const name = file.name.toLowerCase()

  if (!EVIDENCE_EXTENSIONS.some((extension) => name.endsWith(extension))) {
    return t.value.studentExternalActivity.fileTypeError
  }

  if (file.size === 0) return t.value.studentExternalActivity.fileEmptyError

  if (file.size > EVIDENCE_MAX_BYTES) {
    return t.value.studentExternalActivity.fileSizeError
  }

  return ''
}

function setEvidenceFile(file) {
  if (!file) return

  const problem = fileProblem(file)

  if (problem) {
    formError.value = problem
    return
  }

  formError.value = ''
  evidenceFile.value = file
}

function handleFileChange(event) {
  setEvidenceFile(event.target.files?.[0])
  // ให้เลือกไฟล์เดิมซ้ำได้หลังลบออก
  event.target.value = ''
}

function handleDrop(event) {
  isDragging.value = false
  setEvidenceFile(event.dataTransfer?.files?.[0])
}

function removeEvidenceFile() {
  evidenceFile.value = null
}

/* =========================
   Submit
========================= */
function validateForm() {
  const value = form.value

  const required = [
    value.title,
    value.organization,
    value.activity_type,
    value.role,
    value.start_date,
    value.end_date,
    value.location
  ]

  if (required.some((item) => !String(item || '').trim())) {
    return t.value.studentExternalActivity.requiredFieldsError
  }

  if (dateRangeError.value) {
    return dateRangeError.value
  }

  if (relatedSkillCount.value === 0) {
    return t.value.studentExternalActivity.skillRequiredError
  }

  if (!evidenceFile.value && !existingEvidence.value) {
    return t.value.studentExternalActivity.evidenceRequiredError
  }

  return evidenceFile.value ? fileProblem(evidenceFile.value) : ''
}

function errorDetail(data, fallback) {
  if (Array.isArray(data?.detail)) {
    return data.detail.map((item) => item.msg || String(item)).join(', ')
  }

  return data?.detail || fallback
}

async function submitActivity() {
  if (submitting.value) return

  successMessage.value = ''
  formError.value = validateForm()
  if (formError.value) return

  const body = new FormData()

  for (const [key, value] of Object.entries(form.value)) {
    body.append(key, typeof value === 'string' ? value.trim() : value)
  }

  // ส่งเฉพาะชุด Skill ของ role ที่เลือก
  body.append('skills', JSON.stringify(activeSkillLevels.value))

  // ตอนแก้ไข ถ้าไม่ได้เลือกไฟล์ใหม่ ไม่ต้องแนบ 'evidence' ไป backend จะใช้ไฟล์เดิมต่อ
  if (evidenceFile.value) {
    body.append('evidence', evidenceFile.value)
  }

  submitting.value = true

  try {
    const url = editingId.value
      ? `${API_BASE}/api/student/me/external-activities/${editingId.value}`
      : `${API_BASE}/api/student/me/external-activities`

    const response = await fetch(url, {
      method: editingId.value ? 'PUT' : 'POST',
      headers: studentHeaders(),
      body
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      throw new Error(errorDetail(data, t.value.studentExternalActivity.submitFailedFallback))
    }

    successMessage.value = editingId.value
      ? `${t.value.studentExternalActivity.resubmitSuccessPrefix} "${data.title}" ${t.value.studentExternalActivity.resubmitSuccessSuffix}`
      : `${t.value.studentExternalActivity.submitSuccessPrefix} "${data.title}" ${t.value.studentExternalActivity.submitSuccessSuffix}`
    form.value = emptyForm()
    skillLevels.value = emptySkillLevels()
    evidenceFile.value = null
    existingEvidence.value = null
    editingId.value = null
  } catch (error) {
    formError.value =
      error instanceof TypeError
        ? `${t.value.studentExternalActivity.connectionError} (${API_BASE})`
        : error.message
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="external-page">
    <header class="page-title">
      <h1>{{ editingId ? t.studentExternalActivity.editTitle : t.studentExternalActivity.addTitle }}</h1>
      <p>
        {{
          editingId
            ? t.studentExternalActivity.editSubtitle
            : t.studentExternalActivity.addSubtitle
        }}
      </p>
    </header>

    <form class="page-grid" novalidate @submit.prevent="submitActivity">
      <!-- LEFT: activity details + evidence -->
      <div class="form-column form-main">
        <section class="card">
          <div class="card-heading">
            <span class="heading-icon"><Info :size="16" /></span>
            <h2>{{ t.studentExternalActivity.activityDetailsHeading }}</h2>
          </div>

          <div class="form-grid">
            <label class="field full">
              <span>{{ t.studentExternalActivity.activityNameLabel }} <b>*</b></span>
              <input
                v-model="form.title"
                name="title"
                type="text"
                maxlength="255"
                :placeholder="t.studentExternalActivity.activityNamePlaceholder"
              />
            </label>

            <label class="field full">
              <span>{{ t.studentExternalActivity.organizerLabel }} <b>*</b></span>
              <input
                v-model="form.organization"
                name="organization"
                type="text"
                maxlength="255"
                :placeholder="t.studentExternalActivity.organizerPlaceholder"
              />
            </label>

            <label class="field">
              <span>{{ t.studentExternalActivity.categoryLabel }} <b>*</b></span>
              <select v-model="form.activity_type" name="activity_type">
                <option disabled value="">{{ t.studentExternalActivity.selectCategoryOption }}</option>
                <option
                  v-for="category in EXTERNAL_ACTIVITY_CATEGORIES"
                  :key="category"
                  :value="category"
                >
                  {{ category }}
                </option>
              </select>
            </label>

            <label class="field">
              <span>{{ t.studentExternalActivity.roleLabel }} <b>*</b></span>
              <select v-model="form.role" name="role">
                <option
                  v-for="role in EXTERNAL_ROLE_OPTIONS"
                  :key="role.value"
                  :value="role.value"
                >
                  {{ role.label }}
                </option>
              </select>
            </label>

            <label class="field full">
              <span>{{ t.studentExternalActivity.descriptionLabel }}</span>
              <textarea
                v-model="form.description"
                name="description"
                rows="4"
                :placeholder="t.studentExternalActivity.descriptionPlaceholder"
              ></textarea>
            </label>

            <label class="field">
              <span>{{ t.studentExternalActivity.startDateLabel }} <b>*</b></span>
              <DatePicker v-model="form.start_date" :placeholder="t.studentExternalActivity.startDatePlaceholder" />
            </label>

            <label class="field">
              <span>{{ t.studentExternalActivity.endDateLabel }} <b>*</b></span>
              <DatePicker
                v-model="form.end_date"
                :min="form.start_date"
                :placeholder="t.studentExternalActivity.endDatePlaceholder"
              />
            </label>

            <p v-if="dateRangeError" class="field-error full">
              <TriangleAlert :size="14" />
              {{ dateRangeError }}
            </p>

            <label class="field full">
              <span>{{ t.studentExternalActivity.locationLabel }} <b>*</b></span>
              <input
                v-model="form.location"
                name="location"
                type="text"
                maxlength="255"
                :placeholder="t.studentExternalActivity.locationPlaceholder"
              />
            </label>
          </div>
        </section>

        <div
          class="upload-box"
          :class="{ dragging: isDragging, 'has-file': evidenceFile || existingEvidence }"
          @click="!evidenceFile && openFilePicker()"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <input
            ref="fileInput"
            class="file-input"
            type="file"
            name="evidence"
            accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
            @change="handleFileChange"
          />

          <template v-if="!evidenceFile && !existingEvidence">
            <span class="upload-icon"><ImagePlus :size="20" /></span>
            <strong>{{ t.studentExternalActivity.uploadEvidenceLabel }} <b>*</b></strong>
            <p>{{ t.studentExternalActivity.uploadEvidenceHint }}</p>
            <button type="button" class="link-button" @click.stop="openFilePicker">
              {{ t.studentExternalActivity.chooseFileButton }}
            </button>
          </template>

          <div v-else-if="!evidenceFile && existingEvidence" class="selected-file" @click.stop>
            <span class="upload-icon"><Paperclip :size="18" /></span>
            <div>
              <strong>{{ existingEvidence.original_name }}</strong>
              <small>{{ formatFileSize(existingEvidence.size) }} · {{ t.studentExternalActivity.currentEvidenceLabel }}</small>
            </div>
            <button type="button" class="link-button" @click.stop="openFilePicker">
              {{ t.studentExternalActivity.replaceFileButton }}
            </button>
          </div>

          <div v-else class="selected-file" @click.stop>
            <span class="upload-icon"><Paperclip :size="18" /></span>
            <div>
              <strong>{{ evidenceFile.name }}</strong>
              <small>{{ formatFileSize(evidenceFile.size) }}</small>
            </div>
            <button
              type="button"
              class="remove-file"
              :aria-label="t.studentExternalActivity.removeFileAriaLabel"
              @click="removeEvidenceFile"
            >
              <X :size="15" />
            </button>
          </div>
        </div>

      </div>

      <!-- ข้อความ + ปุ่มส่ง (บนจอแคบจะอยู่ใต้ Skill Mapping) -->
      <div class="form-column form-footer">
        <div v-if="formError" class="alert error" role="alert">
          <TriangleAlert :size="16" />
          {{ formError }}
        </div>

        <div v-if="successMessage" class="alert success" role="status">
          <CheckCircle2 :size="16" />
          <span>
            {{ successMessage }}
            <RouterLink
              class="status-link"
              :to="{ path: '/student/activities', query: { tab: 'submissions' } }"
            >
              {{ t.studentExternalActivity.viewStatusLink }}
            </RouterLink>
          </span>
        </div>

        <div class="form-actions">
          <button type="submit" class="primary-button" :disabled="submitting">
            <LoaderCircle v-if="submitting" class="spin" :size="15" />
            {{
              submitting
                ? (editingId ? t.studentExternalActivity.resubmittingButton : t.studentExternalActivity.submittingButton)
                : (editingId ? t.studentExternalActivity.resubmitButton : t.studentExternalActivity.submitButton)
            }}
          </button>
        </div>
      </div>

      <!-- RIGHT: Skill Mapping (ตาม design) -->
      <aside class="card skills-card">
        <div class="card-heading">
          <span class="heading-icon green"><TrendingUp :size="16" /></span>
          <h2>{{ t.studentExternalActivity.skillMappingHeading }}</h2>
        </div>
        <p class="card-subtitle">
          {{ t.studentExternalActivity.skillMappingSubtitle }}
        </p>

        <!-- ชุด Skill ตามบทบาทที่เลือกใน "Your Role" ด้านบน แท็บนี้แสดงผลอย่างเดียว
             ไม่ใช่ตัวเลือก role อีกช่องหนึ่ง จึงปิดแท็บที่ไม่ตรง role ไว้ -->
        <div class="role-tabs" role="tablist" :aria-label="t.studentExternalActivity.skillSetAriaLabel">
          <button
            type="button"
            role="tab"
            data-role="participant"
            :aria-selected="form.role === 'participant'"
            :class="{ active: form.role === 'participant' }"
            :disabled="form.role !== 'participant'"
          >
            {{ t.studentExternalActivity.participantTab }}
          </button>
          <button
            type="button"
            role="tab"
            data-role="organizer"
            :aria-selected="form.role === 'organizer'"
            :class="{ active: form.role === 'organizer' }"
            :disabled="form.role !== 'organizer'"
          >
            {{ t.studentExternalActivity.staffTab }}
          </button>
        </div>

        <SkillLevelEditor
          v-model="activeSkillLevels"
          :definitions="skillDefinitions"
          compact
        />

        <div class="skill-summary" :class="{ empty: relatedSkillCount === 0 }">
          <strong>{{ relatedSkillCount }} {{ relatedSkillCount === 1 ? t.studentExternalActivity.relatedSkillSingular : t.studentExternalActivity.relatedSkillPlural }}</strong>
          <span>
            {{ t.studentExternalActivity.skillSummaryHint }}
            ({{ form.role === 'organizer' ? t.studentExternalActivity.staffTab : t.studentExternalActivity.participantTab }})
          </span>
        </div>
      </aside>
    </form>
  </section>
</template>

<style scoped>
.external-page {
  min-height: 100vh;
  padding: 30px;
  background: #f5f7fb;
  color: #1c2434;
}

.page-title {
  margin-bottom: 22px;
}

.page-title h1 {
  margin: 0;
  color: #1d2f6f;
  font-size: 22px;
  font-weight: 700;
}

.page-title p {
  margin: 6px 0 0;
  color: #7e8796;
  font-size: 13px;
}

.page-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(320px, 1fr);
  grid-template-areas:
    "main skills"
    "footer skills";
  grid-template-rows: auto 1fr;
  gap: 16px 18px;
  align-items: start;
}

.form-main {
  grid-area: main;
}

.form-footer {
  grid-area: footer;
}

.skills-card {
  grid-area: skills;
}

.form-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.card {
  padding: 18px 20px;
  border: 1px solid #e6eaf1;
  border-radius: 12px;
  background: #fff;
}

.card-heading {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-heading h2 {
  margin: 0;
  color: #1c2434;
  font-size: 14px;
  font-weight: 700;
}

.heading-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: #eef1ff;
  color: #1d2f6f;
}

.heading-icon.green {
  background: #dcf7ea;
  color: #11875a;
}

.card-subtitle {
  margin: 8px 0 14px;
  color: #7e8796;
  font-size: 12px;
}

.form-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 0;
}

.field.full {
  grid-column: 1 / -1;
}

.field-error {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: -4px 0 0;
  color: #e0453a;
  font-size: 12px;
}

.field-error.full {
  grid-column: 1 / -1;
}

.field > span {
  color: #1c2434;
  font-size: 12px;
  font-weight: 700;
}

.field b,
.upload-box b {
  color: #e0453a;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  border: 1px solid #dfe3ea;
  border-radius: 8px;
  outline: none;
  background: #fff;
  color: #1c2434;
  font: inherit;
  font-size: 13px;
  box-sizing: border-box;
}

.field input,
.field select {
  height: 40px;
  padding: 0 12px;
}

.field textarea {
  min-height: 96px;
  padding: 10px 12px;
  resize: vertical;
}

.field input::placeholder,
.field textarea::placeholder {
  color: #a3aab6;
}

.field input:focus,
.field select:focus,
.field textarea:focus {
  border-color: #9b5de5;
  box-shadow: 0 0 0 3px rgba(126, 16, 198, 0.08);
}

.upload-box {
  position: relative;
  padding: 26px 20px;
  border: 1.5px dashed #c9cfda;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  background: #fafbfd;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.upload-box.dragging {
  border-color: #7e10c6;
  background: #f7f0ff;
}

.upload-box.has-file {
  cursor: default;
}

.file-input {
  display: none;
}

.upload-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: #eceff4;
  color: #4a5567;
}

.upload-box > strong {
  margin-top: 4px;
  color: #1d2f6f;
  font-size: 13px;
}

.upload-box > p {
  margin: 0;
  color: #4a5567;
  font-size: 12px;
}

.link-button {
  border: none;
  background: none;
  color: #1e45c8;
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.selected-file {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
}

.selected-file > div {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.selected-file strong {
  overflow: hidden;
  color: #1c2434;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-file small {
  color: #7e8796;
  font-size: 11px;
}

.remove-file {
  width: 30px;
  height: 30px;
  border: 1px solid #e3e7ee;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: #fff;
  color: #6b7280;
  cursor: pointer;
}

.alert {
  padding: 10px 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
}

.alert.error {
  background: #fdeaea;
  color: #b42318;
}

.alert.success {
  background: #e6f8ed;
  color: #116c3f;
}

.status-link {
  margin-left: 6px;
  color: #116c3f;
  font-weight: 700;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}

.primary-button {
  min-width: 150px;
  min-height: 42px;
  padding: 0 18px;
  border: none;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  background: #7e10c6;
  color: #fff;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 6px 14px rgba(126, 16, 198, 0.2);
}

.primary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spin {
  animation: spin 0.75s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.skills-card {
  position: sticky;
  top: 16px;
}

.role-tabs {
  margin-bottom: 14px;
  padding: 3px;
  border-radius: 9px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 2px;
  background: #eef0f4;
}

.role-tabs button {
  padding: 8px 4px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: #4a5567;
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.role-tabs button.active {
  background: #fff;
  color: #1c2434;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

.role-tabs button:disabled {
  color: #b0b8c4;
  cursor: not-allowed;
}

.skill-summary {
  margin-top: 14px;
  padding: 10px 12px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  background: #eef1ff;
  color: #1d2f6f;
  font-size: 11.5px;
}

.skill-summary strong {
  font-size: 12.5px;
}

.skill-summary.empty {
  background: #fff5da;
  color: #8a5a00;
}

@media (max-width: 1100px) {
  .page-grid {
    grid-template-columns: 1fr;
    grid-template-areas:
      "main"
      "skills"
      "footer";
    grid-template-rows: auto;
  }

  .skills-card {
    position: static;
  }
}

@media (max-width: 640px) {
  .external-page {
    padding: 18px 16px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .primary-button {
    width: 100%;
  }
}
</style>
