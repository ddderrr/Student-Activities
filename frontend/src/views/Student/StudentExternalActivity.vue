<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  CheckCircle2,
  ImagePlus,
  Info,
  LoaderCircle,
  Paperclip,
  Send,
  SlidersHorizontal,
  Sparkles,
  TriangleAlert,
  X
} from 'lucide-vue-next'
import SkillLevelEditor from '../../components/Admin/SkillLevelEditor.vue'
import DatePicker from '../../components/common/DatePicker.vue'
import { validHours } from '../../utils/activityHours'
import { useLanguage } from '../../composables/useLanguage'
import {
  API_BASE,
  EVIDENCE_EXTENSIONS,
  EVIDENCE_MAX_BYTES,
  EVIDENCE_MAX_FILES,
  EXTERNAL_ACTIVITY_CATEGORIES,
  EXTERNAL_ROLE_OPTIONS,
  OTHER_CATEGORY_VALUE,
  formatFileSize,
  studentHeaders
} from '../../constants/currentStudent'
import {
  PARTICIPANT_SKILLS,
  STAFF_SKILLS,
  defaultSkillLevels
} from '../../constants/activitySkills'

// role ของนักศึกษากำหนดชุด Skill: participant -> Participant skills, organizer -> Staff skills
const { t } = useLanguage()

const SKILLS_BY_ROLE = {
  participant: PARTICIPANT_SKILLS,
  organizer: STAFF_SKILLS
}

// เก็บแยกตาม role: เริ่มที่ level 3 (มีส่วนร่วม) ทุกทักษะ นักศึกษาติ๊ก "ไม่เกี่ยวข้อง" เองได้
// เปลี่ยนบทบาทเมื่อไหร่ ชุดทักษะของบทบาทใหม่รีเซ็ตกลับเป็น level 3 (onRoleChange)
const emptySkillLevels = () => ({
  participant: defaultSkillLevels(PARTICIPANT_SKILLS),
  organizer: defaultSkillLevels(STAFF_SKILLS)
})

/* =========================
   Form
========================= */
const emptyForm = () => ({
  title: '',
  activity_hours: '',
  organization: '',
  activity_type: '',
  // ยังไม่เลือก: ซ่อนแผงทักษะ ฟอร์มเต็มความกว้าง (เลือกแล้วจึงเป็นสองคอลัมน์)
  role: '',
  start_date: '',
  end_date: '',
  location: '',
  description: ''
})

const route = useRoute()
const router = useRouter()

const form = ref(emptyForm())
const skillLevels = ref(emptySkillLevels())
// ไฟล์ที่เลือกใหม่ (File) ยังไม่ได้อัปโหลด
const newEvidenceFiles = ref([])
const fileInput = ref(null)
const isDragging = ref(false)

const formError = ref('')
// ขั้นตอนส่ง: กดส่ง -> popup ยืนยัน -> ส่งจริง -> popup สำเร็จ
// ทั้งสอง popup ปิดด้วยปุ่มในกรอบเท่านั้น (ยืนยันกด Esc = ยกเลิกได้)
const showSubmitConfirm = ref(false)
const submitConfirmButton = ref(null)
const submitResult = ref(null)
const submitResultPrimary = ref(null)
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
// ไฟล์เดิมของคำขอที่กำลังแก้ไข และ id ที่ผู้ใช้กดลบ (ลบจริงตอนส่ง)
const existingEvidence = ref([])
const removedEvidenceIds = ref([])

const keptExistingEvidence = computed(() =>
  existingEvidence.value.filter((item) => !removedEvidenceIds.value.includes(item.id))
)

const evidenceCount = computed(() =>
  keptExistingEvidence.value.length + newEvidenceFiles.value.length
)

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
      description: item.description || '',
      activity_hours: item.activity_hours || ''
    }
    applyCategoryFromValue(item.activity_type)

    const definitions = SKILLS_BY_ROLE[item.role]
    skillLevels.value = {
      ...emptySkillLevels(),
      [item.role]: Object.fromEntries(
        definitions.map((skill) => [skill.key, item.skills?.[skill.key] ?? null])
      )
    }

    existingEvidence.value = item.evidence_files || []
    removedEvidenceIds.value = []
  } catch (error) {
    formError.value = error.message || t.value.studentExternalActivity.loadEditFailed
  }
})

