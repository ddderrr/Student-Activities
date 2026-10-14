<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Check,
  CheckCircle2,
  ClipboardList,
  FileText,
  LoaderCircle,
  MapPin,
  UsersRound,
  UserRound
} from 'lucide-vue-next'
import SkillLevelEditor from '../../components/Admin/SkillLevelEditor.vue'
import UnsavedChangesDialog from '../../components/common/UnsavedChangesDialog.vue'
import { useUnsavedChanges } from '../../composables/useUnsavedChanges'
import {
  PARTICIPANT_SKILLS,
  STAFF_SKILLS,
  defaultSkillLevels
} from '../../constants/activitySkills'
import { useLanguage } from '../../composables/useLanguage'
import { adminFetch } from '../../constants/currentAdmin'

import { validHours } from '../../utils/activityHours'
import { API_BASE } from '../../config/api'
const router = useRouter()
const { t } = useLanguage()

const currentStep = ref(1)
const skillTarget = ref('staff')
const submitting = ref(false)
const errorMessage = ref('')

const OTHER_ACTIVITY_TYPE = 'อื่นๆ (โปรดระบุ)'

const activityTypes = [
  'กิจกรรมวิชาการ',
  'สัมมนา',
  'อบรม / Workshop',
  'จิตอาสา',
  'กิจกรรมพัฒนาทักษะ',
  'กิจกรรมนันทนาการ',
  OTHER_ACTIVITY_TYPE
]

const customActivityType = ref('')

const form = ref({
  activity_type: '',
  name: '',
  activity_hours: '',
  start_at: '',
  end_at: '',
  department: '',
  responsible_person: '',
  advisor: '',
  location: '',
  description: ''
})

const resolvedActivityType = computed(() => {
  if (form.value.activity_type === OTHER_ACTIVITY_TYPE) {
    return customActivityType.value.trim()
  }

  return form.value.activity_type.trim()
})

const staffSkills = ref(defaultSkillLevels(STAFF_SKILLS))
const participantSkills = ref(defaultSkillLevels(PARTICIPANT_SKILLS))

// ออกจากหน้าระหว่างกรอก: ถามก่อนละทิ้ง (เทียบกับค่าตอนเปิดหน้า)
const formSnapshot = () => JSON.stringify([form.value, customActivityType.value, staffSkills.value, participantSkills.value])
const initialFormSnapshot = formSnapshot()
const unsaved = useUnsavedChanges(() => formSnapshot() !== initialFormSnapshot)

const activeSkillDefinitions = computed(() =>
  skillTarget.value === 'staff'
    ? STAFF_SKILLS
    : PARTICIPANT_SKILLS
)

const activeSkills = computed({
  get: () =>
    skillTarget.value === 'staff'
      ? staffSkills.value
      : participantSkills.value,
  set: (value) => {
    if (skillTarget.value === 'staff') staffSkills.value = value
    else participantSkills.value = value
  }
})

const openCalendar = ref(null)
const calendarCursor = ref(new Date())

const weekDays = computed(() => t.value.adminCreateActivity.weekDays)

const calendarTitle = computed(() =>
  new Intl.DateTimeFormat('th-TH-u-ca-gregory', {
    month: 'long',
    year: 'numeric'
  }).format(calendarCursor.value)
)

const calendarDays = computed(() => {
  const year = calendarCursor.value.getFullYear()
  const month = calendarCursor.value.getMonth()
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
      key: toDateKey(date),
      day: date.getDate(),
      outside: date.getMonth() !== month
    }
  })
})

function toDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function parseDateKey(value) {
  if (!value) return null

  const [year, month, day] = value.split('-').map(Number)
  if (!year || !month || !day) return null

  return new Date(year, month - 1, day)
}

function formatDisplayDate(value) {
  const date = parseDateKey(value)
  if (!date) return t.value.adminCreateActivity.selectDatePlaceholder

  return new Intl.DateTimeFormat('th-TH-u-ca-gregory', {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  }).format(date)
}

