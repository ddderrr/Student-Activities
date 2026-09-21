<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { useLanguage } from '../../composables/useLanguage'

const { currentLanguage } = useLanguage()
const dateLocale = computed(() => (currentLanguage.value === 'TH' ? 'th-TH' : 'en-US'))

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  // วันที่เร็วที่สุดที่เลือกได้ (YYYY-MM-DD) วันก่อนหน้านี้จะถูกปิดในปฏิทิน
  min: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Select date'
  }
})

const emit = defineEmits(['update:modelValue'])

const WEEKDAY_LABELS = computed(() =>
  currentLanguage.value === 'TH'
    ? ['อา', 'จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส']
    : ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
)

function parseISO(value) {
  if (!value) return null

  const [year, month, day] = value.split('-').map(Number)

  if (!year || !month || !day) return null

  return new Date(year, month - 1, day)
}

function toISO(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
}

function isSameDay(a, b) {
  return (
    a &&
    b &&
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}

const open = ref(false)
const wrapper = ref(null)

const selectedDate = computed(() => parseISO(props.modelValue))
const minDate = computed(() => parseISO(props.min))

const today = new Date()
const viewYear = ref((selectedDate.value || today).getFullYear())
const viewMonth = ref((selectedDate.value || today).getMonth())

watch(open, (isOpen) => {
  if (!isOpen) return

  const base = selectedDate.value || minDate.value || new Date()
  viewYear.value = base.getFullYear()
  viewMonth.value = base.getMonth()
})

const monthLabel = computed(() =>
  new Date(viewYear.value, viewMonth.value, 1).toLocaleDateString(dateLocale.value, {
    month: 'long',
    year: 'numeric'
  })
)

const displayText = computed(() =>
  selectedDate.value
    ? selectedDate.value.toLocaleDateString(dateLocale.value, {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })
    : ''
)

// ปฏิทิน 6 แถว x 7 วัน รวมวันของเดือนก่อน/ถัดไปให้เต็มตาราง
const weeks = computed(() => {
  const firstOfMonth = new Date(viewYear.value, viewMonth.value, 1)
  const startOffset = firstOfMonth.getDay()
  const gridStart = new Date(viewYear.value, viewMonth.value, 1 - startOffset)

  const days = []
  for (let i = 0; i < 42; i += 1) {
    days.push(
      new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + i)
    )
  }

  const result = []
  for (let i = 0; i < days.length; i += 7) {
    result.push(days.slice(i, i + 7))
  }

  return result
})

function isDisabled(day) {
  return Boolean(minDate.value) && day < minDate.value
}

function isCurrentMonth(day) {
  return day.getMonth() === viewMonth.value
}

function pickDay(day) {
  if (isDisabled(day)) return

  emit('update:modelValue', toISO(day))
  open.value = false
}

function prevMonth() {
  if (viewMonth.value === 0) {
    viewMonth.value = 11
    viewYear.value -= 1
  } else {
    viewMonth.value -= 1
  }
}

function nextMonth() {
  if (viewMonth.value === 11) {
    viewMonth.value = 0
    viewYear.value += 1
  } else {
    viewMonth.value += 1
  }
}

function toggleOpen() {
  open.value = !open.value
}

function handleClickOutside(event) {
  if (open.value && wrapper.value && !wrapper.value.contains(event.target)) {
    open.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', handleClickOutside))
</script>

<template>
  <div ref="wrapper" class="date-picker">
    <button type="button" class="date-picker-trigger" @click.stop="toggleOpen">
      <Calendar :size="15" />
      <span :class="{ placeholder: !displayText }">{{ displayText || placeholder }}</span>
    </button>

    <div v-if="open" class="date-picker-panel" role="dialog" aria-label="Choose a date">
      <div class="date-picker-header">
        <button type="button" class="nav-button" @click.stop="prevMonth">
          <ChevronLeft :size="16" />
        </button>

        <strong>{{ monthLabel }}</strong>

        <button type="button" class="nav-button" @click.stop="nextMonth">
          <ChevronRight :size="16" />
        </button>
      </div>

      <div class="date-picker-weekdays">
        <span v-for="label in WEEKDAY_LABELS" :key="label">{{ label }}</span>
      </div>

      <div class="date-picker-grid">
        <button
          v-for="day in weeks.flat()"
          :key="day.getTime()"
          type="button"
          class="date-cell"
          :class="{
            outside: !isCurrentMonth(day),
            selected: isSameDay(day, selectedDate),
            disabled: isDisabled(day)
          }"
          :disabled="isDisabled(day)"
          @click.stop="pickDay(day)"
        >
          {{ day.getDate() }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.date-picker {
  position: relative;
}

.date-picker-trigger {
  width: 100%;
  height: 42px;
  padding: 0 12px;

  display: flex;
  align-items: center;
  gap: 8px;

  background: #fff;
  border: 1px solid #d8dee9;
  border-radius: 8px;

  color: #1f2937;
  font-size: 13px;
  font-family: inherit;

  cursor: pointer;
  transition: 0.15s;
}

.date-picker-trigger:hover {
  border-color: #a100d4;
}

.date-picker-trigger span.placeholder {
  color: #9aa5b5;
}

.date-picker-panel {
  position: absolute;
  z-index: 20;
  top: calc(100% + 6px);
  left: 0;

  width: 260px;
  padding: 12px;

  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.12);
}

.date-picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  margin-bottom: 8px;
}

.date-picker-header strong {
  font-size: 13px;
  color: #1f2937;
}

.nav-button {
  width: 26px;
  height: 26px;

  display: grid;
  place-items: center;

  background: none;
  border: none;
  border-radius: 6px;

  color: #4b5563;
  cursor: pointer;
}

.nav-button:hover {
  background: #f1f5f9;
}

.date-picker-weekdays,
.date-picker-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.date-picker-weekdays span {
  text-align: center;
  font-size: 10px;
  color: #94a3b8;
  padding-bottom: 4px;
}

.date-cell {
  height: 30px;

  display: grid;
  place-items: center;

  background: none;
  border: none;
  border-radius: 6px;

  font-size: 12px;
  color: #1f2937;

  cursor: pointer;
}

.date-cell:hover:not(.disabled) {
  background: #f1e6fb;
}

.date-cell.outside {
  color: #cbd5e1;
}

.date-cell.selected {
  background: #a100d4;
  color: #fff;
}

.date-cell.disabled {
  color: #d5dae2;
  cursor: not-allowed;
}
</style>