/* =========================
   Skill Mapping
========================= */
const hasRole = computed(() => Boolean(SKILLS_BY_ROLE[form.value.role]))

const skillDefinitions = computed(() => SKILLS_BY_ROLE[form.value.role] || [])

const activeSkillLevels = computed({
  get: () => skillLevels.value[form.value.role] || {},
  set: (value) => {
    if (!hasRole.value) return
    skillLevels.value = { ...skillLevels.value, [form.value.role]: value }
  }
})

// เรียกจาก @change ของ dropdown เท่านั้น (ผู้ใช้เปลี่ยนเอง) -- ตอนโหลดรายการ
// ที่ถูกปฏิเสธมาแก้ไข role ถูกตั้งจากโค้ด ต้องไม่ล้างระดับทักษะที่บันทึกไว้
function onRoleChange() {
  const definitions = SKILLS_BY_ROLE[form.value.role]
  if (!definitions) return

  skillLevels.value = {
    ...skillLevels.value,
    [form.value.role]: defaultSkillLevels(definitions)
  }
  skillsError.value = ''
}

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
  if (event.key === 'Escape' && showSubmitConfirm.value) cancelSubmitConfirm()
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

// รับได้หลายไฟล์ ไฟล์ที่ผิดเงื่อนไขหรือเกินจำนวนจะถูกข้ามและแจ้งชื่อไฟล์
function addEvidenceFiles(fileList) {
  const problems = []

  for (const file of Array.from(fileList || [])) {
    if (evidenceCount.value >= EVIDENCE_MAX_FILES) {
      problems.push(
        t.value.studentExternalActivity.evidenceLimitError.replace('{max}', EVIDENCE_MAX_FILES)
      )
      break
    }

    const problem = fileProblem(file)

    if (problem) {
      problems.push(`${file.name}: ${problem}`)
      continue
    }

    newEvidenceFiles.value = [...newEvidenceFiles.value, file]
  }

  formError.value = problems.join(' · ')
}

function handleFileChange(event) {
  addEvidenceFiles(event.target.files)
  // ให้เลือกไฟล์เดิมซ้ำได้หลังลบออก
  event.target.value = ''
}

function handleDrop(event) {
  isDragging.value = false
  addEvidenceFiles(event.dataTransfer?.files)
}

function removeNewEvidence(index) {
  newEvidenceFiles.value = newEvidenceFiles.value.filter((_, itemIndex) => itemIndex !== index)
}

function removeExistingEvidence(id) {
  removedEvidenceIds.value = [...removedEvidenceIds.value, id]
}

/* =========================
   Submit
========================= */
function validateForm() {
  if (!validHours(form.value.activity_hours)) return t.value.activityHours.invalid
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

  if (evidenceCount.value === 0) {
    return t.value.studentExternalActivity.evidenceRequiredError
  }

  if (evidenceCount.value > EVIDENCE_MAX_FILES) {
    return t.value.studentExternalActivity.evidenceLimitError.replace('{max}', EVIDENCE_MAX_FILES)
  }

  for (const file of newEvidenceFiles.value) {
    const problem = fileProblem(file)
    if (problem) return `${file.name}: ${problem}`
  }

  return ''
}

function errorDetail(data, fallback) {
  if (Array.isArray(data?.detail)) {
    return data.detail.map((item) => item.msg || String(item)).join(', ')
  }

  return data?.detail || fallback
}