function openCalendarPicker(type) {
  openCalendar.value = type

  const selectedValue =
    type === 'start'
      ? form.value.start_at
      : form.value.end_at || form.value.start_at

  calendarCursor.value = parseDateKey(selectedValue) || new Date()
}

function closeCalendar() {
  openCalendar.value = null
}

function changeMonth(offset) {
  const current = calendarCursor.value
  calendarCursor.value = new Date(
    current.getFullYear(),
    current.getMonth() + offset,
    1
  )
}

function isCalendarDateDisabled(day) {
  if (openCalendar.value !== 'end' || !form.value.start_at) return false
  return day.key < form.value.start_at
}

function isSelectedCalendarDate(day) {
  const selected =
    openCalendar.value === 'start'
      ? form.value.start_at
      : form.value.end_at

  return day.key === selected
}

function isToday(day) {
  return day.key === toDateKey(new Date())
}

function selectCalendarDate(day) {
  if (isCalendarDateDisabled(day)) return

  if (openCalendar.value === 'start') {
    form.value.start_at = day.key

    // ถ้าวันสิ้นสุดเดิมอยู่ก่อนวันเริ่มต้นใหม่ ให้ขยับมาวันเดียวกันอัตโนมัติ
    if (form.value.end_at && form.value.end_at < day.key) {
      form.value.end_at = day.key
    }
  } else if (openCalendar.value === 'end') {
    form.value.end_at = day.key
  }

  closeCalendar()
}

function selectToday() {
  const today = { key: toDateKey(new Date()) }
  if (isCalendarDateDisabled(today)) return
  selectCalendarDate(today)
}

function goBack() {
  if (currentStep.value === 2) {
    currentStep.value = 1
    errorMessage.value = ''
    return
  }

  router.push('/admin/activities')
}

function validateStepOne() {
  if (!validHours(form.value.activity_hours)) {
    errorMessage.value = t.value.activityHours.invalid
    return false
  }
  errorMessage.value = ''

  if (
    form.value.activity_type === OTHER_ACTIVITY_TYPE &&
    !customActivityType.value.trim()
  ) {
    errorMessage.value = t.value.adminCreateActivity.validateOtherActivityTypeRequired
    return false
  }

  const required = [
    resolvedActivityType.value,
    form.value.name,
    form.value.start_at,
    form.value.end_at,
    form.value.responsible_person,
    form.value.location
  ]

  if (required.some((value) => !String(value || '').trim())) {
    errorMessage.value = t.value.adminCreateActivity.validateRequiredFields
    return false
  }

  if (form.value.end_at < form.value.start_at) {
    errorMessage.value = t.value.adminCreateActivity.validateEndDateBeforeStart
    return false
  }

  return true
}

