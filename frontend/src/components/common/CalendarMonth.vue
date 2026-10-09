<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ChevronLeft, ChevronRight, X } from 'lucide-vue-next'

import { useLanguage } from '../../composables/useLanguage'

/*
  ปฏิทินรายเดือน ใช้ร่วมกันทุกหน้า (Dashboard แอดมิน, กิจกรรมของฉันของนักศึกษา) วาดอย่างเดียว ไม่โหลดข้อมูลเอง
  events: [{ key, id, name, start: Date, end: Date, past, cancelled, color, legendKey }]
    start/end = วันเริ่ม/วันสิ้นสุด (เที่ยงคืนเวลาเครื่อง) ใช้ dayOf() แปลงจากค่าของ API
  legend: [{ key, label, color }] คำอธิบายสี แสดงเฉพาะ key ที่มีในเดือนที่แสดง
  slot "popover" ({ event, dateRange }) = เนื้อหา popup เมื่อกดกิจกรรม (สถานะ + ชื่อกิจกรรมแสดงให้แล้ว)

  กิจกรรมหลายวันเป็นแถบยาวต่อกันแบบ Google Calendar: แบ่งตามสัปดาห์ แล้ววางแต่ละช่วงลงแถว (lane)
  แรกที่ว่าง วันไหนเกิน MAX_LANES แถว แสดง "+N" ให้กดดูรายการของวันนั้น
  ผ่านมาแล้ว = สีเดิมจาง 40%, ยกเลิก = ลายขีดสีเทา
*/
const props = defineProps({
  events: { type: Array, required: true },
  legend: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' }
})

const MAX_LANES = 3
const DAY_MS = 86_400_000

const { t, currentLanguage } = useLanguage()

const today = new Date()
const todayKey = dateKey(today)
const viewMonth = ref(new Date(today.getFullYear(), today.getMonth(), 1))

const locale = computed(() => (currentLanguage.value === 'TH' ? 'th-TH' : 'en-GB'))

function dateKey(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

/* ---------- เดือนที่แสดง ---------- */

const monthTitle = computed(() =>
  new Intl.DateTimeFormat(locale.value, { month: 'long', year: 'numeric' }).format(viewMonth.value)
)

// ชื่อวันในสัปดาห์ เริ่มวันอาทิตย์ (2023-01-01 เป็นวันอาทิตย์)
const weekdayNames = computed(() => {
  const formatter = new Intl.DateTimeFormat(locale.value, { weekday: 'short' })
  return Array.from({ length: 7 }, (_, index) => formatter.format(new Date(2023, 0, 1 + index)))
})

function shiftMonth(step) {
  closePopover()
  viewMonth.value = new Date(viewMonth.value.getFullYear(), viewMonth.value.getMonth() + step, 1)
}

function goToday() {
  closePopover()
  viewMonth.value = new Date(today.getFullYear(), today.getMonth(), 1)
}

const isCurrentMonth = computed(() =>
  viewMonth.value.getFullYear() === today.getFullYear() && viewMonth.value.getMonth() === today.getMonth()
)

/* ---------- จัดวางแถบกิจกรรมทีละสัปดาห์ ---------- */

const weeks = computed(() => {
  const first = viewMonth.value
  const gridStart = new Date(first.getFullYear(), first.getMonth(), 1 - first.getDay())
  const lastOfMonth = new Date(first.getFullYear(), first.getMonth() + 1, 0)
  const weekCount = Math.ceil((first.getDay() + lastOfMonth.getDate()) / 7)

  return Array.from({ length: weekCount }, (_, weekIndex) => {
    const weekStart = new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + weekIndex * 7)
    const weekEnd = new Date(weekStart.getFullYear(), weekStart.getMonth(), weekStart.getDate() + 6)

    const days = Array.from({ length: 7 }, (_, column) => {
      const date = new Date(weekStart.getFullYear(), weekStart.getMonth(), weekStart.getDate() + column)
      return {
        key: dateKey(date),
        date,
        number: date.getDate(),
        inMonth: date.getMonth() === first.getMonth(),
        today: dateKey(date) === todayKey
      }
    })

    // กิจกรรมที่ทับสัปดาห์นี้: เริ่มก่อนอยู่ก่อน ยาวกว่าอยู่ก่อน (แถบยาวอยู่บนสุดเหมือน Google Calendar)
    const overlapping = props.events
      .filter((item) => item.start <= weekEnd && item.end >= weekStart)
      .sort((a, b) => a.start - b.start || (b.end - b.start) - (a.end - a.start) || String(a.key).localeCompare(String(b.key)))

    const laneEnds = []
    const segments = []
    const hiddenByDay = Array(7).fill(0)

    for (const item of overlapping) {
      const startColumn = Math.max(0, Math.round((item.start - weekStart) / DAY_MS))
      const endColumn = Math.min(6, Math.round((item.end - weekStart) / DAY_MS))
      let lane = laneEnds.findIndex((end) => end < startColumn)
      if (lane === -1) lane = laneEnds.length
      laneEnds[lane] = endColumn

      if (lane >= MAX_LANES) {
        for (let column = startColumn; column <= endColumn; column++) hiddenByDay[column]++
        continue
      }

      segments.push({
        item,
        lane,
        startColumn,
        endColumn,
        // ต่อจากสัปดาห์ก่อน / ต่อไปสัปดาห์หน้า: ไม่ทำมุมโค้งฝั่งนั้น
        continuesBefore: item.start < weekStart,
        continuesAfter: item.end > weekEnd
      })
    }

    return {
      key: dateKey(weekStart),
      days,
      segments,
      hiddenByDay,
      // อย่างน้อย 1 แถว: repeat(0, ...) ใน CSS grid ใช้ไม่ได้
      lanes: Math.max(1, Math.min(laneEnds.length, MAX_LANES))
    }
  })
})

