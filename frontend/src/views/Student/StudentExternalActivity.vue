<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  CheckCircle2,
  ImagePlus,
  Info,
  LoaderCircle,
  Paperclip,
  SlidersHorizontal,
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
  OTHER_CATEGORY_VALUE,
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

const defaultLevels = (definitions) =>
  Object.fromEntries(definitions.map((skill) => [skill.key, null]))

// เก็บแยกตาม role เพื่อให้สลับบทบาทไปมาแล้วค่าที่ตั้งไว้ไม่หาย
// เริ่มจาก "ไม่เกี่ยวข้อง" (null) ทั้งหมด นักศึกษาต้องเลือกเองอย่างน้อย 1 ทักษะ
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

/* =========================
   Category ("อื่น ๆ" custom category modal)
========================= */
// select แสดงตัวเลือกที่เลือกไว้ ส่วน form.activity_type คือค่าจริงที่ส่งไป backend
// (เมื่อเลือก "อื่น ๆ" ค่าที่ส่งจริงคือข้อความที่นักศึกษาพิมพ์เอง ไม่ใช่คำว่า "อื่น ๆ")
const selectedCategory = ref('')
const customCategoryText = ref('')
const showCategoryModal = ref(false)
const categoryModalDraft = ref('')
const categoryModalError = ref('')
let lastConfirmedCategory = ''

function applyCategoryFromValue(activityType) {
  if (activityType && EXTERNAL_ACTIVITY_CATEGORIES.includes(activityType)) {
    selectedCategory.value = activityType
    customCategoryText.value = ''
  } else if (activityType) {
    selectedCategory.value = OTHER_CATEGORY_VALUE
    customCategoryText.value = activityType
  } else {
    selectedCategory.value = ''
    customCategoryText.value = ''
  }

  lastConfirmedCategory = selectedCategory.value
}

function onCategorySelect() {
  if (selectedCategory.value === OTHER_CATEGORY_VALUE) {
    categoryModalDraft.value = customCategoryText.value
    categoryModalError.value = ''
    showCategoryModal.value = true
    return
  }

  customCategoryText.value = ''
  form.value.activity_type = selectedCategory.value
  lastConfirmedCategory = selectedCategory.value
}

function openCategoryModalForEdit() {
  categoryModalDraft.value = customCategoryText.value
  categoryModalError.value = ''
  showCategoryModal.value = true
}

function confirmCategoryModal() {
  const trimmed = categoryModalDraft.value.trim()

  if (!trimmed) {
    categoryModalError.value = t.value.studentExternalActivity.otherCategoryRequiredError
    return
  }

  customCategoryText.value = trimmed
  form.value.activity_type = trimmed
  lastConfirmedCategory = OTHER_CATEGORY_VALUE
  showCategoryModal.value = false
}

function cancelCategoryModal() {
  selectedCategory.value = lastConfirmedCategory
  showCategoryModal.value = false
}

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
    applyCategoryFromValue(item.activity_type)

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

const countRelated = (levels) =>
  Object.values(levels).filter((level) => level !== null).length

const relatedSkillCount = computed(() => countRelated(activeSkillLevels.value))

const roleSkillLabel = computed(() =>
  form.value.role === 'organizer'
    ? t.value.studentExternalActivity.staffTab
    : t.value.studentExternalActivity.participantTab
)

function skillsSummaryText(count) {
  if (count === 0) return t.value.studentExternalActivity.skillsNoneSelected

  const template = count === 1
    ? t.value.studentExternalActivity.skillsSelectedSingular
    : t.value.studentExternalActivity.skillsSelectedPlural
  return template.replace('{count}', count)
}

// error ของช่องทักษะแสดงที่ตัวช่องเอง หายเมื่อเลือกทักษะแล้วอย่างน้อย 1 ทักษะ
const skillsField = ref(null)
const skillsError = ref('')

watch(relatedSkillCount, (count) => {
  if (count > 0) skillsError.value = ''
})

/* =========================
   Skills modal
   แก้บน draft: บันทึก = เขียนกลับ, ยกเลิก/ปิด = ทิ้ง draft
========================= */
const showSkillsModal = ref(false)
const skillDraft = ref({})

const draftRelatedCount = computed(() => countRelated(skillDraft.value))

function openSkillsModal() {
  skillDraft.value = { ...activeSkillLevels.value }
  showSkillsModal.value = true
}

function cancelSkillsModal() {
  showSkillsModal.value = false
}

function saveSkillsModal() {
  activeSkillLevels.value = { ...skillDraft.value }
  showSkillsModal.value = false
}