function nextStep() {
  if (!validateStepOne()) return

  currentStep.value = 2
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function createActivity() {
  if (!validateStepOne()) return
  if (submitting.value) return

  submitting.value = true
  errorMessage.value = ''

  try {
    let response

    try {
      response = await adminFetch(`${API_BASE}/api/activities`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...form.value,
          activity_type: resolvedActivityType.value,
          // Backend ยังรับ datetime อยู่ จึงกำหนดเวลาให้อัตโนมัติ
          // เพื่อให้ผู้ใช้เลือกเฉพาะวันที่ และยังรองรับกิจกรรมที่จบวันเดียวกันได้
          start_at: `${form.value.start_at}T00:00:00`,
          end_at: `${form.value.end_at}T23:59:59`,
          staff_skills: staffSkills.value,
          participant_skills: participantSkills.value
        })
      })
    } catch (networkError) {
      console.error('Create activity network error:', networkError)

      throw new Error(
        `${t.value.adminCreateActivity.backendConnectionError} (${API_BASE}) ${t.value.adminCreateActivity.backendConnectionErrorHint}`
      )
    }

    const rawText = await response.text()

    let data = {}

    if (rawText) {
      try {
        data = JSON.parse(rawText)
      } catch {
        data = { detail: rawText }
      }
    }

    if (!response.ok) {
      const detail = Array.isArray(data.detail)
        ? data.detail.map((item) => item.msg || String(item)).join(', ')
        : data.detail

      throw new Error(detail || t.value.adminCreateActivity.createActivityError)
    }

    unsaved.allowLeave()
    router.push('/admin/activities')
  } catch (error) {
    console.error('Create activity error:', error)

    errorMessage.value =
      error.message || t.value.adminCreateActivity.createActivityError
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="create-page" @click="closeCalendar">
    <div class="page-shell">
      <header class="hero-card">
        <div>
          <h1>{{ t.adminCreateActivity.pageTitle }}</h1>
        </div>

        <div class="steps">
          <div class="step" :class="{ active: currentStep >= 1 }">
            <span>1</span>
            <div>
              <strong>{{ t.adminCreateActivity.stepActivityInfoTitle }}</strong>
              <small>{{ t.adminCreateActivity.stepActivityInfoSubtitle }}</small>
            </div>
          </div>

          <div class="step-connector" :class="{ active: currentStep === 2 }"></div>

          <div class="step" :class="{ active: currentStep === 2 }">
            <span>2</span>
            <div>
              <strong>{{ t.adminCreateActivity.stepAttachSkillsTitle }}</strong>
              <small>{{ t.adminCreateActivity.stepAttachSkillsSubtitle }}</small>
            </div>
          </div>
        </div>
      </header>

      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>

      <!-- STEP 1 -->
      <template v-if="currentStep === 1">
        <div class="content-layout">
          <main class="form-column">
            <section class="form-card">
              <div class="section-heading">
                <div class="section-icon"><ClipboardList :size="20" /></div>
                <div>
                  <h2>{{ t.adminCreateActivity.basicInfoTitle }}</h2>
                  <p>{{ t.adminCreateActivity.basicInfoSubtitle }}</p>
                </div>
              </div>

              <div class="form-grid">
                <label class="field"><span>{{ t.activityHours.label }} <b>*</b></span><input v-model="form.activity_hours" name="activity_hours" type="number" min="0.01" max="99999999.99" step="0.01" required /></label>
                <label class="field">
                  <span>{{ t.adminCreateActivity.activityTypeLabel }} <b>*</b></span>
                  <select v-model="form.activity_type">
                    <option disabled value="">{{ t.adminCreateActivity.selectActivityTypePlaceholder }}</option>
                    <option v-for="type in activityTypes" :key="type" :value="type">
                      {{ type }}
                    </option>
                  </select>

                  <input
                    v-if="form.activity_type === OTHER_ACTIVITY_TYPE"
                    v-model="customActivityType"
                    class="other-activity-input"
                    type="text"
                    :placeholder="t.adminCreateActivity.customActivityTypePlaceholder"
                  />
                </label>

                <label class="field">
                  <span>{{ t.adminCreateActivity.activityNameLabel }} <b>*</b></span>
                  <input
                    v-model="form.name"
                    type="text"
                    :placeholder="t.adminCreateActivity.activityNamePlaceholder"
                  />
                </label>
              </div>
            </section>

            <section class="form-card schedule-card">
              <div class="section-heading">
                <div class="section-icon"><CalendarDays :size="20" /></div>
                <div>
                  <h2>{{ t.adminCreateActivity.scheduleTitle }}</h2>
                  <p>{{ t.adminCreateActivity.scheduleSubtitle }}</p>
                </div>
              </div>

              <div class="form-grid date-grid">
                <div class="field date-field">
                  <span>{{ t.adminCreateActivity.startDateLabel }} <b>*</b></span>
                  <div class="date-picker" @click.stop>
                    <button
                      type="button"
                      class="date-trigger"
                      :class="{ selected: form.start_at }"
                      @click="openCalendarPicker('start')"
                    >
                      <span class="date-trigger-icon"><CalendarDays :size="18" /></span>
                      <span class="date-trigger-text">
                        <small>{{ t.adminCreateActivity.startDateBadge }}</small>
                        <strong>{{ formatDisplayDate(form.start_at) }}</strong>
                      </span>
                    </button>

                    <div v-if="openCalendar === 'start'" class="calendar-popover">
                      <div class="calendar-header">
                        <button type="button" class="calendar-nav" @click="changeMonth(-1)">
                          <ChevronLeft :size="18" />
                        </button>
                        <div>
                          <small>{{ t.adminCreateActivity.calendarHeaderSelectStart }}</small>
                          <strong>{{ calendarTitle }}</strong>
                        </div>
                        <button type="button" class="calendar-nav" @click="changeMonth(1)">
                          <ChevronRight :size="18" />
                        </button>
                      </div>

                      <div class="calendar-weekdays">
                        <span v-for="dayName in weekDays" :key="dayName">{{ dayName }}</span>
                      </div>

                      <div class="calendar-days">
                        <button
                          v-for="day in calendarDays"
                          :key="day.key"
                          type="button"
                          class="calendar-day"
                          :class="{
                            outside: day.outside,
                            today: isToday(day),
                            selected: isSelectedCalendarDate(day)
                          }"
                          @click="selectCalendarDate(day)"
                        >
                          {{ day.day }}
                        </button>
                      </div>

                      <div class="calendar-footer">
                        <span>{{ t.adminCreateActivity.calendarFooterHintStart }}</span>
                        <button type="button" @click="selectToday">{{ t.adminCreateActivity.todayButton }}</button>
                      </div>
                    </div>
                  </div>

                </div>

                <div class="field date-field">
                  <span>{{ t.adminCreateActivity.endDateLabel }} <b>*</b></span>
                  <div class="date-picker end-picker" @click.stop>
                    <button
                      type="button"
                      class="date-trigger"
                      :class="{ selected: form.end_at }"
                      @click="openCalendarPicker('end')"
                    >
                      <span class="date-trigger-icon"><CalendarDays :size="18" /></span>
                      <span class="date-trigger-text">
                        <small>{{ t.adminCreateActivity.endDateBadge }}</small>
                        <strong>{{ formatDisplayDate(form.end_at) }}</strong>
                      </span>
                    </button>

                    <div v-if="openCalendar === 'end'" class="calendar-popover">
                      <div class="calendar-header">
                        <button type="button" class="calendar-nav" @click="changeMonth(-1)">
                          <ChevronLeft :size="18" />
                        </button>
                        <div>
                          <small>{{ t.adminCreateActivity.calendarHeaderSelectEnd }}</small>
                          <strong>{{ calendarTitle }}</strong>
                        </div>
                        <button type="button" class="calendar-nav" @click="changeMonth(1)">
                          <ChevronRight :size="18" />
                        </button>
                      </div>

                      <div class="calendar-weekdays">
                        <span v-for="dayName in weekDays" :key="dayName">{{ dayName }}</span>
                      </div>

                      <div class="calendar-days">
                        <button
                          v-for="day in calendarDays"
                          :key="day.key"
                          type="button"
                          class="calendar-day"
                          :disabled="isCalendarDateDisabled(day)"
                          :class="{
                            outside: day.outside,
                            today: isToday(day),
                            selected: isSelectedCalendarDate(day),
                            disabled: isCalendarDateDisabled(day)
                          }"
                          @click="selectCalendarDate(day)"
                        >
                          {{ day.day }}
                        </button>
                      </div>

                      <div class="calendar-footer">
                        <span>{{ t.adminCreateActivity.calendarFooterHintEnd }}</span>
                        <button
                          type="button"
                          :disabled="Boolean(form.start_at && toDateKey(new Date()) < form.start_at)"
                          @click="selectToday"
                        >
                          {{ t.adminCreateActivity.todayButton }}
                        </button>
                      </div>
                    </div>
                  </div>

                </div>
              </div>
            </section>

            <section class="form-card">
              <div class="section-heading">
                <div class="section-icon"><Building2 :size="20" /></div>
                <div>
                  <h2>{{ t.adminCreateActivity.orgPersonnelTitle }}</h2>
                  <p>{{ t.adminCreateActivity.orgPersonnelSubtitle }}</p>
                </div>
              </div>

              <div class="form-grid">
                <label class="field">
                  <span>{{ t.adminCreateActivity.departmentLabel }}</span>
                  <input
                    v-model="form.department"
                    type="text"
                    :placeholder="t.adminCreateActivity.departmentPlaceholder"
                  />
                </label>

                <label class="field">
                  <span>{{ t.adminCreateActivity.responsiblePersonLabel }} <b>*</b></span>
                  <div class="input-icon">
                    <UserRound :size="17" />
                    <input
                      v-model="form.responsible_person"
                      type="text"
                      :placeholder="t.adminCreateActivity.responsiblePersonPlaceholder"
                    />
                  </div>
                </label>

                <label class="field">
                  <span>{{ t.adminCreateActivity.advisorLabel }}</span>
                  <div class="input-icon">
                    <UserRound :size="17" />
                    <input
                      v-model="form.advisor"
                      type="text"
                      :placeholder="t.adminCreateActivity.advisorPlaceholder"
                    />
                  </div>
                </label>

                <label class="field">
                  <span>{{ t.adminCreateActivity.locationLabel }} <b>*</b></span>
                  <div class="input-icon">
                    <MapPin :size="17" />
                    <input
                      v-model="form.location"
                      type="text"
                      :placeholder="t.adminCreateActivity.locationPlaceholder"
                    />
                  </div>
                </label>
              </div>
            </section>

            <section class="form-card">
              <div class="section-heading">
                <div class="section-icon"><FileText :size="20" /></div>
                <div>
                  <h2>{{ t.adminCreateActivity.additionalDetailsTitle }}</h2>
                  <p>{{ t.adminCreateActivity.additionalDetailsSubtitle }}</p>
                </div>
              </div>

              <label class="field">
                <span>{{ t.adminCreateActivity.descriptionLabel }}</span>
                <textarea
                  v-model="form.description"
                  rows="6"
                  :placeholder="t.adminCreateActivity.descriptionPlaceholder"
                ></textarea>
              </label>
            </section>
          </main>

          <aside class="tips-column">
            <section class="tips-card">
              <div class="tips-icon"><CheckCircle2 :size="21" /></div>
              <h3>{{ t.adminCreateActivity.tipsTitle }}</h3>
              <p>{{ t.adminCreateActivity.tipsSubtitle }}</p>

              <ul>
                <li><Check :size="14" /> {{ t.adminCreateActivity.tipNameAndType }}</li>
                <li><Check :size="14" /> {{ t.adminCreateActivity.tipDates }}</li>
                <li><Check :size="14" /> {{ t.adminCreateActivity.responsiblePersonLabel }}</li>
                <li><Check :size="14" /> {{ t.adminCreateActivity.tipLocation }}</li>
              </ul>
            </section>
          </aside>
        </div>
      </template>

      <!-- STEP 2 -->
      <template v-else>
        <section class="skills-card">
          <div class="skills-heading">
            <div>
              <h2>{{ t.adminCreateActivity.skillsSectionTitle }}</h2>
              <p>
                  {{
                    skillTarget === 'staff'
                      ? t.adminCreateActivity.skillsForStaffDescription
                      : t.adminCreateActivity.skillsForParticipantDescription
                  }}
                </p>
            </div>

            <div class="skill-target">
              <div class="segmented-control">
                <button
                  :class="{ active: skillTarget === 'staff' }"
                  @click="skillTarget = 'staff'"
                >
                  {{ t.adminCreateActivity.staffLabel }}
                </button>
                <button
                  :class="{ active: skillTarget === 'participant' }"
                  @click="skillTarget = 'participant'"
                >
                  {{ t.adminCreateActivity.participantLabel }}
                </button>
              </div>

              <!-- ยังไม่มีหน้าตั้งค่าสกิล: เตรียมไว้สำหรับกิจกรรมที่มีสกิลนอกเหนือจากชุดมาตรฐาน -->
              <button type="button" class="skill-settings-link">
                {{ t.adminCreateActivity.skillSettingsLink }}
              </button>
            </div>
          </div>

          <SkillLevelEditor
            v-model="activeSkills"
            :definitions="activeSkillDefinitions"
          />
        </section>
      </template>

      <footer class="action-bar">
        <button class="secondary-button" :disabled="submitting" @click="goBack">
          <ArrowLeft :size="17" />
          {{ currentStep === 1 ? t.adminCreateActivity.cancelButton : t.adminCreateActivity.backButton }}
        </button>

        <button
          v-if="currentStep === 1"
          class="primary-button"
          @click="nextStep"
        >
          {{ t.adminCreateActivity.continueButton }}
          <ArrowRight :size="17" />
        </button>

        <button
          v-else
          class="primary-button"
          :disabled="submitting"
          @click="createActivity"
        >
          <LoaderCircle v-if="submitting" class="spin" :size="17" />
          <CheckCircle2 v-else :size="17" />
          {{ submitting ? t.adminCreateActivity.creatingButton : t.adminCreateActivity.createActivityButton }}
        </button>
      </footer>
    </div>
  </section>
  <UnsavedChangesDialog
    :open="unsaved.open.value"
    :message="t.unsavedChanges.createActivity"
    @stay="unsaved.stay"
    @leave="unsaved.leave"
  />
