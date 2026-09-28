<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { Download, Eye, FileText, Loader2, RefreshCw, X } from 'lucide-vue-next'

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

function exportParams() {
  const params = new URLSearchParams({ style: style.value, scope: scope.value })

  if (!allYears.value) {
    params.set('years', selectedYears.value.join(','))
  }

  return params
}

// ใช้ร่วมกันทั้งดาวน์โหลดและดูตัวอย่าง: สร้าง PDF ตามตัวเลือกปัจจุบัน
async function fetchTranscript() {
  const response = await fetch(`${API_BASE}/api/student/me/transcript/export?${exportParams()}`, {
    headers: studentHeaders()
  })

  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(data?.detail || t.value.studentTranscript.downloadError)
  }

  return {
    blob: await response.blob(),
    filename: filenameFromDisposition(
      response.headers.get('content-disposition') || '',
      `transcript-${style.value}.pdf`
    )
  }
}

function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()

  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

async function downloadTranscript() {
  if (!canDownload.value) return

  downloading.value = true
  downloadError.value = ''

  try {
    const { blob, filename } = await fetchTranscript()
    saveBlob(blob, filename)
  } catch (error) {
    downloadError.value = error.message || t.value.studentTranscript.downloadError
  } finally {
    downloading.value = false
  }
}


/* =========================
   ดูตัวอย่าง
========================= */

const previewButton = ref(null)
const previewCloseButton = ref(null)
const previewOpen = ref(false)
const previewLoading = ref(false)
const previewError = ref('')
const previewUrl = ref('')
const previewFile = ref(null)
const previewNotice = ref('')

// ปิด popup ระหว่างโหลดแล้วเปิดใหม่: ผลของคำขอเก่าต้องไม่ทับของใหม่
let previewRequest = 0

// iPhone/iPad แสดง PDF ใน iframe ได้แค่หน้าแรกและเลื่อนไม่ได้ ส่วน Android ไม่มีตัวแสดง PDF ในหน้าเว็บ
// จึงเปิดในแท็บใหม่แทน (iPadOS รายงานตัวเองเป็น Mac จึงดู maxTouchPoints ด้วย)
function shouldOpenPreviewInNewTab() {
  const ua = navigator.userAgent || ''
  const iOS = /iPad|iPhone|iPod/.test(ua) ||
    (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1)

  return iOS || /Android/i.test(ua) || navigator.pdfViewerEnabled === false
}

function releasePreview() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  previewFile.value = null
}

function onPreviewKeydown(event) {
  if (event.key === 'Escape') closePreview()
}

async function openPreviewInNewTab() {
  // เปิดแท็บก่อน await เพื่อไม่ให้ browser บล็อก popup
  const tab = window.open('', '_blank')

  if (!tab) {
    previewNotice.value = t.value.studentTranscript.previewPopupBlocked
    return
  }

  previewLoading.value = true
  previewNotice.value = ''
  downloadError.value = ''

  try {
    const { blob } = await fetchTranscript()
    const url = URL.createObjectURL(blob)
    tab.location.href = url
    // แท็บใหม่ใช้ URL นี้อยู่ ปล่อยทีหลัง
    setTimeout(() => URL.revokeObjectURL(url), 60000)
  } catch (error) {
    tab.close()
    downloadError.value = error.message || t.value.studentTranscript.downloadError
  } finally {
    previewLoading.value = false
  }
}

async function openPreview() {
  if (!canDownload.value || previewLoading.value) return

  if (shouldOpenPreviewInNewTab()) {
    await openPreviewInNewTab()
    return
  }

  const request = ++previewRequest

  releasePreview()
  previewError.value = ''
  previewNotice.value = ''
  previewLoading.value = true
  previewOpen.value = true
  document.addEventListener('keydown', onPreviewKeydown)
  document.body.style.overflow = 'hidden'

  await nextTick()
  previewCloseButton.value?.focus()

  try {
    const file = await fetchTranscript()

    if (request !== previewRequest) return

    previewFile.value = file
    // zoom=100: เปิดที่ 100% เสมอ ไม่ขยายตามความกว้างจอ (ผู้ใช้ยังซูมเองได้)
    previewUrl.value = `${URL.createObjectURL(file.blob)}#zoom=100`
  } catch (error) {
    if (request !== previewRequest) return
    previewError.value = error.message || t.value.studentTranscript.downloadError
  } finally {
    if (request === previewRequest) previewLoading.value = false
  }
}

function closePreview() {
  if (!previewOpen.value) return

  previewRequest++
  previewOpen.value = false
  previewLoading.value = false
  releasePreview()
  document.removeEventListener('keydown', onPreviewKeydown)
  document.body.style.overflow = ''
  previewButton.value?.focus()
}

function downloadFromPreview() {
  if (previewFile.value) {
    saveBlob(previewFile.value.blob, previewFile.value.filename)
  }
}