function onKeydown(event) {
  if (event.key === 'Escape' && showSkillsModal.value) cancelSkillsModal()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

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
  skillsError.value = relatedSkillCount.value === 0
    ? t.value.studentExternalActivity.skillRequiredError
    : ''

  // ถ้าผิดแค่ช่องทักษะ เลื่อนจอไปที่ช่องนั้น (error อื่นแสดงอยู่ข้างปุ่มส่งแล้ว)
  if (skillsError.value && !formError.value) {
    await nextTick()
    skillsField.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    skillsField.value?.querySelector('button')?.focus({ preventScroll: true })
  }

  if (formError.value || skillsError.value) return

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
    applyCategoryFromValue('')
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
              <select v-model="selectedCategory" name="activity_type" @change="onCategorySelect">
                <option disabled value="">{{ t.studentExternalActivity.selectCategoryOption }}</option>
                <option
                  v-for="category in EXTERNAL_ACTIVITY_CATEGORIES"
                  :key="category"
                  :value="category"
                >
                  {{ category }}
                </option>
              </select>

              <div v-if="selectedCategory === OTHER_CATEGORY_VALUE" class="custom-category-display">
                <span>{{ t.studentExternalActivity.otherCategoryDisplayLabel }}: <strong>{{ customCategoryText }}</strong></span>
                <button type="button" class="custom-category-edit" @click="openCategoryModalForEdit">
                  {{ t.studentExternalActivity.otherCategoryEditButton }}
                </button>
              </div>
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

            <div
              ref="skillsField"
              class="field full skills-field"
              :class="{ invalid: skillsError }"
            >
              <span id="skills-field-label">{{ t.studentExternalActivity.skillsFieldLabel }} <b>*</b></span>

              <div class="skills-field-row">
                <div class="skills-field-summary" :class="{ empty: relatedSkillCount === 0 }">
                  <strong>{{ skillsSummaryText(relatedSkillCount) }}</strong>
                  <small>{{ roleSkillLabel }} · {{ t.studentExternalActivity.skillsFieldHint }}</small>
                </div>

                <button
                  type="button"
                  class="view-skills-button"
                  aria-labelledby="skills-field-label"
                  aria-haspopup="dialog"
                  @click="openSkillsModal"
                >
                  <SlidersHorizontal :size="15" />
                  {{ t.studentExternalActivity.viewSkillsButton }}
                </button>
              </div>

              <p v-if="skillsError" class="field-error" role="alert">
                <TriangleAlert :size="14" />
                {{ skillsError }}
              </p>
            </div>

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

    </form>

    <!-- SKILLS MODAL -->
    <div
      v-if="showSkillsModal"
      class="modal-backdrop skills-backdrop"
      @click.self="cancelSkillsModal"
    >
      <div
        class="skills-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="skills-modal-title"
      >
        <div class="modal-header skills-modal-header">
          <div>
            <h2 id="skills-modal-title">
              {{ t.studentExternalActivity.skillMappingHeading }} ({{ roleSkillLabel }})
            </h2>
            <p class="card-subtitle">{{ t.studentExternalActivity.skillMappingSubtitle }}</p>
          </div>

          <button
            class="modal-close"
            type="button"
            :aria-label="t.studentExternalActivity.skillsModalClose"
            @click="cancelSkillsModal"
          >
            <X :size="20" />
          </button>
        </div>

        <!-- เลื่อนได้เฉพาะเนื้อหา ปุ่มด้านล่างอยู่กับที่เสมอ -->
        <div class="skills-modal-body">
          <SkillLevelEditor
            v-model="skillDraft"
            :definitions="skillDefinitions"
            compact
          />
        </div>

        <div class="skills-modal-footer">
          <span class="skills-modal-count" :class="{ empty: draftRelatedCount === 0 }">
            {{ skillsSummaryText(draftRelatedCount) }}
          </span>

          <div class="skills-modal-actions">
            <button type="button" class="modal-secondary-button" @click="cancelSkillsModal">
              {{ t.studentExternalActivity.skillsModalCancel }}
            </button>

            <button type="button" class="modal-confirm-button" @click="saveSkillsModal">
              {{ t.studentExternalActivity.skillsModalSave }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- OTHER CATEGORY MODAL -->
    <div
      v-if="showCategoryModal"
      class="modal-backdrop"
      @click.self="cancelCategoryModal"
    >
      <div class="category-modal">
        <div class="modal-header">
          <h2>{{ t.studentExternalActivity.otherCategoryModalTitle }}</h2>

          <button class="modal-close" type="button" @click="cancelCategoryModal">
            <X :size="20" />
          </button>
        </div>

        <label class="field full">
          <input
            v-model="categoryModalDraft"
            type="text"
            maxlength="120"
            :placeholder="t.studentExternalActivity.otherCategoryInputPlaceholder"
            @keyup.enter="confirmCategoryModal"
          />
        </label>

        <p v-if="categoryModalError" class="category-modal-error">
          <TriangleAlert :size="15" />
          {{ categoryModalError }}
        </p>

        <div class="modal-actions">
          <button type="button" class="modal-secondary-button" @click="cancelCategoryModal">
            {{ t.studentExternalActivity.otherCategoryCancelButton }}
          </button>

          <button type="button" class="modal-confirm-button" @click="confirmCategoryModal">
            {{ t.studentExternalActivity.otherCategoryConfirmButton }}
          </button>
        </div>
      </div>
    </div>
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
  max-width: 860px;
  display: flex;
  flex-direction: column;
  gap: 16px;
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

.skills-field-row {
  padding: 10px 12px;
  border: 1px solid #dfe3ea;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: #fff;
}

.skills-field.invalid .skills-field-row {
  border-color: #e0453a;
  box-shadow: 0 0 0 3px rgba(224, 69, 58, 0.08);
}

.skills-field-summary {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.skills-field-summary strong {
  color: #1d2f6f;
  font-size: 13px;
}

.skills-field-summary.empty strong {
  color: #8a5a00;
}

.skills-field-summary small {
  color: #7e8796;
  font-size: 11.5px;
}

.skills-field .field-error {
  margin: 0;
}

.view-skills-button {
  min-height: 36px;
  padding: 0 14px;
  border: 1px solid #d9c6f3;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  background: #f7f0ff;
  color: #7e10c6;
  font: inherit;
  font-size: 12.5px;
  font-weight: 700;
  cursor: pointer;
}

.view-skills-button:hover {
  background: #efe3ff;
}

.view-skills-button:focus-visible {
  outline: 2px solid #9b5de5;
  outline-offset: 2px;
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

  .skills-field-row {
    flex-direction: column;
    align-items: stretch;
  }

  .view-skills-button {
    justify-content: center;
  }
}

/* =========================
   Other category modal
========================= */
.custom-category-display {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 12px;
  color: #53647c;
}

.custom-category-display strong {
  color: #2a3547;
}

.custom-category-edit {
  border: 0;
  background: none;
  padding: 0;
  color: #7e10c6;
  font: inherit;
  font-weight: 700;
  font-size: 12px;
  cursor: pointer;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1200;
  padding: 22px;
  display: grid;
  place-items: center;
  background: rgba(15, 23, 42, 0.34);
}

.category-modal {
  width: min(420px, 100%);
  padding: 22px;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 24px 65px rgba(15, 23, 42, 0.2);
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 16px;
}

.modal-header h2 {
  margin: 0;
  color: #1b283d;
  font-size: 18px;
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
  flex-shrink: 0;
}

.category-modal-error {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 8px 0 0;
  color: #e0453a;
  font-size: 12px;
}

.modal-actions {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
  gap: 9px;
  flex-wrap: wrap;
}

.modal-secondary-button,
.modal-confirm-button {
  min-height: 39px;
  padding: 0 14px;
  border: 0;
  border-radius: 9px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: inherit;
  font-weight: 700;
  cursor: pointer;
}

.modal-secondary-button {
  border: 1px solid #dfe6ef;
  background: #fff;
  color: #526279;
}

.modal-confirm-button {
  background: #7e10c6;
  color: #fff;
}

/* =========================
   Skills modal
   header / footer อยู่กับที่ เลื่อนเฉพาะ body
========================= */
.skills-modal {
  width: min(600px, 100%);
  max-height: calc(100vh - 44px);
  max-height: calc(100dvh - 44px);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 24px 65px rgba(15, 23, 42, 0.2);
}

.skills-modal-header {
  margin: 0;
  padding: 20px 22px 4px;
  flex-shrink: 0;
}

.skills-modal-header .card-subtitle {
  margin: 6px 0 0;
}

.skills-modal-body {
  flex: 1 1 auto;
  min-height: 0;
  padding: 12px 22px 16px;
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
}

.skills-modal-footer {
  flex-shrink: 0;
  padding: 12px 22px;
  border-top: 1px solid #eef0f4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  background: #fff;
}

.skills-modal-count {
  color: #1d2f6f;
  font-size: 12.5px;
  font-weight: 700;
}

.skills-modal-count.empty {
  color: #8a5a00;
}

.skills-modal-actions {
  display: flex;
  gap: 9px;
}

@media (max-width: 640px) {
  /* บนมือถือเป็น bottom sheet เต็มความกว้าง ปุ่มติดขอบล่างเสมอ */
  .skills-backdrop {
    padding: 0;
    align-items: end;
  }

  .skills-modal {
    width: 100%;
    max-height: 92vh;
    max-height: 92dvh;
    border-radius: 16px 16px 0 0;
  }

  .skills-modal-header {
    padding: 16px 16px 4px;
  }

  .skills-modal-body {
    padding: 10px 16px 14px;
  }

  .skills-modal-footer {
    padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
    flex-direction: column;
    align-items: stretch;
  }

  .skills-modal-actions > button {
    flex: 1;
  }
}
</style>