</template>

<style scoped>
.create-page {
  min-height: 100vh;
  padding: 30px;
  background:
    radial-gradient(circle at 85% 0%, rgba(134, 19, 189, 0.08), transparent 28%),
    #f7f8fc;
  color: #1e2a3e;
}

.page-shell {
  width: min(1180px, 100%);
  margin: 0 auto;
}

.hero-card {
  margin-bottom: 22px;
  padding: 26px 28px;
  border: 1px solid #e4e9f1;
  border-radius: 20px;
  background: linear-gradient(135deg, #ffffff 0%, #f9f6ff 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 30px;
}

.hero-card h1 {
  margin: 0;
  font-size: 30px;
  color: #1e2a3e;
}

.hero-card p,
.skills-heading p {
  margin: 8px 0 0;
  color: #8290a3;
  font-size: var(--fs-body);
}

.steps {
  display: flex;
  align-items: center;
  gap: 10px;
}

.step {
  display: flex;
  align-items: center;
  gap: 10px;
  opacity: 0.55;
}

.step.active {
  opacity: 1;
}

.step > span {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #edf0f5;
  color: #77859a;
  font-size: var(--fs-small);
  font-weight: 800;
}

.step.active > span {
  background: #8613bd;
  color: #fff;
}

.step strong {
  display: block;
  font-size: var(--fs-small);
}

.step small {
  display: block;
  margin-top: 2px;
  color: #96a2b2;
  font-size: var(--fs-badge);
}

.step-connector {
  width: 42px;
  height: 2px;
  background: #e1e6ed;
}

.step-connector.active {
  background: #a855f7;
}

.error-message {
  margin-bottom: 16px;
  padding: 12px 14px;
  border: 1px solid #f4cccc;
  border-radius: 10px;
  background: #fff2f2;
  color: #bc3b3b;
  font-size: var(--fs-small);
}

.content-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 270px;
  gap: 20px;
}