// คำอธิบายสี: เฉพาะสีที่มีกิจกรรมในเดือนที่แสดง
const monthLegend = computed(() => {
  const keys = new Set(
    props.events
      .filter((item) => item.start <= monthEnd.value && item.end >= viewMonth.value)
      .map((item) => item.legendKey)
  )
  return props.legend.filter((entry) => keys.has(entry.key))
})

const monthEnd = computed(() => new Date(viewMonth.value.getFullYear(), viewMonth.value.getMonth() + 1, 0))

const monthHasActivities = computed(() => weeks.value.some((week) => week.segments.length || week.hiddenByDay.some(Boolean)))

/* ---------- popup ---------- */

const popover = ref(null) // { type: 'activity', item } | { type: 'day', date, items }
const popoverStyle = ref({})
const wrapper = ref(null)

function placePopover(event) {
  const box = wrapper.value.getBoundingClientRect()
  const target = event.currentTarget.getBoundingClientRect()
  const width = Math.min(320, box.width - 16)
  const left = Math.min(Math.max(8, target.left - box.left), box.width - width - 8)
  popoverStyle.value = { top: `${target.bottom - box.top + 6}px`, left: `${left}px`, width: `${width}px` }
}

function openActivity(item, event) {
  placePopover(event)
  popover.value = { type: 'activity', item }
}

function openDay(day, event) {
  placePopover(event)
  const items = props.events
    .filter((item) => item.start <= day.date && item.end >= day.date)
    .sort((a, b) => a.start - b.start || String(a.key).localeCompare(String(b.key)))
  popover.value = { type: 'day', date: day.date, items }
}

function closePopover() {
  popover.value = null
}

function formatDate(date, withWeekday = false) {
  return new Intl.DateTimeFormat(locale.value, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    ...(withWeekday ? { weekday: 'short' } : {})
  }).format(date)
}

function dateRange(item) {
  return item.start.getTime() === item.end.getTime()
    ? formatDate(item.start)
    : `${formatDate(item.start)} – ${formatDate(item.end)}`
}

function statusLabel(item) {
  if (item.cancelled) return t.value.activityCalendar.statusCancelled
  if (item.past) return t.value.activityCalendar.statusPast
  return item.start > today ? t.value.activityCalendar.statusUpcoming : t.value.activityCalendar.statusOngoing
}

function onDocumentClick(event) {
  if (popover.value && wrapper.value && !wrapper.value.contains(event.target)) closePopover()
}

