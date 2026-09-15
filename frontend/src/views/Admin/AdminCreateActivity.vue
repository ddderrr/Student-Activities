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
  GraduationCap,
  Leaf,
  Lightbulb,
  LoaderCircle,
  MapPin,
  Rocket,
  Scale,
  Sparkles,
  UsersRound,
  UserRound,
  Palette,
  HandHeart,
  Globe2,
  HeartPulse,
  Trees
} from 'lucide-vue-next'

const API_BASE = 'http://127.0.0.1:8000'
const router = useRouter()

const currentStep = ref(1)
const skillTarget = ref('staff')
const submitting = ref(false)
const errorMessage = ref('')

const activityTypes = [
  'กิจกรรมวิชาการ',
  'สัมมนา',
  'อบรม / Workshop',
  'จิตอาสา',
  'กิจกรรมพัฒนาทักษะ',
  'กิจกรรมนันทนาการ'
]

const form = ref({
  activity_type: '',
  name: '',
  start_at: '',
  end_at: '',
  department: '',
  responsible_person: '',
  advisor: '',
  location: '',
  description: ''
})

const staffSkillDefinitions = [
  {
    key: 'creative_leadership',
    label: 'Creative Leadership',
    description: 'ภาวะผู้นำเชิงสร้างสรรค์',
    icon: Lightbulb
  },
  {
    key: 'innovation',
    label: 'Innovation',
    description: 'การคิดและสร้างนวัตกรรม',
    icon: Sparkles
  },
  {
    key: 'entrepreneurship',
    label: 'Entrepreneurship',
    description: 'ความเป็นผู้ประกอบการ',
    icon: Rocket
  },
  {
    key: 'promote_equality',
    label: 'Promote Equality',
    description: 'การส่งเสริมความเท่าเทียม',
    icon: Scale
  },
  {
    key: 'academic',
    label: 'Academic',
    description: 'ทักษะทางวิชาการ',
    icon: GraduationCap
  },
  {
    key: 'nature_environmental',
    label: 'Nature and Environmental',
    description: 'ธรรมชาติและสิ่งแวดล้อม',
    icon: Leaf
  }
]

const participantSkillDefinitions = [
  {
    key: 'arts_culture_traditions',
    label: 'Arts, Culture, and Traditions',
    description: 'ศิลปะ วัฒนธรรม และประเพณี',
    icon: Palette
  },
  {
    key: 'volunteerism',
    label: 'Volunteerism',
    description: 'จิตอาสาและการมีส่วนร่วมเพื่อสังคม',
    icon: HandHeart
  },
  {
    key: 'academics',
    label: 'Academics',
    description: 'การเรียนรู้และพัฒนาทางวิชาการ',
    icon: GraduationCap
  },
  {
    key: 'internationalization',
    label: 'Internationalization',
    description: 'ความเป็นสากลและการเรียนรู้ข้ามวัฒนธรรม',
    icon: Globe2
  },
  {
    key: 'health_promotion',
    label: 'Health Promotion',
    description: 'การส่งเสริมสุขภาพและความเป็นอยู่ที่ดี',
    icon: HeartPulse
  },
  {
    key: 'nature_environmental_conservation',
    label: 'Nature and Environmental Conservation',
    description: 'การอนุรักษ์ธรรมชาติและสิ่งแวดล้อม',
    icon: Trees
  }
]

const staffSkills = ref({
  creative_leadership: 3,
  innovation: 3,
  entrepreneurship: 3,
  promote_equality: 3,
  academic: 3,
  nature_environmental: 3
})

const participantSkills = ref({
  arts_culture_traditions: 3,
  volunteerism: 3,
  academics: 3,
  internationalization: 3,
  health_promotion: 3,
  nature_environmental_conservation: 3
})

const activeSkillDefinitions = computed(() =>
  skillTarget.value === 'staff'
    ? staffSkillDefinitions
    : participantSkillDefinitions
)

const activeSkills = computed(() =>
  skillTarget.value === 'staff'
    ? staffSkills.value
    : participantSkills.value
)

const openCalendar = ref(null)
const calendarCursor = ref(new Date())

