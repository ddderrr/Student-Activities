<script setup>
import { computed, onMounted, ref } from 'vue'
import { Download, FileText, RefreshCw } from 'lucide-vue-next'

import { useLanguage } from '../../composables/useLanguage'
import { API_BASE, studentHeaders } from '../../constants/currentStudent'

const { t } = useLanguage()

// หลักสูตรปกติ 4 ปี: แสดงช่องปี 1-4 เสมอ ปีที่เกินชั้นปีปัจจุบันกดไม่ได้
const DISPLAY_YEAR_LEVELS = 4

const loading = ref(true)
const loadError = ref('')
const options = ref(null)

const style = ref('A')
const scope = ref('all')
const allYears = ref(true)
const selectedYears = ref([])

const downloading = ref(false)
const downloadError = ref('')

const currentYearLevel = computed(() => options.value?.current_year_level ?? null)
const allowedYears = computed(() => options.value?.allowed_year_levels || [])

const yearChoices = computed(() => {
  const count = Math.max(DISPLAY_YEAR_LEVELS, currentYearLevel.value || 0)
  return Array.from({ length: count }, (_, index) => index + 1)
})

const scopeLabels = computed(() => ({
  all: t.value.studentTranscript.scopeAll,
  major: t.value.studentTranscript.scopeMajor,
  faculty: t.value.studentTranscript.scopeFaculty,
  external: t.value.studentTranscript.scopeExternal
}))

const styleCards = computed(() => [
  { key: 'A', title: t.value.studentTranscript.styleA, description: t.value.studentTranscript.styleADescription },
  { key: 'B', title: t.value.studentTranscript.styleB, description: t.value.studentTranscript.styleBDescription }
])

const canDownload = computed(() =>
  !downloading.value && (allYears.value || selectedYears.value.length > 0)
)

function toggleYear(level) {
  if (!allowedYears.value.includes(level)) return

  selectedYears.value = selectedYears.value.includes(level)
    ? selectedYears.value.filter((item) => item !== level)
    : [...selectedYears.value, level].sort((a, b) => a - b)

  allYears.value = selectedYears.value.length === 0
}

function chooseAllYears() {
  allYears.value = true
  selectedYears.value = []
}