// ล้างทั้งฟอร์มกลับเป็นค่าเริ่มต้น (ทักษะกลับไป level 3) และออกจากโหมดแก้ไข
function resetForm() {
  form.value = emptyForm()
  applyCategoryFromValue('')
  skillLevels.value = emptySkillLevels()
  newEvidenceFiles.value = []
  existingEvidence.value = []
  removedEvidenceIds.value = []
  editingId.value = null
  formError.value = ''
  skillsError.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

async function addAnotherActivity() {
  submitResult.value = null
  resetForm()

  // มาจากลิงก์แก้ไข: ล้าง ?edit ออก ไม่งั้น refresh แล้วจะพยายามโหลดรายการเดิม
  if (route.query.edit) await router.replace({ query: {} })

  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function viewSubmissions() {
  submitResult.value = null
  router.push({ path: '/student/activities', query: { tab: 'submissions' } })
}

async function submitActivity() {
  if (submitting.value) return

  formError.value = validateForm()
  // ยังไม่เลือกบทบาท: error "กรอกช่องที่มี * ให้ครบ" ครอบคลุมแล้ว ไม่ต้องเตือนเรื่องทักษะซ้ำ
  skillsError.value = hasRole.value && relatedSkillCount.value === 0
    ? t.value.studentExternalActivity.skillRequiredError
    : ''

  // ถ้าผิดแค่ช่องทักษะ เลื่อนจอไปที่ช่องนั้น (error อื่นแสดงอยู่ข้างปุ่มส่งแล้ว)
  if (skillsError.value && !formError.value) {
    await nextTick()
    skillsField.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    skillsField.value?.querySelector('button')?.focus({ preventScroll: true })
  }

  if (formError.value || skillsError.value) return

  showSubmitConfirm.value = true
  await nextTick()
  submitConfirmButton.value?.focus()
}

function cancelSubmitConfirm() {
  if (submitting.value) return
  showSubmitConfirm.value = false
}

async function confirmSubmit() {
  if (submitting.value) return

  const body = new FormData()

  for (const [key, value] of Object.entries(form.value)) {
    body.append(key, typeof value === 'string' ? value.trim() : value)
  }

  // ส่งเฉพาะชุด Skill ของ role ที่เลือก
  body.append('skills', JSON.stringify(activeSkillLevels.value))

  // แนบเฉพาะไฟล์ใหม่ ไฟล์เดิมที่ไม่ได้ลบ backend ใช้ต่อเอง
  for (const file of newEvidenceFiles.value) {
    body.append('evidence', file)
  }

  for (const id of removedEvidenceIds.value) {
    body.append('remove_evidence_ids', String(id))
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

    const resubmit = Boolean(editingId.value)
    showSubmitConfirm.value = false
    resetForm()
    submitResult.value = { resubmit, title: data.title }
    await nextTick()
    submitResultPrimary.value?.focus()
  } catch (error) {
    // ส่งไม่สำเร็จ: ปิด popup ยืนยัน กลับไปที่ฟอร์ม (ข้อมูลยังอยู่) แสดง error ข้างปุ่มส่ง
    showSubmitConfirm.value = false
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

    <form class="page-grid" :class="{ 'no-role': !hasRole }" novalidate @submit.prevent="submitActivity">
      <!-- LEFT: activity details + evidence -->
      <div class="form-column form-main">
        <section class="card">
          <div class="card-heading">
            <span class="heading-icon"><Info :size="16" /></span>
            <h2>{{ t.studentExternalActivity.activityDetailsHeading }}</h2>
          </div>

          <div class="form-grid">
            <label class="field"><span>{{ t.activityHours.label }}</span><input v-model="form.activity_hours" name="activity_hours" type="number" min="0.01" max="99999999.99" step="0.01" required /></label>
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
              <select v-model="form.role" name="role" @change="onRoleChange">
                <option disabled value="">{{ t.studentExternalActivity.selectRoleOption }}</option>
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
      </div>

      <!-- RIGHT: ทักษะที่ได้รับ (ติดขอบบนตอนเลื่อน) ปรับระดับใน popup -->
      <Transition name="side-panel">
      <aside v-if="hasRole" class="form-column form-side">
        <section
          ref="skillsField"
          class="card skills-panel"
          :class="{ invalid: skillsError }"
        >
          <div class="card-heading">
            <span class="heading-icon accent"><Sparkles :size="16" /></span>
            <div class="skills-panel-title">
              <h2 id="skills-field-label">{{ t.studentExternalActivity.skillsFieldLabel }} <b>*</b></h2>
              <small>{{ roleSkillLabel }} · {{ t.studentExternalActivity.skillsFieldHint }}</small>
            </div>
          </div>

          <!-- เนื้อหาเปลี่ยนตามบทบาท: key ตาม role ให้ fade ทุกครั้งที่สลับ -->
          <Transition name="skills-swap" mode="out-in">
          <div :key="form.role" class="skills-role-content">
          <div class="skills-panel-summary" :class="{ empty: relatedSkillCount === 0 }">
            <strong>{{ skillsSummaryText(relatedSkillCount) }}</strong>
            <span>{{ relatedSkillCount }} / {{ skillDefinitions.length }}</span>
          </div>

          <ul class="skill-overview">
            <li
              v-for="skill in skillDefinitions"
              :key="skill.key"
              :class="{ 'not-related': activeSkillLevels[skill.key] == null }"
            >
              <span class="skill-overview-icon"><component :is="skill.icon" :size="16" /></span>
              <span class="skill-overview-name">
                <strong>{{ skill.label }}</strong>
                <small>{{ skill.description }}</small>
              </span>
              <span class="skill-overview-level">
                <template v-if="activeSkillLevels[skill.key] != null">
                  <span class="level-dots" aria-hidden="true">
                    <i v-for="dot in 5" :key="dot" :class="{ on: dot <= activeSkillLevels[skill.key] }"></i>
                  </span>
                  <small>{{ t.skillLevelEditor.level }} {{ activeSkillLevels[skill.key] }}</small>
                </template>
                <small v-else>{{ t.skillLevelEditor.notApplicable }}</small>
              </span>
            </li>
          </ul>

          <button
            type="button"
            class="view-skills-button"
            aria-labelledby="skills-field-label"
            aria-haspopup="dialog"
            @click="openSkillsModal"
          >
            <SlidersHorizontal :size="16" />
            {{ t.studentExternalActivity.adjustSkillsButton }}
          </button>
          </div>
          </Transition>

          <p v-if="skillsError" class="field-error" role="alert">
            <TriangleAlert :size="14" />
            {{ skillsError }}
          </p>
        </section>
      </aside>
      </Transition>

      <!-- หลักฐาน: เต็มความกว้างใต้สองคอลัมน์ -->
      <section class="card evidence-card">
        <div class="card-heading">
          <span class="heading-icon green"><ImagePlus :size="16" /></span>
          <h2>{{ t.studentExternalActivity.evidenceCardHeading }}</h2>
        </div>

        <div class="evidence-section">
          <div
            v-if="evidenceCount < EVIDENCE_MAX_FILES"
            class="upload-box"
            :class="{ dragging: isDragging }"
            @click="openFilePicker"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
          >
            <input
              ref="fileInput"
              class="file-input"
              type="file"
              name="evidence"
              multiple
              accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
              @click.stop
              @change="handleFileChange"
            />

            <span class="upload-icon large"><ImagePlus :size="26" /></span>
            <strong>{{ t.studentExternalActivity.uploadEvidenceLabel }} <b>*</b></strong>
            <p>{{ t.studentExternalActivity.uploadEvidenceHint.replace('{max}', EVIDENCE_MAX_FILES) }}</p>
            <button type="button" class="link-button" @click.stop="openFilePicker">
              {{
                evidenceCount
                  ? t.studentExternalActivity.addMoreFilesButton
                  : t.studentExternalActivity.chooseFileButton
              }}
            </button>
          </div>

          <p v-else class="evidence-limit-note">
            <Info :size="14" />
            {{ t.studentExternalActivity.evidenceLimitReached.replace('{max}', EVIDENCE_MAX_FILES) }}
          </p>

          <div v-if="evidenceCount" class="evidence-list-header">
            <strong>{{ t.studentExternalActivity.evidenceListHeading }}</strong>
            <span>
              {{
                t.studentExternalActivity.evidenceCountLabel
                  .replace('{count}', evidenceCount)
                  .replace('{max}', EVIDENCE_MAX_FILES)
              }}
            </span>
          </div>

          <ul v-if="evidenceCount" class="evidence-list">
            <li
              v-for="item in keptExistingEvidence"
              :key="`existing-${item.id}`"
              class="selected-file"
            >
              <span class="upload-icon"><Paperclip :size="18" /></span>
              <div>
                <strong>{{ item.original_name }}</strong>
                <small>{{ formatFileSize(item.size) }} · {{ t.studentExternalActivity.currentEvidenceLabel }}</small>
              </div>
              <button
                type="button"
                class="remove-file"
                :aria-label="`${t.studentExternalActivity.removeFileAriaLabel} ${item.original_name}`"
                @click="removeExistingEvidence(item.id)"
              >
                <X :size="15" />
              </button>
            </li>

            <li
              v-for="(file, index) in newEvidenceFiles"
              :key="`new-${index}-${file.name}-${file.size}`"
              class="selected-file"
            >
              <span class="upload-icon"><Paperclip :size="18" /></span>
              <div>
                <strong>{{ file.name }}</strong>
                <small>{{ formatFileSize(file.size) }} · {{ t.studentExternalActivity.newEvidenceLabel }}</small>
              </div>
              <button
                type="button"
                class="remove-file"
                :aria-label="`${t.studentExternalActivity.removeFileAriaLabel} ${file.name}`"
                @click="removeNewEvidence(index)"
              >
                <X :size="15" />
              </button>
            </li>
          </ul>
        </div>
      </section>

      <!-- ข้อความ + ปุ่มส่ง -->
      <div class="form-column form-footer">
        <div v-if="formError" class="alert error" role="alert">
          <TriangleAlert :size="16" />
          {{ formError }}
        </div>

        <div class="form-actions">
          <button type="submit" class="primary-button" :disabled="submitting">
            <Send :size="18" />
            {{ editingId ? t.studentExternalActivity.resubmitButton : t.studentExternalActivity.submitButton }}
          </button>
        </div>
      </div>

    </form>

    <!-- ยืนยันก่อนส่ง: ไม่มี @click.self คลิกนอกกรอบจึงไม่ปิด -->
    <div v-if="showSubmitConfirm" class="modal-backdrop" data-testid="submit-confirm">
      <div
        class="submit-result-modal"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="submit-confirm-title"
        aria-describedby="submit-confirm-message"
      >
        <span class="submit-result-icon confirm" aria-hidden="true">
          <Send :size="34" />
        </span>

        <h2 id="submit-confirm-title">
          {{
            editingId
              ? t.studentExternalActivity.confirmResubmitTitle
              : t.studentExternalActivity.confirmSubmitTitle
          }}
        </h2>

        <p id="submit-confirm-message">
          {{
            (editingId
              ? t.studentExternalActivity.confirmResubmitMessage
              : t.studentExternalActivity.confirmSubmitMessage
            ).replace('{name}', form.title.trim())
          }}
        </p>

        <div class="submit-result-actions">
          <button
            type="button"
            class="modal-secondary-button"
            :disabled="submitting"
            @click="cancelSubmitConfirm"
          >
            {{ t.studentExternalActivity.confirmCancelButton }}
          </button>
          <button
            ref="submitConfirmButton"
            type="button"
            class="modal-confirm-button"
            :disabled="submitting"
            data-testid="submit-confirm-button"
            @click="confirmSubmit"
          >
            <LoaderCircle v-if="submitting" class="spin" :size="17" />
            {{
              submitting
                ? (editingId ? t.studentExternalActivity.resubmittingButton : t.studentExternalActivity.submittingButton)
                : t.studentExternalActivity.confirmSubmitButton
            }}
          </button>
        </div>
      </div>
    </div>

    <!-- ส่งสำเร็จ: ไม่มี @click.self คลิกนอกกรอบจึงไม่ปิด ต้องเลือกปุ่มใดปุ่มหนึ่ง -->
    <div v-if="submitResult" class="modal-backdrop" data-testid="submit-result">
      <div
        class="submit-result-modal"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="submit-result-title"
        aria-describedby="submit-result-message"
      >
        <span class="submit-result-icon" aria-hidden="true">
          <CheckCircle2 :size="40" />
        </span>

        <h2 id="submit-result-title">
          {{
            submitResult.resubmit
              ? t.studentExternalActivity.resubmitResultTitle
              : t.studentExternalActivity.submitResultTitle
          }}
        </h2>

        <p id="submit-result-message">
          {{
            (submitResult.resubmit
              ? t.studentExternalActivity.resubmitResultMessage
              : t.studentExternalActivity.submitResultMessage
            ).replace('{name}', submitResult.title)
          }}
        </p>

        <div class="submit-result-actions">
          <button type="button" class="modal-secondary-button" @click="addAnotherActivity">
            {{ t.studentExternalActivity.addAnotherActivityButton }}
          </button>
          <button
            ref="submitResultPrimary"
            type="button"
            class="modal-confirm-button"
            @click="viewSubmissions"
          >
            {{ t.studentExternalActivity.viewSubmissionsButton }}
          </button>
        </div>
      </div>
    </div>

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
  padding: 32px;
  background: #f5f7fb;
  color: #1c2434;
}

.page-title {
  max-width: 1280px;
  margin: 0 auto 24px;
}

.page-title h1 {
  margin: 0;
  color: #1d2f6f;
  font-size: 28px;
  font-weight: 700;
}

.page-title p {
  margin: 6px 0 0;
  color: #7e8796;
  font-size: var(--fs-body);
}

.page-grid {
  /* ฟอร์ม ~60% | ทักษะ ~40% แล้วหลักฐาน + ปุ่มส่งเต็มแถวด้านล่าง */
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
  grid-template-areas:
    "main side"
    "evidence evidence"
    "footer footer";
  align-items: start;
  gap: 24px;
}

.form-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.form-main { grid-area: main; }
/* column ยืดเท่าแถวฟอร์ม ให้ panel ติดขอบบนได้แค่ในแถวนี้ ไม่เลื่อนทับหลักฐาน */
.form-side {
  grid-area: side;
  align-self: stretch;
}
.form-side .skills-panel {
  position: sticky;
  top: 24px;
}
.evidence-card { grid-area: evidence; }
.form-footer { grid-area: footer; }

.card {
  padding: 26px 28px;
  border: 1px solid #e6eaf1;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(29, 47, 111, 0.04), 0 6px 20px rgba(29, 47, 111, 0.04);
}

.card-heading {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-heading h2 {
  margin: 0;
  color: #1c2434;
  font-size: 20px;
  font-weight: 700;
}

.heading-icon {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border-radius: 10px;
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
  font-size: var(--fs-small);
}

.form-grid {
  margin-top: 22px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px 18px;
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
  font-size: var(--fs-small);
}

.field-error.full {
  grid-column: 1 / -1;
}

.field > span {
  color: #1c2434;
  font-size: var(--fs-small);
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
  border-radius: 10px;
  outline: none;
  background: #fff;
  color: #1c2434;
  font: inherit;
  font-size: var(--fs-body);
  box-sizing: border-box;
}

.field input,
.field select {
  height: 46px;
  padding: 0 14px;
}

.field textarea {
  min-height: 120px;
  padding: 12px 14px;
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
  max-width: 760px;
  width: 100%;
  margin: 0 auto;
  padding: 36px 24px;
  border: 2px dashed #cdbef0;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  background: linear-gradient(180deg, #fbf9ff 0%, #f5f0ff 100%);
  text-align: center;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.upload-box:hover {
  border-color: #9b5de5;
}
.upload-box.dragging {
  border-color: #7e10c6;
  background: #f7f0ff;
}

.evidence-section {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.evidence-limit-note {
  margin: 0;
  padding: 10px 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  background: #eef1ff;
  color: #1d2f6f;
  font-size: var(--fs-small);
}

.evidence-list-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  font-size: var(--fs-small);
}

.evidence-list-header strong {
  color: #1c2434;
}

.evidence-list-header span {
  color: #7e8796;
}

.evidence-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.evidence-list .selected-file {
  padding: 10px 12px;
  border: 1px solid #e6eaf1;
  border-radius: 10px;
  background: #fff;
  box-sizing: border-box;
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

.upload-icon.large {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: #fff;
  color: #7e10c6;
  box-shadow: 0 4px 12px rgba(126, 16, 198, 0.12);
}

.upload-box > strong {
  margin-top: 4px;
  color: #1d2f6f;
  font-size: var(--fs-body);
}

.upload-box > p {
  margin: 0;
  color: #4a5567;
  font-size: var(--fs-small);
}

.link-button {
  margin-top: 6px;
  padding: 9px 20px;
  border: 1px solid #d9c6f3;
  border-radius: 999px;
  background: #fff;
  color: #7e10c6;
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 700;
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
  font-size: var(--fs-body);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-file small {
  color: #7e8796;
  font-size: var(--fs-small);
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
  font-size: var(--fs-small);
}

.alert.error {
  background: #fdeaea;
  color: #b42318;
}

.form-actions {
  display: flex;
  justify-content: center;
  padding: 8px 0 12px;
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
  font-size: var(--fs-body);
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 6px 14px rgba(126, 16, 198, 0.2);
}

.form-actions .primary-button {
  width: min(100%, 420px);
  min-height: 56px;
  gap: 10px;
  border-radius: 14px;
  font-size: var(--fs-lead);
  box-shadow: 0 10px 24px rgba(126, 16, 198, 0.28);
  transition: background-color 0.15s ease, transform 0.15s ease;
}

.form-actions .primary-button:not(:disabled):hover {
  background: #6a0da8;
  transform: translateY(-1px);
}

.form-footer .alert {
  width: 100%;
  max-width: 760px;
  margin: 0 auto;
  box-sizing: border-box;
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

/* =========================
   Skills panel (ขวา)
========================= */
.skills-panel {
  border-color: #e3d6f7;
  background: linear-gradient(180deg, #fcfaff 0%, #fff 140px);
  box-shadow: 0 1px 2px rgba(126, 16, 198, 0.05), 0 10px 28px rgba(126, 16, 198, 0.08);
}

.skills-panel::before {
  content: '';
  display: block;
  height: 4px;
  margin: -26px -28px 22px;
  border-radius: 16px 16px 0 0;
  background: linear-gradient(90deg, #7e10c6, #b76cf0);
}

.skills-panel.invalid {
  border-color: #e0453a;
  box-shadow: 0 0 0 3px rgba(224, 69, 58, 0.1);
}

.heading-icon.accent {
  background: #f1e6ff;
  color: #7e10c6;
}

.skills-panel .card-heading {
  align-items: flex-start;
}

.skills-panel-title {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.skills-panel-title h2 {
  margin: 0;
  color: #1c2434;
  font-size: 20px;
  font-weight: 700;
  line-height: 34px;
}

.skills-panel-title h2 b {
  color: #e0453a;
}

.skills-panel-title small {
  color: #7e8796;
  font-size: var(--fs-small);
}

.skills-panel-summary {
  margin: 20px 0 14px;
  padding: 12px 16px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: #f5eeff;
  color: #5b0f96;
}

.skills-panel-summary strong {
  font-size: var(--fs-body);
}

.skills-panel-summary span {
  font-size: var(--fs-small);
  font-weight: 700;
}

.skills-panel-summary.empty {
  background: #fff5e0;
  color: #8a5a00;
}

.skill-overview {
  margin: 0 0 18px;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
}

.skill-overview li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 0;
}

.skill-overview li + li {
  border-top: 1px solid #f0f2f6;
}

.skill-overview-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: #f1f3f8;
  color: #4a5567;
}

.skill-overview-name {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.skill-overview-name strong {
  color: #1c2434;
  font-size: var(--fs-small);
  font-weight: 600;
}

.skill-overview-name small {
  color: #8a93a3;
  font-size: var(--fs-caption);
}

.skill-overview-level {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 3px;
}

.skill-overview-level small {
  color: #7e10c6;
  font-size: var(--fs-caption);
  font-weight: 700;
}

.level-dots {
  display: flex;
  gap: 3px;
}

.level-dots i {
  width: 12px;
  height: 6px;
  border-radius: 3px;
  background: #e6e9f0;
}

.level-dots i.on {
  background: #7e10c6;
}

.skill-overview li.not-related .skill-overview-icon,
.skill-overview li.not-related .skill-overview-name {
  opacity: 0.5;
}

.skill-overview li.not-related .skill-overview-level small {
  color: #a3aab6;
}

.skills-panel .field-error {
  margin: 12px 0 0;
}

.view-skills-button {
  width: 100%;
  min-height: 46px;
  padding: 0 16px;
  border: 1.5px solid #d9c6f3;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #f7f0ff;
  color: #7e10c6;
  font: inherit;
  font-size: var(--fs-body);
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

/* จอกลาง: เหลือคอลัมน์เดียว ลำดับ ฟอร์ม -> ทักษะ -> หลักฐาน -> ปุ่มส่ง */
@media (max-width: 1180px) {
  .page-grid {
    max-width: 860px;
    grid-template-columns: minmax(0, 1fr);
    grid-template-areas:
      "main"
      "side"
      "evidence"
      "footer";
    gap: 20px;
  }

  .page-title {
    max-width: 860px;
  }

  .form-side .skills-panel {
    position: static;
  }
}

@media (max-width: 640px) {
  .external-page {
    padding: 20px 16px;
  }

  .page-title h1 {
    font-size: 24px;
  }

  .card {
    padding: 20px 16px;
  }

  .skills-panel::before {
    margin: -20px -16px 18px;
  }

  .form-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .evidence-list {
    grid-template-columns: 1fr;
  }

  .upload-box {
    padding: 28px 16px;
  }

  .form-actions .primary-button {
    width: 100%;
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
  font-size: var(--fs-small);
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
  font-size: var(--fs-small);
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
  font-size: 20px;
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
  font-size: var(--fs-small);
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
  font-size: var(--fs-small);
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

/* =========================
   Submit result modal
========================= */
.submit-result-modal {
  width: min(440px, 100%);
  padding: 32px 28px 24px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #fff;
  box-shadow: 0 24px 65px rgba(15, 23, 42, 0.2);
  text-align: center;
  animation: submit-result-pop 0.18s ease-out;
}

.submit-result-icon {
  width: 72px;
  height: 72px;
  margin-bottom: 16px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #e6f8ed;
  color: #16a34a;
}

.submit-result-icon.confirm {
  background: #f3e8ff;
  color: #7e10c6;
}

.submit-result-actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.submit-result-actions .modal-confirm-button {
  gap: 8px;
}

.submit-result-modal h2 {
  margin: 0 0 8px;
  color: #1b283d;
  font-size: 20px;
}

.submit-result-modal p {
  margin: 0 0 24px;
  color: #526279;
  font-size: var(--fs-body);
  line-height: 1.6;
  overflow-wrap: anywhere;
}

.submit-result-actions {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.submit-result-actions button {
  min-height: 46px;
  font-size: var(--fs-body);
}

.submit-result-actions .modal-secondary-button:hover {
  background: #f7f8fb;
}

.submit-result-actions button:focus-visible {
  outline: 3px solid rgba(126, 16, 198, 0.3);
  outline-offset: 2px;
}

@keyframes submit-result-pop {
  from { opacity: 0; transform: scale(0.94); }
  to { opacity: 1; transform: scale(1); }
}

@media (max-width: 420px) {
  .submit-result-actions {
    grid-template-columns: 1fr;
  }

  .submit-result-actions .modal-confirm-button {
    order: -1;
  }
}

/* ยังไม่เลือกบทบาท: คอลัมน์เดียวทุกขนาดจอ (specificity สูงกว่า .page-grid ใน @media) */
.page-grid.no-role {
  grid-template-columns: minmax(0, 1fr);
  grid-template-areas:
    "main"
    "evidence"
    "footer";
}

/* แผงทักษะเลื่อนเข้ามาจากขวาเมื่อเลือกบทบาท / เนื้อหา fade ตอนสลับบทบาท */
.side-panel-enter-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.side-panel-enter-from {
  opacity: 0;
  transform: translateX(16px);
}

.skills-swap-enter-active,
.skills-swap-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.skills-swap-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.skills-swap-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (prefers-reduced-motion: reduce) {
  .side-panel-enter-active,
  .skills-swap-enter-active,
  .skills-swap-leave-active {
    transition: none;
  }
}
</style>