function onKeydown(event) {
  if (event.key === 'Escape') closePopover()
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div class="calendar-month">
    <div class="calendar-toolbar">
      <div class="month-nav">
        <button type="button" class="nav-button" :aria-label="t.activityCalendar.previousMonth" data-testid="calendar-prev" @click="shiftMonth(-1)">
          <ChevronLeft :size="18" />
        </button>
        <h3 class="month-title" data-testid="calendar-month">{{ monthTitle }}</h3>
        <button type="button" class="nav-button" :aria-label="t.activityCalendar.nextMonth" data-testid="calendar-next" @click="shiftMonth(1)">
          <ChevronRight :size="18" />
        </button>
        <button type="button" class="today-button" :disabled="isCurrentMonth" @click="goToday">
          {{ t.activityCalendar.today }}
        </button>
      </div>

      <div class="legend" aria-hidden="true">
        <span><i class="swatch upcoming"></i>{{ t.activityCalendar.legendUpcoming }}</span>
        <span><i class="swatch past"></i>{{ t.activityCalendar.legendPast }}</span>
        <span><i class="swatch cancelled"></i>{{ t.activityCalendar.legendCancelled }}</span>
      </div>
    </div>

    <div v-if="monthLegend.length" class="type-legend" data-testid="calendar-type-legend">
      <span v-for="entry in monthLegend" :key="entry.key">
        <i class="swatch" :style="{ background: entry.color }"></i>{{ entry.label }}
      </span>
    </div>

    <p v-if="error" class="calendar-state error">{{ error }}</p>

    <div ref="wrapper" class="calendar-wrapper" :class="{ loading }">
      <div class="calendar-scroll">
        <div class="calendar-grid">
          <div class="weekday-row">
            <span v-for="name in weekdayNames" :key="name">{{ name }}</span>
          </div>

          <div
            v-for="week in weeks"
            :key="week.key"
            class="week-row"
            :style="{ '--lanes': week.lanes }"
          >
            <div
              v-for="(day, column) in week.days"
              :key="day.key"
              class="day-cell"
              :class="{ outside: !day.inMonth, today: day.today }"
              :style="{ gridColumn: column + 1 }"
            >
              <span class="day-number">{{ day.number }}</span>
            </div>

            <button
              v-for="segment in week.segments"
              :key="`${segment.item.key}-${week.key}`"
              type="button"
              class="event-bar"
              :class="{
                past: segment.item.past,
                cancelled: segment.item.cancelled,
                'continues-before': segment.continuesBefore,
                'continues-after': segment.continuesAfter
              }"
              :style="{ gridColumn: `${segment.startColumn + 1} / ${segment.endColumn + 2}`, gridRow: segment.lane + 2, '--event-color': segment.item.color }"
              :title="segment.item.name"
              :data-activity-id="segment.item.id"
              :data-event-key="segment.item.key"
              @click.stop="openActivity(segment.item, $event)"
            >
              {{ segment.item.name }}
            </button>

            <template v-for="(hidden, column) in week.hiddenByDay" :key="`more-${column}`">
              <button
                v-if="hidden"
                type="button"
                class="more-button"
                :style="{ gridColumn: column + 1, gridRow: MAX_LANES + 2 }"
                @click.stop="openDay(week.days[column], $event)"
              >
                {{ t.activityCalendar.more.replace('{count}', hidden) }}
              </button>
            </template>
          </div>
        </div>
      </div>

      <p v-if="!loading && !error && !monthHasActivities" class="calendar-state">{{ t.activityCalendar.empty }}</p>

      <!-- popup รายละเอียด -->
      <div
        v-if="popover"
        class="calendar-popover"
        role="dialog"
        data-testid="calendar-popover"
        :style="{ ...popoverStyle, '--event-color': popover.type === 'activity' ? popover.item.color : '#3d4fd6' }"
        :class="{ accented: popover.type === 'activity' }"
        @click.stop
      >
        <button type="button" class="popover-close" :aria-label="t.activityCalendar.close" @click="closePopover">
          <X :size="16" />
        </button>

        <template v-if="popover.type === 'activity'">
          <span class="status-chip" :class="{ past: popover.item.past, cancelled: popover.item.cancelled }">
            {{ statusLabel(popover.item) }}
          </span>
          <h4>{{ popover.item.name }}</h4>
          <slot name="popover" :event="popover.item" :date-range="dateRange(popover.item)" />
        </template>

        <template v-else>
          <h4>{{ formatDate(popover.date, true) }}</h4>
          <ul class="day-list">
            <li v-for="item in popover.items" :key="item.key">
              <button
                type="button"
                class="day-list-item"
                :class="{ past: item.past, cancelled: item.cancelled }"
                @click.stop="popover = { type: 'activity', item }"
              >
                <i class="swatch" :class="{ cancelled: item.cancelled }" :style="item.cancelled ? null : { background: item.color, opacity: item.past ? 0.4 : 1 }"></i>
                <span>{{ item.name }}</span>
              </button>
            </li>
          </ul>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.calendar-toolbar {
  margin: 20px 0 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.month-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.month-title {
  min-width: 170px;
  margin: 0;
  color: #1d3268;
  font-size: var(--fs-lead);
  font-weight: 800;
  text-align: center;
}

.nav-button,
.today-button {
  height: 34px;
  border: 1px solid #e3e8f0;
  border-radius: 9px;
  background: #fff;
  color: #42526b;
  font: inherit;
  cursor: pointer;
}

.nav-button {
  width: 34px;
  display: grid;
  place-items: center;
}

.today-button {
  padding: 0 12px;
  font-size: var(--fs-small);
  font-weight: 700;
}

.nav-button:hover,
.today-button:hover:not(:disabled) {
  background: #f3f6ff;
  color: #3d4fd6;
}

.today-button:disabled {
  color: #a3aebf;
  cursor: default;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  color: #6b7a90;
  font-size: var(--fs-caption);
  font-weight: 600;
}

.legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

:deep(.swatch),
.swatch {
  flex-shrink: 0;
  width: 12px;
  height: 12px;
  border-radius: 4px;
  display: inline-block;
}

.swatch.upcoming { background: #475569; }
.swatch.past { background: rgba(71, 85, 105, 0.4); }
.swatch.cancelled { background: repeating-linear-gradient(135deg, #e5e7eb 0 3px, #cbd2dc 3px 6px); }

.type-legend {
  margin: -2px 0 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  color: #42526b;
  font-size: var(--fs-caption);
  font-weight: 600;
}

.type-legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.calendar-state {
  margin: 12px 0 0;
  color: #8da0bd;
  font-size: var(--fs-small);
  text-align: center;
}

.calendar-state.error {
  margin: 0 0 10px;
  color: #b42318;
}

.calendar-wrapper {
  position: relative;
}

.calendar-wrapper.loading .calendar-grid {
  opacity: 0.55;
}

.calendar-scroll {
  overflow-x: auto;
}

.calendar-grid {
  min-width: 640px;
  border: 1px solid #edf0f5;
  border-radius: 14px;
  overflow: hidden;
  transition: opacity 0.15s ease;
}

.weekday-row {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  background: #f7f9fc;
  border-bottom: 1px solid #edf0f5;
}

.weekday-row span {
  padding: 9px 10px;
  color: #6b7a90;
  font-size: var(--fs-caption);
  font-weight: 700;
  text-align: center;
}

/* แถวแรก = เลขวันที่, แถวถัดไป = lane ของแถบกิจกรรม, แถวสุดท้าย = ปุ่ม +N */
.week-row {
  position: relative;
  min-height: 112px;
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  grid-template-rows: 32px repeat(var(--lanes), 26px) 24px;
  row-gap: 3px;
  padding-bottom: 6px;
}

.week-row + .week-row {
  border-top: 1px solid #edf0f5;
}

.day-cell {
  grid-row: 1 / -1;
  padding: 6px 8px;
  border-left: 1px solid #f1f4f8;
}

.day-cell:first-child {
  border-left: 0;
}

.day-cell.outside {
  background: #fbfcfe;
}

.day-cell.outside .day-number {
  color: #c2cad8;
}

.day-number {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: inline-grid;
  place-items: center;
  color: #42526b;
  font-size: var(--fs-small);
  font-weight: 700;
}

.day-cell.today {
  background: #f5f7ff;
}

.day-cell.today .day-number {
  background: #3d4fd6;
  color: #fff;
}

.event-bar {
  z-index: 1;
  min-width: 0;
  margin: 0 4px;
  padding: 0 8px;
  border: 0;
  border-radius: 6px;
  overflow: hidden;
  /* สีตามประเภทกิจกรรม (--event-color) */
  background: var(--event-color, #4338ca);
  color: #fff;
  font: inherit;
  font-size: var(--fs-caption);
  font-weight: 700;
  line-height: 26px;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  transition: filter 0.15s ease;
}

.event-bar:hover {
  filter: brightness(1.12);
}

.event-bar.past {
  /* ผ่านมาแล้ว: สีเดิมจางลงเหลือ 40% ตัวอักษรสีเข้มให้ยังอ่านออก */
  background: color-mix(in srgb, var(--event-color, #4338ca) 40%, white);
  color: #1f2937;
  font-weight: 600;
}

.event-bar.cancelled {
  /* ยกเลิก: ลายขีดสีเทา + ขอบซ้ายเป็นสีประเภท */
  box-shadow: inset 3px 0 0 var(--event-color, #4338ca);
  background: repeating-linear-gradient(135deg, #f1f3f6 0 6px, #e6e9ee 6px 12px);
  color: #8a96a8;
  font-weight: 600;
  text-decoration: line-through;
}

.event-bar.continues-before {
  margin-left: 0;
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}

.event-bar.continues-after {
  margin-right: 0;
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.more-button {
  z-index: 1;
  margin: 0 4px;
  padding: 0 6px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #3d4fd6;
  font: inherit;
  font-size: var(--fs-caption);
  font-weight: 700;
  text-align: left;
  cursor: pointer;
}

.more-button:hover {
  background: #eef2ff;
}

.calendar-popover {
  position: absolute;
  z-index: 20;
  padding: 16px;
  overflow: hidden;
  border: 1px solid #e3e8f0;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 18px 44px rgba(28, 41, 61, 0.18);
}

.calendar-popover.accented {
  border-top: 4px solid var(--event-color);
}

.popover-close {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: transparent;
  color: #7b8ba3;
  cursor: pointer;
}

.popover-close:hover {
  background: #f3f6fb;
}

.status-chip {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--event-color, #3d4fd6) 14%, white);
  color: var(--event-color, #3d4fd6);
  font-size: var(--fs-caption);
  font-weight: 700;
}

.status-chip.past {
  background: #f1f4f8;
  color: #5b6b82;
}

.status-chip.cancelled {
  background: #fef2f2;
  color: #b42318;
}

.calendar-popover h4 {
  margin: 8px 28px 10px 0;
  color: #1d3268;
  font-size: var(--fs-body);
  line-height: 1.45;
}

:deep(.calendar-popover dl) {
  margin: 0;
  display: grid;
  gap: 6px;
}

:deep(.calendar-popover dl div) {
  display: grid;
  grid-template-columns: 92px 1fr;
  gap: 8px;
}

:deep(.calendar-popover dt) {
  color: #8da0bd;
  font-size: var(--fs-caption);
  font-weight: 600;
}

:deep(.calendar-popover dd) {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 5px;
  color: #34445a;
  font-size: var(--fs-small);
}

:deep(.details-link) {
  margin-top: 12px;
  padding: 0;
  border: 0;
  background: none;
  color: var(--event-color, #3d4fd6);
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 700;
  cursor: pointer;
}

:deep(.details-link:hover) {
  text-decoration: underline;
}

.day-list {
  max-height: 260px;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  list-style: none;
}

.day-list-item {
  width: 100%;
  padding: 7px 6px;
  border: 0;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  color: #1d3268;
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}

.day-list-item:hover {
  background: #f5f7fb;
}

.day-list-item.past {
  color: #6b7a90;
  font-weight: 500;
}

.day-list-item.cancelled span {
  text-decoration: line-through;
}

@media (max-width: 700px) {
  .month-title {
    min-width: 130px;
    font-size: var(--fs-body);
  }
}
</style>