async function loadOptions() {
  loading.value = true
  loadError.value = ''

  try {
    const response = await fetch(`${API_BASE}/api/student/me/transcript/options`, {
      headers: studentHeaders()
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    options.value = await response.json()
  } catch {
    loadError.value = t.value.studentTranscript.loadError
  } finally {
    loading.value = false
  }
}

function filenameFromDisposition(disposition, fallback) {
  return disposition.match(/filename="?([^";]+)"?/i)?.[1] || fallback
}

async function downloadTranscript() {
  if (!canDownload.value) return

  downloading.value = true
  downloadError.value = ''

  const params = new URLSearchParams({ style: style.value, scope: scope.value })

  if (!allYears.value) {
    params.set('years', selectedYears.value.join(','))
  }

  try {
    const response = await fetch(`${API_BASE}/api/student/me/transcript/export?${params}`, {
      headers: studentHeaders()
    })

    if (!response.ok) {
      const data = await response.json().catch(() => null)
      throw new Error(data?.detail || t.value.studentTranscript.downloadError)
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')

    link.href = url
    link.download = filenameFromDisposition(
      response.headers.get('content-disposition') || '',
      `transcript-${style.value}.pdf`
    )
    document.body.appendChild(link)
    link.click()
    link.remove()

    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (error) {
    downloadError.value = error.message || t.value.studentTranscript.downloadError
  } finally {
    downloading.value = false
  }
}

onMounted(loadOptions)
</script>

<template>
  <div class="transcript-page">
    <div class="page-heading">
      <h1>{{ t.studentTranscript.title }}</h1>
      <p>{{ t.studentTranscript.subtitle }}</p>
    </div>

    <p v-if="loading" class="muted">{{ t.studentTranscript.loading }}</p>

    <div v-else-if="loadError" class="error-card" role="alert">
      <span>{{ loadError }}</span>
      <button type="button" class="ghost-btn" @click="loadOptions">
        <RefreshCw :size="15" />
        {{ t.studentTranscript.retry }}
      </button>
    </div>

    <form v-else class="options-card" @submit.prevent="downloadTranscript">
      <!-- รูปแบบเอกสาร -->
      <section class="option-section">
        <h2>{{ t.studentTranscript.styleTitle }}</h2>

        <div class="style-grid">
          <label
            v-for="card in styleCards"
            :key="card.key"
            class="style-card"
            :class="{ selected: style === card.key }"
            :data-testid="`style-${card.key}`"
          >
            <input v-model="style" type="radio" name="style" :value="card.key">

            <!-- ภาพย่อโครงเอกสาร -->
            <span class="thumb" :class="`thumb-${card.key}`" aria-hidden="true">
              <span class="thumb-head"></span>
              <span class="thumb-line"></span>
              <span class="thumb-line short"></span>
              <span class="thumb-table"></span>
              <span class="thumb-sign"></span>
            </span>

            <span class="style-text">
              <strong>{{ card.title }}</strong>
              <small>{{ card.description }}</small>
            </span>
          </label>
        </div>
      </section>

      <!-- ประเภทกิจกรรม -->
      <section class="option-section">
        <h2>{{ t.studentTranscript.scopeTitle }}</h2>

        <div class="choice-list">
          <label
            v-for="item in options.scopes"
            :key="item.key"
            class="choice"
            :class="{ selected: scope === item.key }"
          >
            <input v-model="scope" type="radio" name="scope" :value="item.key">
            <span>
              {{ scopeLabels[item.key] || item.label }}
              <small v-if="item.key === 'major' && options.major">({{ options.major }})</small>
            </span>
            <span class="count">{{ item.count }} {{ t.studentTranscript.activitiesUnit }}</span>
          </label>
        </div>
      </section>

      <!-- ชั้นปี -->
      <section class="option-section">
        <h2>{{ t.studentTranscript.yearTitle }}</h2>

        <p v-if="currentYearLevel" class="muted">
          {{ t.studentTranscript.currentYear }} {{ currentYearLevel }}
          · {{ t.studentTranscript.yearRule }}
        </p>
        <p v-else class="muted" data-testid="year-unknown">
          {{ t.studentTranscript.yearUnknown }}
        </p>

        <div class="year-list">
          <button
            type="button"
            class="year-chip"
            :class="{ selected: allYears }"
            @click="chooseAllYears"
          >
            {{ t.studentTranscript.allYears }}
          </button>

          <button
            v-for="level in yearChoices"
            :key="level"
            type="button"
            class="year-chip"
            :class="{ selected: !allYears && selectedYears.includes(level) }"
            :disabled="!allowedYears.includes(level)"
            :title="allowedYears.includes(level) ? '' : t.studentTranscript.yearDisabled"
            :data-testid="`year-${level}`"
            @click="toggleYear(level)"
          >
            {{ t.studentTranscript.yearPrefix }} {{ level }}
          </button>
        </div>
      </section>

      <p v-if="downloadError" class="error-text" role="alert">{{ downloadError }}</p>

      <div class="actions">
        <p class="muted">
          <FileText :size="15" />
          {{ t.studentTranscript.demoNote }}
        </p>

        <button type="submit" class="primary-btn" :disabled="!canDownload" data-testid="download">
          <Download :size="17" />
          {{ downloading ? t.studentTranscript.downloading : t.studentTranscript.download }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.transcript-page {
  width: 100%;
  min-height: 100vh;
  padding: 24px 28px 38px;
  box-sizing: border-box;
  background: #f5f7fb;
  color: #17213c;
  font-size: 15px;
}

.page-heading h1 {
  margin: 0 0 5px;
  color: #172d68;
  font-size: 25px;
}

.page-heading p,
.muted {
  margin: 0;
  color: #8793aa;
  font-size: 13.5px;
}

.page-heading {
  margin-bottom: 18px;
}

.options-card,
.error-card {
  max-width: 920px;
  padding: 24px 26px;
  border: 1px solid #d8deea;
  border-radius: 17px;
  background: #fff;
  box-sizing: border-box;
}

.error-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #b42318;
}

.option-section + .option-section {
  margin-top: 26px;
}

.option-section h2 {
  margin: 0 0 12px;
  color: #172d68;
  font-size: 16px;
}

.option-section .muted {
  margin-bottom: 10px;
}

input[type="radio"] {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

/* รูปแบบเอกสาร */
.style-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.style-card {
  position: relative;
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 14px;
  border: 1px solid #d7deeb;
  border-radius: 12px;
  cursor: pointer;
  transition: 0.2s;
}

.style-card.selected,
.choice.selected {
  border-color: #6d28d9;
  box-shadow: 0 0 0 3px rgba(109, 40, 217, 0.1);
}

.style-card:focus-within,
.choice:focus-within {
  outline: 2px solid #6d28d9;
  outline-offset: 2px;
}

.style-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.style-text strong {
  color: #172d68;
}

.style-text small {
  color: #6b7a96;
  line-height: 1.45;
}

.thumb {
  position: relative;
  flex-shrink: 0;
  width: 64px;
  height: 86px;
  padding: 7px 6px;
  border: 1px solid #d7deeb;
  border-radius: 4px;
  background: #fff;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.thumb span {
  display: block;
  background: #cfd6e4;
  border-radius: 1px;
}

.thumb-head { height: 10px; }
.thumb-line { height: 3px; }
.thumb-line.short { width: 60%; }
.thumb-table { flex: 1; }
.thumb-sign { height: 3px; width: 45%; align-self: flex-end; }

.thumb-A .thumb-head {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  align-self: center;
  background: #aab4c8;
}

.thumb-A .thumb-table {
  background: repeating-linear-gradient(#fff 0 5px, #9aa6bd 5px 6px);
  border: 1px solid #9aa6bd;
}

.thumb-B {
  padding-top: 0;
}

.thumb-B .thumb-head {
  height: 16px;
  margin: 0 -6px 2px;
  border-radius: 3px 3px 0 0;
  background: #23306b;
}

.thumb-B .thumb-table {
  background: repeating-linear-gradient(#fff 0 6px, #e1e5ee 6px 7px);
}

/* ประเภทกิจกรรม */
.choice-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.choice {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid #d7deeb;
  border-radius: 10px;
  cursor: pointer;
  transition: 0.2s;
}

.choice small {
  color: #6b7a96;
}

.count {
  flex-shrink: 0;
  color: #6b7a96;
  font-size: 13px;
}

/* ชั้นปี */
.year-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.year-chip {
  padding: 8px 16px;
  border: 1px solid #d7deeb;
  border-radius: 999px;
  background: #fff;
  color: #33415f;
  font: inherit;
  font-size: 14px;
  cursor: pointer;
  transition: 0.2s;
}

.year-chip.selected {
  border-color: #6d28d9;
  background: #6d28d9;
  color: #fff;
}

.year-chip:disabled {
  border-style: dashed;
  background: #f5f7fb;
  color: #b3bccd;
  cursor: not-allowed;
}

/* ปุ่ม */
.actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 28px;
  padding-top: 18px;
  border-top: 1px solid #e8ecf3;
}

.actions .muted {
  display: flex;
  align-items: center;
  gap: 6px;
}

.primary-btn,
.ghost-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: 9px;
  font: inherit;
  cursor: pointer;
}

.primary-btn {
  flex-shrink: 0;
  padding: 11px 20px;
  border: none;
  background: #6d28d9;
  color: #fff;
  font-weight: 600;
}

.primary-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.ghost-btn {
  padding: 8px 14px;
  border: 1px solid currentColor;
  background: transparent;
  color: inherit;
}

.error-text {
  margin: 18px 0 0;
  color: #b42318;
  font-size: 14px;
}

@media (max-width: 720px) {
  .transcript-page {
    padding: 18px 16px 30px;
  }

  .options-card {
    padding: 18px 16px;
  }

  .style-grid,
  .choice-list {
    grid-template-columns: 1fr;
  }

  .actions {
    flex-direction: column;
    align-items: stretch;
  }

  .primary-btn {
    justify-content: center;
  }
}
</style>
