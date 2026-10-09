<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { CalendarRange, Users } from 'lucide-vue-next'

import BranchFilterSelect from '../common/BranchFilterSelect.vue'
import CalendarMonth from '../common/CalendarMonth.vue'
import { useLanguage } from '../../composables/useLanguage'
import { API_BASE } from '../../config/api'
import { adminFetch, getAdminSession } from '../../constants/currentAdmin'
import { ALL_BRANCHES_VALUE } from '../../constants/branches'
import { ACTIVITY_TYPE_COLORS, OTHER_TYPE_COLOR, activityTypeColor } from '../../utils/activityColors'
import { dayOf, isPast } from '../../utils/calendarDates'

/*
  ปฏิทินกิจกรรมท้ายหน้า Dashboard (GET /api/admin/calendar/activities) วาดด้วย CalendarMonth
  - แอดมินกลาง: เลือก "ทุกสาขา" หรือสาขาเดียว
  - แอดมินสาขา: "ทุกกิจกรรม" (ค่าเริ่มต้น ทุกกิจกรรมในคณะ) หรือ "เฉพาะสาขาของฉัน"
  - สีตามประเภทกิจกรรม (utils/activityColors.js)
*/
const { t } = useLanguage()
const router = useRouter()
const admin = getAdminSession()
const isCentral = admin?.is_central === true

const branch = ref(ALL_BRANCHES_VALUE)
const branchScope = ref('all')
const activities = ref([])
const loading = ref(false)
const loadError = ref(false)
let request = 0

async function loadActivities() {
  const current = ++request
  loading.value = true
  loadError.value = false

  try {
    const params = new URLSearchParams()
    if (isCentral) {
      if (branch.value !== ALL_BRANCHES_VALUE) params.set('major', branch.value)
    } else {
      params.set('scope', branchScope.value)
    }
    const response = await adminFetch(`${API_BASE}/api/admin/calendar/activities?${params}`)
    if (!response.ok) throw new Error()
    const data = await response.json()
    if (current !== request) return
    activities.value = data.activities
  } catch {
    if (current === request) {
      activities.value = []
      loadError.value = true
    }
  } finally {
    if (current === request) loading.value = false
  }
}

watch([branch, branchScope], loadActivities)

const events = computed(() =>
  activities.value
    .filter((item) => item.start_at && item.end_at)
    .map((item) => {
      const start = dayOf(item.start_at)
      const end = dayOf(item.end_at)
      const palette = activityTypeColor(item.activity_type)
      return {
        ...item,
        key: `activity-${item.id}`,
        start,
        // end ก่อน start (ข้อมูลผิด) ให้เป็นกิจกรรมวันเดียว
        end: end < start ? start : end,
        past: isPast(item.end_at),
        cancelled: item.status === 'cancelled',
        color: palette.color,
        legendKey: palette.key
      }
    })
)

const legend = computed(() =>
  [...ACTIVITY_TYPE_COLORS, OTHER_TYPE_COLOR].map((entry) => ({
    key: entry.key,
    color: entry.color,
    label: t.value.activityCalendar.types[entry.key]
  }))
)

function openDetails(item) {
  router.push(`/admin/activities/${item.id}/details`)
}

onMounted(loadActivities)
</script>

<template>
  <section class="card calendar-card" data-testid="activity-calendar">
    <div class="calendar-header">
      <div class="calendar-title">
        <span class="calendar-icon" aria-hidden="true"><CalendarRange :size="20" /></span>
        <div>
          <h2>{{ t.activityCalendar.title }}</h2>
          <p>{{ t.activityCalendar.description }}</p>
        </div>
      </div>

      <BranchFilterSelect v-if="isCentral" v-model="branch" class="calendar-branch" />

      <!-- แอดมินสาขา: ทุกกิจกรรมในคณะ หรือเฉพาะสาขาตัวเอง -->
      <div v-else class="scope-field">
        <label for="calendar-scope">{{ t.activityCalendar.scopeLabel }}</label>
        <select id="calendar-scope" v-model="branchScope" data-testid="calendar-scope">
          <option value="all">{{ t.activityCalendar.scopeAll }}</option>
          <option value="mine">{{ t.activityCalendar.scopeMine.replace('{major}', admin?.major || '') }}</option>
        </select>
      </div>
    </div>

    <CalendarMonth
      class="calendar-body"
      :events="events"
      :legend="legend"
      :loading="loading"
      :error="loadError ? t.activityCalendar.loadError : ''"
    >
      <template #popover="{ event, dateRange }">
        <dl>
          <div>
            <dt>{{ t.activityCalendar.typeLabel }}</dt>
            <dd><i class="swatch" :style="{ background: event.color }"></i>{{ event.activity_type || '-' }}</dd>
          </div>
          <div><dt>{{ t.activityCalendar.dateLabel }}</dt><dd>{{ dateRange }}</dd></div>
          <div><dt>{{ t.activityCalendar.organizerLabel }}</dt><dd>{{ event.organizer || '-' }}</dd></div>
          <div>
            <dt>{{ t.activityCalendar.participantsLabel }}</dt>
            <dd><Users :size="14" /> {{ t.activityCalendar.participantsCount.replace('{count}', event.participants ?? 0) }}</dd>
          </div>
          <div>
            <dt>{{ t.activityCalendar.branchLabel }}</dt>
            <dd>{{ event.major || t.activityCalendar.facultyWide }}</dd>
          </div>
        </dl>
        <!-- แอดมินสาขาเปิดรายละเอียดกิจกรรมของสาขาอื่นไม่ได้ -->
        <button v-if="event.can_open" type="button" class="details-link" @click="openDetails(event)">
          {{ t.activityCalendar.viewDetails }}
        </button>
      </template>
    </CalendarMonth>
  </section>
</template>

<style scoped>
.card {
  margin-top: 20px;
  padding: 25px;
  background: white;
  border: 1px solid #edf0f5;
  border-radius: 18px;
  box-shadow: 0 2px 8px rgba(30, 60, 100, 0.04);
}

.calendar-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.calendar-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.calendar-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: #eef2ff;
  color: #3d4fd6;
}

.calendar-title h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  color: #1d3268;
}

.calendar-title p {
  margin: 4px 0 0;
  font-size: var(--fs-body);
  color: #8da0bd;
}

.calendar-branch,
.scope-field {
  min-width: 220px;
}

.scope-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.scope-field label {
  color: #42526b;
  font-size: var(--fs-small);
  font-weight: 600;
}

.scope-field select {
  height: 40px;
  padding: 0 12px;
  border: 1px solid #dce5ef;
  border-radius: 10px;
  background: #fff;
  color: #1d3268;
  font: inherit;
  font-size: var(--fs-small);
}

@media (max-width: 700px) {
  .card {
    padding: 18px 14px;
  }

  .calendar-branch,
  .scope-field {
    width: 100%;
    min-width: 0;
  }
}
</style>