const previewSummary = computed(() => {
  const styleLabel = styleCards.value.find((card) => card.key === style.value)?.title || style.value
  const years = allYears.value
    ? t.value.studentTranscript.allYears
    : selectedYears.value.map((level) => `${t.value.studentTranscript.yearPrefix} ${level}`).join(', ')

  return `${styleLabel} · ${scopeLabels.value[scope.value]} · ${years}`
})

onBeforeUnmount(closePreview)

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

        <div class="action-buttons">
          <button
            ref="previewButton"
            type="button"
            class="secondary-btn"
            :disabled="!canDownload || previewLoading"
            data-testid="preview"
            @click="openPreview"
          >
            <Loader2 v-if="previewLoading && !previewOpen" :size="17" class="spin" />
            <Eye v-else :size="17" />
            {{ t.studentTranscript.preview }}
          </button>

          <button type="submit" class="primary-btn" :disabled="!canDownload" data-testid="download">
            <Download :size="17" />
            {{ downloading ? t.studentTranscript.downloading : t.studentTranscript.download }}
          </button>
        </div>
      </div>

      <p v-if="previewNotice" class="error-text" role="alert">{{ previewNotice }}</p>
    </form>

    <!-- popup ดูตัวอย่าง PDF: คลิกนอกกรอบ / Esc / ปุ่มปิด = ปิด -->
    <div
      v-if="previewOpen"
      class="preview-backdrop"
      data-testid="preview-backdrop"
      @click.self="closePreview"
    >
      <div
        class="preview-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="preview-title"
      >
        <div class="preview-header">
          <div class="preview-heading">
            <h2 id="preview-title">{{ t.studentTranscript.previewTitle }}</h2>
            <p>{{ previewSummary }}</p>
          </div>

          <div class="preview-actions">
            <button
              type="button"
              class="primary-btn"
              :disabled="!previewFile"
              :aria-label="t.studentTranscript.download"
              data-testid="preview-download"
              @click="downloadFromPreview"
            >
              <Download :size="17" />
              <span class="label">{{ t.studentTranscript.download }}</span>
            </button>

            <button
              ref="previewCloseButton"
              type="button"
              class="icon-btn"
              :aria-label="t.studentTranscript.close"
              :title="t.studentTranscript.close"
              data-testid="preview-close"
              @click="closePreview"
            >
              <X :size="20" />
            </button>
          </div>
        </div>

        <div class="preview-body">
          <div v-if="previewLoading" class="preview-status" data-testid="preview-loading">
            <Loader2 :size="28" class="spin" />
            <span>{{ t.studentTranscript.previewLoading }}</span>
          </div>

          <div v-else-if="previewError" class="preview-status error" role="alert">
            <span>{{ previewError }}</span>
            <button type="button" class="ghost-btn" @click="openPreview">
              <RefreshCw :size="15" />
              {{ t.studentTranscript.retry }}
            </button>
          </div>

          <iframe
            v-else-if="previewUrl"
            :src="previewUrl"
            :title="t.studentTranscript.previewTitle"
            data-testid="preview-frame"
          ></iframe>
        </div>
      </div>
    </div>
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

.action-buttons {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.secondary-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border: 1px solid #6d28d9;
  border-radius: 9px;
  background: #fff;
  color: #6d28d9;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.secondary-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.spin {
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* popup ดูตัวอย่าง */
.preview-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  padding: 24px;
  background: rgba(15, 23, 42, 0.6);
  display: flex;
  box-sizing: border-box;
}

.preview-dialog {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.35);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  border-bottom: 1px solid #e8ecf3;
}

.preview-heading {
  min-width: 0;
}

.preview-heading h2 {
  margin: 0 0 2px;
  color: #172d68;
  font-size: 17px;
}

.preview-heading p {
  margin: 0;
  color: #6b7a96;
  font-size: 13px;
}

.preview-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 1px solid #d7deeb;
  border-radius: 9px;
  background: #fff;
  color: #33415f;
  cursor: pointer;
}

.icon-btn:hover {
  background: #f5f7fb;
}

.preview-body {
  position: relative;
  flex: 1;
  min-height: 0;
  background: #525659;
}

.preview-body iframe {
  width: 100%;
  height: 100%;
  border: 0;
  display: block;
}

.preview-status {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: #f5f7fb;
  color: #33415f;
}

.preview-status.error {
  color: #b42318;
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

  .action-buttons {
    flex-direction: column-reverse;
  }

  .action-buttons .secondary-btn {
    justify-content: center;
  }

  .preview-backdrop {
    padding: 0;
  }

  .preview-dialog {
    border-radius: 0;
  }

  .preview-header {
    padding: 10px 12px;
  }

  .preview-actions .label {
    display: none;
  }
}
</style>