.form-column {
  display: flex;
  flex-direction: column;
  gap: 17px;
}

.form-card,
.tips-card,
.skills-card {
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.035);
}

.form-card {
  padding: 21px;
}

.section-heading {
  margin-bottom: 18px;
  display: flex;
  align-items: center;
  gap: 11px;
}

.section-icon {
  display: grid;
  place-items: center;
  background: #f5f4f4;
  color: #1769dc;
  width: 39px;
  height: 39px;
  border-radius: 11px;
}

.section-heading h2,
.skills-heading h2 {
  margin: 0;
  font-size: 20px;
  color: #1e2a3e;
}

.section-heading p {
  margin: 3px 0 0;
  color: #657bbc;
  font-size: var(--fs-caption);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 15px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field > span {
  color: #5f6d80;
  font-size: var(--fs-small);
  font-weight: 700;
}

.field b {
  color: #ef4444;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  border: 1px solid #dbe3ed;
  border-radius: 10px;
  outline: none;
  background: #fff;
  color: #34445a;
  font: inherit;
  font-size: var(--fs-body);
  transition: 0.2s;
}

.field input,
.field select {
  height: 43px;
  padding: 0 12px;
}

.other-activity-input {
  margin-top: 4px;
}


.schedule-card {
  overflow: visible;
}

.date-grid {
  align-items: start;
}

.date-field {
  min-width: 0;
}

.date-picker {
  position: relative;
}

.time-field {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.time-field > span {
  color: #5f6d80;
  font-size: var(--fs-small);
  font-weight: 700;
}

.date-trigger {
  width: 100%;
  min-height: 58px;
  padding: 9px 12px;
  border: 1px solid #dbe3ed;
  border-radius: 12px;
  background: linear-gradient(180deg, #ffffff 0%, #fbfcff 100%);
  display: flex;
  align-items: center;
  gap: 11px;
  color: #34445a;
  font-family: inherit;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}

.date-trigger:hover:not(:disabled) {
  border-color: #b8c6db;
}

.date-trigger:disabled {
  background: #f7f8fa;
  color: #aab3bf;
  cursor: not-allowed;
  opacity: 0.72;
}

.date-trigger:focus-visible {
  outline: none;
  border-color: #8f7cf1;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.date-trigger.selected {
  border-color: #c9b9f5;
  background: linear-gradient(180deg, #ffffff 0%, #faf7ff 100%);
}

.date-trigger-icon {
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: #f1ebff;
  color: #7137b8;
}

.date-trigger-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.date-trigger-text small {
  color: #9a86b8;
  font-size: var(--fs-badge);
  font-weight: 800;
  letter-spacing: 0.08em;
}

.date-trigger-text strong {
  overflow: hidden;
  color: #34445a;
  font-size: var(--fs-body);
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.calendar-popover {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  z-index: 80;
  width: min(340px, calc(100vw - 56px));
  padding: 14px;
  border: 1px solid #e1e6ef;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 18px 50px rgba(30, 42, 62, 0.16);
}

.end-picker .calendar-popover {
  right: 0;
  left: auto;
}

.calendar-header {
  margin-bottom: 12px;
  padding: 2px 2px 10px;
  border-bottom: 1px solid #eef1f5;
  display: grid;
  grid-template-columns: 34px 1fr 34px;
  align-items: center;
  gap: 8px;
}

.calendar-header > div {
  min-width: 0;
  text-align: center;
}

.calendar-header small {
  display: block;
  margin-bottom: 2px;
  color: #98a4b4;
  font-size: var(--fs-badge);
}

.calendar-header strong {
  display: block;
  color: #26364b;
  font-size: var(--fs-body);
}

.calendar-nav {
  width: 34px;
  height: 34px;
  border: 0;
  border-radius: 9px;
  background: #f5f6f9;
  display: grid;
  place-items: center;
  color: #56677d;
  cursor: pointer;
}

.calendar-nav:hover {
  background: #eee9fb;
  color: #7137b8;
}

.calendar-weekdays,
.calendar-days {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 4px;
}

.calendar-weekdays {
  margin-bottom: 5px;
}

.calendar-weekdays span {
  min-height: 24px;
  display: grid;
  place-items: center;
  color: #9aa5b4;
  font-size: var(--fs-badge);
  font-weight: 800;
}

.calendar-day {
  aspect-ratio: 1;
  min-width: 0;
  border: 0;
  border-radius: 10px;
  background: transparent;
  display: grid;
  place-items: center;
  color: #415168;
  font-family: inherit;
  font-size: var(--fs-small);
  font-weight: 700;
  cursor: pointer;
  transition: 0.15s;
}

.calendar-day:hover:not(:disabled):not(.selected) {
  background: #f3effb;
  color: #6b2fa8;
}

.calendar-day.outside {
  color: #c3cad3;
}

.calendar-day.today:not(.selected) {
  box-shadow: inset 0 0 0 1px #b9a3e6;
  color: #6b2fa8;
}

.calendar-day.selected {
  background: linear-gradient(135deg, #2563eb, #8613bd);
  color: #fff;
  box-shadow: 0 5px 12px rgba(109, 40, 217, 0.22);
}

.calendar-day.disabled,
.calendar-day:disabled {
  background: transparent;
  color: #d6dbe2;
  cursor: not-allowed;
  text-decoration: line-through;
}

.calendar-footer {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #eef1f5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.calendar-footer span {
  color: #8a97a8;
  font-size: var(--fs-badge);
  line-height: 1.6;
}

.calendar-footer button {
  flex: 0 0 auto;
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

.calendar-footer button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.field textarea {
  min-height: 138px;
  padding: 12px;
  resize: vertical;
  line-height: 1.6;
}

.field input:focus,
.field select:focus,
.field textarea:focus {
  border-color: #8f7cf1;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.08);
}

.input-icon {
  position: relative;
}

.input-icon svg {
  position: absolute;
  top: 50%;
  left: 12px;
  transform: translateY(-50%);
  color: #91a0b3;
}

.input-icon input {
  padding-left: 38px;
}

.tips-column {
  align-self: start;
  position: sticky;
  top: 20px;
}

.tips-card {
  padding: 19px;
}

.tips-icon {
  width: 42px;
  height: 42px;
  margin-bottom: 13px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: #f1ebff;
  color: #7c3aed;
}

.tips-card h3 {
  margin: 0;
  font-size: 18px;
  color: #1e2a3e;
}

.tips-card p {
  margin: 8px 0 14px;
  color: #8290a2;
  font-size: var(--fs-small);
  line-height: 1.6;
}

.tips-card ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.tips-card li {
  padding: 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #647287;
  font-size: var(--fs-small);
}

.tips-card li svg {
  color: #22a06b;
}

.skills-card {
  padding: 24px;
}

.skills-heading {
  margin-bottom: 18px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.skill-target {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
}

.skill-settings-link {
  padding: 0;
  border: 0;
  background: none;
  color: #5d2db2;
  font-family: inherit;
  font-size: var(--fs-small);
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 4px;
  cursor: pointer;
}

.segmented-control {
  padding: 4px;
  border-radius: 10px;
  background: #f1f3f7;
  display: flex;
  gap: 4px;
}

.segmented-control button {
  min-width: 120px;
  min-height: 36px;
  padding: 0 14px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #66758a;
  font-family: inherit;
  font-size: var(--fs-small);
  font-weight: 700;
  cursor: pointer;
}

.segmented-control button.active {
  background: #fff;
  color: #5d2db2;
  box-shadow: 0 2px 7px rgba(15, 23, 42, 0.07);
}











.action-bar {
  position: sticky;
  bottom: 14px;
  z-index: 30;
  margin-top: 20px;
  padding: 12px;
  border: 1px solid #dfe6ef;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
}

.secondary-button,
.primary-button {
  min-height: 41px;
  padding: 0 16px;
  border-radius: 9px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  font-family: inherit;
  font-weight: 700;
  cursor: pointer;
}

.secondary-button {
  border: 1px solid #dce4ee;
  background: #fff;
  color: #596a80;
}

.primary-button {
  border: 0;
  background: linear-gradient(135deg, #2563eb, #8613bd);
  color: #fff;
  box-shadow: 0 6px 16px rgba(109, 40, 217, 0.18);
}

.primary-button:disabled,
.secondary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spin {
  animation: spin 0.75s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 900px) {
  .hero-card,
  .skills-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .content-layout {
    grid-template-columns: 1fr;
  }

  .tips-column {
    position: static;
  }
}

@media (max-width: 650px) {
  .create-page {
    padding: 17px 13px 90px;
  }

  .hero-card,
  .form-card,
  .skills-card {
    padding: 18px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .calendar-popover,
  .end-picker .calendar-popover {
    right: auto;
    left: 0;
    width: min(340px, calc(100vw - 52px));
  }

  .steps {
    width: 100%;
  }

  .step-connector {
    flex: 1;
  }

  .step div {
    display: none;
  }

  .skill-target,
  .segmented-control {
    width: 100%;
  }

  .segmented-control button {
    flex: 1;
    min-width: 0;
  }
}
</style>