<script setup>
import { computed, onMounted, ref } from 'vue'
import { CalendarRange } from 'lucide-vue-next'

import CalendarMonth from '../common/CalendarMonth.vue'
import { useLanguage } from '../../composables/useLanguage'
import { API_BASE, studentHeaders } from '../../constants/currentStudent'
import { STUDENT_SOURCE_COLORS, studentSourceColor } from '../../utils/activityColors'
import { dayOf, isPast } from '../../utils/calendarDates'

/*
  ปฏิทินกิจกรรมของนักศึกษา (ใต้รายการในหน้ากิจกรรมของฉัน) วาดด้วย CalendarMonth
  GET /api/student/me/calendar-activities = กิจกรรมที่คณะ (ส่วนกลาง) และสาขาของนักศึกษาจัด
  ไว้ดูล่วงหน้าว่าจะมีอะไรบ้าง (เข้าร่วมหรือยังก็ได้) สีตามแหล่ง: คณะ / สาขา
*/
const { t } = useLanguage()

const activities = ref([])
const loading = ref(false)
const loadError = ref(false)

async function loadActivities() {
  loading.value = true
  loadError.value = false
  try {
    const response = await fetch(`${API_BASE}/api/student/me/calendar-activities`, { headers: studentHeaders() })
    if (!response.ok) throw new Error()
    activities.value = (await response.json()).activities
  } catch {
    activities.value = []
    loadError.value = true
  } finally {
    loading.value = false
  }
}

onMounted(loadActivities)

const events = computed(() =>
  activities.value
    .filter((item) => item.start_at && item.end_at)
    .map((item) => {
      const start = dayOf(item.start_at)
      const end = dayOf(item.end_at)
      const palette = studentSourceColor(item.scope)
      return {
        ...item,
        key: `activity-${item.id}`,
        name: item.title,
        start,
        end: end < start ? start : end,
        past: isPast(item.end_at),
        cancelled: item.status === 'cancelled',
        color: palette.color,
        legendKey: palette.key
      }
    })
)

function joinLabel(event) {
  if (!event.joined) return t.value.studentCalendar.notJoined
  return event.role === 'organizer'
    ? t.value.studentCalendar.joinedAsOrganizer
    : t.value.studentCalendar.joinedAsParticipant
}

// ปฏิทินนี้มีแค่กิจกรรมคณะและกิจกรรมสาขา
const legend = computed(() =>
  STUDENT_SOURCE_COLORS.filter((entry) => entry.key !== 'external').map((entry) => ({
    key: entry.key,
    color: entry.color,
    label: t.value.studentCalendar.sources[entry.key]
  }))
)
</script>

<template>
  <section class="calendar-card" data-testid="student-activity-calendar">
    <div class="calendar-title">
      <span class="calendar-icon" aria-hidden="true"><CalendarRange :size="20" /></span>
      <div>
        <h2>{{ t.studentCalendar.title }}</h2>
        <p>{{ t.studentCalendar.description }}</p>
      </div>
    </div>

    <CalendarMonth
      :events="events"
      :legend="legend"
      :loading="loading"
      :error="loadError ? t.activityCalendar.loadError : ''"
    >
      <template #popover="{ event, dateRange }">
        <dl>
          <div>
            <dt>{{ t.studentCalendar.sourceLabel }}</dt>
            <dd><i class="swatch" :style="{ background: event.color }"></i>{{ t.studentCalendar.sources[event.legendKey] }}</dd>
          </div>
          <div><dt>{{ t.activityCalendar.dateLabel }}</dt><dd>{{ dateRange }}</dd></div>
          <div><dt>{{ t.activityCalendar.typeLabel }}</dt><dd>{{ event.activity_type || '-' }}</dd></div>
          <div><dt>{{ t.studentCalendar.locationLabel }}</dt><dd>{{ event.location || '-' }}</dd></div>
          <div><dt>{{ t.activityCalendar.organizerLabel }}</dt><dd>{{ event.organizer || '-' }}</dd></div>
          <div><dt>{{ t.studentCalendar.hoursLabel }}</dt><dd>{{ event.activity_hours }} {{ t.activityHours.unit }}</dd></div>
          <div>
            <dt>{{ t.studentCalendar.joinLabel }}</dt>
            <dd :class="event.joined ? 'joined' : 'not-joined'" data-testid="calendar-join-status">{{ joinLabel(event) }}</dd>
          </div>
        </dl>
      </template>
    </CalendarMonth>
  </section>
</template>

<style scoped>
.calendar-card {
  margin-top: 24px;
  padding: 22px;
  border: 1px solid #e6e9f2;
  border-radius: 16px;
  background: #fff;
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
  background: #f3e6fb;
  color: #8d00c4;
}

.calendar-title h2 {
  margin: 0;
  color: #1e2b4d;
  font-size: var(--fs-lead);
  font-weight: 800;
}

.calendar-title p {
  margin: 3px 0 0;
  color: #8a94a8;
  font-size: var(--fs-small);
}

:deep(dd.joined) {
  color: #157a37;
  font-weight: 700;
}

:deep(dd.not-joined) {
  color: #b45f06;
  font-weight: 600;
}

@media (max-width: 700px) {
  .calendar-card {
    padding: 16px 12px;
  }
}
</style>