const weekDays = ['จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส', 'อา']

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
  if (!date) return 'เลือกวันที่'

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
  errorMessage.value = ''

  const required = [
    form.value.activity_type,
    form.value.name,
    form.value.start_at,
    form.value.end_at,
    form.value.responsible_person,
    form.value.location
  ]

  if (required.some((value) => !String(value || '').trim())) {
    errorMessage.value = 'กรุณากรอกข้อมูลที่มีเครื่องหมาย * ให้ครบ'
    return false
  }

  const start = new Date(form.value.start_at)
  const end = new Date(form.value.end_at)

  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    errorMessage.value = 'กรุณาระบุวันที่ให้ถูกต้อง'
    return false
  }

  if (end < start) {
    errorMessage.value = 'วันที่สิ้นสุดต้องไม่อยู่ก่อนวันที่เริ่มต้น'
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
  if (submitting.value) return

  submitting.value = true
  errorMessage.value = ''

  try {
    let response

    try {
      response = await fetch(`${API_BASE}/api/activities`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...form.value,
          // UI เลือกเฉพาะวันที่ แต่ยังส่งค่า datetime ให้ Backend เหมือนเดิม
          start_at: `${form.value.start_at}T00:00:00`,
          end_at: `${form.value.end_at}T23:59:59`,
          staff_skills: staffSkills.value,
          participant_skills: participantSkills.value
        })
      })
    } catch (networkError) {
      console.error('Create activity network error:', networkError)

      throw new Error(
        `เชื่อมต่อ Backend ไม่ได้ (${API_BASE}) กรุณาตรวจว่า uvicorn ยังรันอยู่`
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

      throw new Error(detail || 'ไม่สามารถสร้างกิจกรรมได้')
    }

    router.push('/admin/activities')
  } catch (error) {
    console.error('Create activity error:', error)

    errorMessage.value =
      error.message || 'ไม่สามารถสร้างกิจกรรมได้'
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
          <div class="eyebrow">
            <Sparkles :size="15" />
            ACTIVITY MANAGEMENT
          </div>

          <h1>Create New Activity</h1>
          <p>สร้างกิจกรรมใหม่และกำหนด Skill ที่เกี่ยวข้องในขั้นตอนเดียว</p>
        </div>

        <div class="steps">
          <div class="step" :class="{ active: currentStep >= 1 }">
            <span>1</span>
            <div>
              <strong>Activity Info</strong>
              <small>รายละเอียดกิจกรรม</small>
            </div>
          </div>

          <div class="step-connector" :class="{ active: currentStep === 2 }"></div>

          <div class="step" :class="{ active: currentStep === 2 }">
            <span>2</span>
            <div>
              <strong>Attach Skills</strong>
              <small>กำหนดระดับ Skill</small>
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
                  <h2>ข้อมูลพื้นฐาน</h2>
                  <p>ข้อมูลหลักที่ใช้แสดงในหน้ากิจกรรม</p>
                </div>
              </div>

              <div class="form-grid">
                <label class="field">
                  <span>ประเภทกิจกรรม <b>*</b></span>
                  <select v-model="form.activity_type">
                    <option disabled value="">เลือกประเภทกิจกรรม</option>
                    <option v-for="type in activityTypes" :key="type" :value="type">
                      {{ type }}
                    </option>
                  </select>
                </label>

                <label class="field">
                  <span>ชื่อกิจกรรม (ไทย/อังกฤษ) <b>*</b></span>
                  <input
                    v-model="form.name"
                    type="text"
                    placeholder="เช่น Bio-Tech Innovations 2026"
                  />
                </label>
              </div>
            </section>

            <section class="form-card schedule-card">
              <div class="section-heading">
                <div class="section-icon"><CalendarDays :size="20" /></div>
                <div>
                  <h2>กำหนดการ</h2>
                  <p>เลือกวันที่เริ่มต้นและวันที่สิ้นสุดของกิจกรรม</p>
                </div>
              </div>

              <div class="form-grid date-grid">
                <div class="field date-field">
                  <span>วันที่เริ่มต้น <b>*</b></span>
                  <div class="date-picker" @click.stop>
                    <button
                      type="button"
                      class="date-trigger"
                      :class="{ selected: form.start_at }"
                      @click="openCalendarPicker('start')"
                    >
                      <span class="date-trigger-icon"><CalendarDays :size="18" /></span>
                      <span class="date-trigger-text">
                        <small>START DATE</small>
                        <strong>{{ formatDisplayDate(form.start_at) }}</strong>
                      </span>
                    </button>

                    <div v-if="openCalendar === 'start'" class="calendar-popover">
                      <div class="calendar-header">
                        <button type="button" class="calendar-nav" @click="changeMonth(-1)">
                          <ChevronLeft :size="18" />
                        </button>
                        <div>
                          <small>เลือกวันที่เริ่มต้น</small>
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
                        <span>เลือกได้ทุกวันที่ต้องการ</span>
                        <button type="button" @click="selectToday">วันนี้</button>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="field date-field">
                  <span>วันที่สิ้นสุด <b>*</b></span>
                  <div class="date-picker end-picker" @click.stop>
                    <button
                      type="button"
                      class="date-trigger"
                      :class="{ selected: form.end_at }"
                      @click="openCalendarPicker('end')"
                    >
                      <span class="date-trigger-icon"><CalendarDays :size="18" /></span>
                      <span class="date-trigger-text">
                        <small>END DATE</small>
                        <strong>{{ formatDisplayDate(form.end_at) }}</strong>
                      </span>
                    </button>

                    <div v-if="openCalendar === 'end'" class="calendar-popover">
                      <div class="calendar-header">
                        <button type="button" class="calendar-nav" @click="changeMonth(-1)">
                          <ChevronLeft :size="18" />
                        </button>
                        <div>
                          <small>เลือกวันที่สิ้นสุด</small>
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
                        <span>วันสิ้นสุดต้องไม่ก่อนวันเริ่มต้น</span>
                        <button
                          type="button"
                          :disabled="Boolean(form.start_at && toDateKey(new Date()) < form.start_at)"
                          @click="selectToday"
                        >
                          วันนี้
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
                  <h2>หน่วยงานและบุคลากร</h2>
                  <p>ระบุหน่วยงาน ผู้รับผิดชอบ และสถานที่</p>
                </div>
              </div>

              <div class="form-grid">
                <label class="field">
                  <span>หน่วยงานที่จัด (ภาควิชา/คณะ)</span>
                  <input
                    v-model="form.department"
                    type="text"
                    placeholder="เช่น Physics Department"
                  />
                </label>

                <label class="field">
                  <span>ผู้รับผิดชอบหลัก <b>*</b></span>
                  <div class="input-icon">
                    <UserRound :size="17" />
                    <input
                      v-model="form.responsible_person"
                      type="text"
                      placeholder="ค้นหาชื่อบุคลากร..."
                    />
                  </div>
                </label>

                <label class="field">
                  <span>อาจารย์ที่ปรึกษา (อาจารย์ผู้รับผิดชอบ)</span>
                  <div class="input-icon">
                    <UserRound :size="17" />
                    <input
                      v-model="form.advisor"
                      type="text"
                      placeholder="ชื่ออาจารย์ที่ปรึกษา"
                    />
                  </div>
                </label>

                <label class="field">
                  <span>สถานที่ <b>*</b></span>
                  <div class="input-icon">
                    <MapPin :size="17" />
                    <input
                      v-model="form.location"
                      type="text"
                      placeholder="เช่น Room 402, Science Building 3"
                    />
                  </div>
                </label>
              </div>
            </section>

            <section class="form-card">
              <div class="section-heading">
                <div class="section-icon"><FileText :size="20" /></div>
                <div>
                  <h2>รายละเอียดเพิ่มเติม</h2>
                  <p>ระบุวัตถุประสงค์ ผลลัพธ์ และกลุ่มเป้าหมาย</p>
                </div>
              </div>

              <label class="field">
                <span>รายละเอียดกิจกรรม</span>
                <textarea
                  v-model="form.description"
                  rows="6"
                  placeholder="ระบุวัตถุประสงค์ ผลลัพธ์ที่คาดหวัง และกลุ่มเป้าหมาย..."
                ></textarea>
              </label>
            </section>
          </main>

          <aside class="tips-column">
            <section class="tips-card">
              <div class="tips-icon"><CheckCircle2 :size="21" /></div>
              <h3>ก่อนกดถัดไป</h3>
              <p>ตรวจสอบข้อมูลสำคัญให้ครบก่อนกำหนด Skill ของกิจกรรม</p>

              <ul>
                <li><Check :size="14" /> ชื่อและประเภทกิจกรรม</li>
                <li><Check :size="14" /> วันที่เริ่ม / สิ้นสุด</li>
                <li><Check :size="14" /> ผู้รับผิดชอบหลัก</li>
                <li><Check :size="14" /> สถานที่จัดกิจกรรม</li>
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
              <div class="eyebrow"><GraduationCap :size="15" /> ATTACH SKILLS</div>
              <h2>กำหนด Skill ของกิจกรรม</h2>
              <p>
                  {{
                    skillTarget === 'staff'
                      ? 'Staff ใช้ชุด Skill สำหรับผู้จัดและผู้ปฏิบัติงาน'
                      : 'Participant ใช้ชุด Skill สำหรับผู้เข้าร่วมกิจกรรม'
                  }}
                </p>
            </div>

            <div class="segmented-control">
              <button
                :class="{ active: skillTarget === 'staff' }"
                @click="skillTarget = 'staff'"
              >
                Staff
              </button>
              <button
                :class="{ active: skillTarget === 'participant' }"
                @click="skillTarget = 'participant'"
              >
                Participant
              </button>
            </div>
          </div>

          <div class="skill-list">
            <article
              v-for="skill in activeSkillDefinitions"
              :key="skill.key"
              class="skill-row"
            >
              <div class="skill-topline">
                <div class="skill-name">
                  <div class="skill-icon"><component :is="skill.icon" :size="18" /></div>
                  <div>
                    <strong>{{ skill.label }}</strong>
                    <small>{{ skill.description }}</small>
                  </div>
                </div>

                <span class="level-badge">LEVEL {{ activeSkills[skill.key] }}</span>
              </div>

              <input
                v-model.number="activeSkills[skill.key]"
                class="skill-range"
                type="range"
                min="1"
                max="5"
                step="1"
              />

              <div class="range-labels">
                <span v-for="level in 5" :key="level">{{ level }}</span>
              </div>
            </article>
          </div>
        </section>
      </template>

      <footer class="action-bar">
        <button class="secondary-button" :disabled="submitting" @click="goBack">
          <ArrowLeft :size="17" />
          {{ currentStep === 1 ? 'Cancel' : 'Back' }}
        </button>

        <button
          v-if="currentStep === 1"
          class="primary-button"
          @click="nextStep"
        >
          Continue
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
          {{ submitting ? 'Creating...' : 'Create Activity' }}
        </button>
      </footer>
    </div>
  </section>
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

.eyebrow {
  margin-bottom: 7px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: #7e36bd;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
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
  font-size: 13px;
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
  font-size: 12px;
  font-weight: 800;
}

.step.active > span {
  background: #8613bd;
  color: #fff;
}

.step strong {
  display: block;
  font-size: 12px;
}

.step small {
  display: block;
  margin-top: 2px;
  color: #96a2b2;
  font-size: 9px;
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
  font-size: 12px;
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

.section-icon,
.skill-icon {
  display: grid;
  place-items: center;
  background: #f5f4f4;
  color: #1769dc;
}

.section-icon {
  width: 39px;
  height: 39px;
  border-radius: 11px;
}

.section-heading h2,
.skills-heading h2 {
  margin: 0;
  font-size: 16px;
  color: #1e2a3e;
}

.section-heading p {
  margin: 3px 0 0;
  color: #657bbc;
  font-size: 10px;
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
  font-size: 11px;
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
  font-size: 13px;
  transition: 0.2s;
}

.field input,
.field select {
  height: 43px;
  padding: 0 12px;
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
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.date-trigger-text strong {
  overflow: hidden;
  color: #34445a;
  font-size: 13px;
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
  font-size: 9px;
}

.calendar-header strong {
  display: block;
  color: #26364b;
  font-size: 14px;
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
  font-size: 9px;
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
  font-size: 11px;
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
  font-size: 9px;
  line-height: 1.4;
}

.calendar-footer button {
  flex: 0 0 auto;
  padding: 6px 10px;
  border: 0;
  border-radius: 8px;
  background: #f1ebff;
  color: #6d35aa;
  font-family: inherit;
  font-size: 10px;
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
  font-size: 15px;
  color: #1e2a3e;
}

.tips-card p {
  margin: 8px 0 14px;
  color: #8290a2;
  font-size: 11px;
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
  font-size: 11px;
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
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.segmented-control button.active {
  background: #fff;
  color: #5d2db2;
  box-shadow: 0 2px 7px rgba(15, 23, 42, 0.07);
}

.skill-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skill-row {
  padding: 17px 18px;
  border: 1px solid #e7ebf1;
  border-radius: 12px;
  background: #fbfcfe;
}

.skill-topline {
  margin-bottom: 13px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.skill-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.skill-icon {
  width: 35px;
  height: 35px;
  border-radius: 9px;
}

.skill-name strong {
  display: block;
  color: #26364b;
  font-size: 12px;
}

.skill-name small {
  display: block;
  margin-top: 2px;
  color: #94a1b1;
  font-size: 9px;
}

.level-badge {
  padding: 5px 9px;
  border-radius: 999px;
  background: #e8f8ee;
  color: #17864d;
  font-size: 9px;
  font-weight: 800;
}

.skill-range {
  width: 100%;
  accent-color: #155bc7;
  cursor: pointer;
}

.range-labels {
  margin-top: 3px;
  display: flex;
  justify-content: space-between;
  color: #8290a2;
  font-size: 9px;
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

  .segmented-control {
    width: 100%;
  }

  .segmented-control button {
    flex: 1;
    min-width: 0;
  }
}
</style>