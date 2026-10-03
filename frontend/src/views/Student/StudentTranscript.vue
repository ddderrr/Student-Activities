<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  Building2,
  Check,
  Download,
  Eye,
  FileText,
  Globe2,
  GraduationCap,
  Layers,
  Loader2,
  RefreshCw,
  X
} from 'lucide-vue-next'

import { useLanguage } from '../../composables/useLanguage'
import { API_BASE, studentHeaders } from '../../constants/currentStudent'

const { t, currentLanguage } = useLanguage()

const loading = ref(true)
const loadError = ref('')
const options = ref(null)

const style = ref('A')
const scope = ref('all')
// ภาษาของเอกสาร PDF (ทั้งฉบับ) เริ่มตามภาษาของหน้าเว็บ เปลี่ยนเองได้
// เอกสารรวมทุกชั้นปีเสมอ (ไม่มีตัวเลือกชั้นปีแล้ว)
const documentLanguage = ref(currentLanguage.value === 'EN' ? 'en' : 'th')

const downloading = ref(false)
const downloadError = ref('')

const languageCards = computed(() => [
  { key: 'th', badge: 'ไทย', title: t.value.studentTranscript.languageThai, note: t.value.studentTranscript.languageThaiNote },
  { key: 'en', badge: 'EN', title: t.value.studentTranscript.languageEnglish, note: t.value.studentTranscript.languageEnglishNote }
])

const previewLabel = computed(() =>
  documentLanguage.value === 'en' ? t.value.studentTranscript.previewEnglish : t.value.studentTranscript.previewThai
)

const downloadLabel = computed(() =>
  documentLanguage.value === 'en' ? t.value.studentTranscript.downloadEnglish : t.value.studentTranscript.downloadThai
)

const scopeLabels = computed(() => ({
  all: t.value.studentTranscript.scopeAll,
  major: t.value.studentTranscript.scopeMajor,
  faculty: t.value.studentTranscript.scopeFaculty,
  external: t.value.studentTranscript.scopeExternal
}))

const scopeIcons = {
  all: Layers,
  major: GraduationCap,
  faculty: Building2,
  external: Globe2
}

const styleCards = computed(() => [
  { key: 'A', title: t.value.studentTranscript.styleA, description: t.value.studentTranscript.styleADescription },
  { key: 'B', title: t.value.studentTranscript.styleB, description: t.value.studentTranscript.styleBDescription }
])

const canDownload = computed(() => !downloading.value)

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
  return new URLSearchParams({ style: style.value, scope: scope.value, lang: documentLanguage.value })
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
      `transcript-${style.value}-${documentLanguage.value}.pdf`
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
  const languageLabel = languageCards.value.find((card) => card.key === documentLanguage.value)?.title

  return `${styleLabel} · ${scopeLabels.value[scope.value]} · ${t.value.studentTranscript.allYears} · ${languageLabel}`
})

onBeforeUnmount(closePreview)

onMounted(loadOptions)
</script>

<template>
  <div class="transcript-page">
    <div class="transcript-container">
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
        <div class="section-heading">
          <span class="step" aria-hidden="true">1</span>
          <h2>{{ t.studentTranscript.styleTitle }}</h2>
        </div>

        <div class="style-grid">
          <label
            v-for="card in styleCards"
            :key="card.key"
            class="style-card"
            :class="{ selected: style === card.key }"
            :data-testid="`style-${card.key}`"
          >
            <input v-model="style" type="radio" name="style" :value="card.key">

            <span class="check-mark" aria-hidden="true"><Check :size="14" :stroke-width="3" /></span>

            <!-- ภาพย่อโครงเอกสาร -->
            <span class="thumb-stage" aria-hidden="true">
              <span class="thumb" :class="`thumb-${card.key}`">
                <span class="thumb-head">
                  <span class="thumb-seal"></span>
                  <span class="thumb-title"></span>
                  <span class="thumb-title short"></span>
                </span>
                <span class="thumb-info">
                  <span></span><span></span><span></span><span></span>
                </span>
                <span class="thumb-table">
                  <span v-for="row in 5" :key="row"></span>
                </span>
                <span class="thumb-skills">
                  <span v-for="skill in 6" :key="skill"></span>
                </span>
                <span class="thumb-foot">
                  <span class="thumb-qr"></span>
                  <span class="thumb-sign"></span>
                </span>
              </span>
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
        <div class="section-heading">
          <span class="step" aria-hidden="true">2</span>
          <h2>{{ t.studentTranscript.scopeTitle }}</h2>
        </div>

        <div class="choice-list">
          <label
            v-for="item in options.scopes"
            :key="item.key"
            class="choice"
            :class="{ selected: scope === item.key, empty: !item.count }"
          >
            <input v-model="scope" type="radio" name="scope" :value="item.key">

            <span class="choice-icon" aria-hidden="true">
              <component :is="scopeIcons[item.key] || Layers" :size="20" />
            </span>

            <span class="choice-text">
              <strong>{{ scopeLabels[item.key] || item.label }}</strong>
              <small v-if="item.key === 'major' && options.major">{{ options.major }}</small>
            </span>

            <span class="count">
              <b>{{ item.count }}</b>
              {{ t.studentTranscript.activitiesUnit }}
            </span>
          </label>
        </div>
      </section>

      <!-- ภาษาของเอกสาร (ทุกชั้นปีเสมอ ไม่มีตัวเลือกชั้นปี) -->
      <section class="option-section">
        <div class="section-heading">
          <span class="step" aria-hidden="true">3</span>
          <div>
            <h2>{{ t.studentTranscript.languageTitle }}</h2>
            <p class="muted">{{ t.studentTranscript.languageHint }}</p>
          </div>
        </div>

        <div class="choice-list language-list">
          <label
            v-for="card in languageCards"
            :key="card.key"
            class="choice"
            :class="{ selected: documentLanguage === card.key }"
            :data-testid="`language-${card.key}`"
          >
            <input v-model="documentLanguage" type="radio" name="document-language" :value="card.key">

            <span class="choice-icon language-badge" aria-hidden="true">{{ card.badge }}</span>

            <span class="choice-text">
              <strong>{{ card.title }}</strong>
              <small>{{ card.note }}</small>
            </span>
          </label>
        </div>
      </section>

      <div class="actions">
        <p class="summary">{{ previewSummary }}</p>

        <div class="action-buttons">
          <button
            ref="previewButton"
            type="button"
            class="secondary-btn"
            :disabled="!canDownload || previewLoading"
            data-testid="preview"
            @click="openPreview"
          >
            <Loader2 v-if="previewLoading && !previewOpen" :size="19" class="spin" />
            <Eye v-else :size="19" />
            {{ previewLabel }}
          </button>

          <button type="submit" class="primary-btn" :disabled="!canDownload" data-testid="download">
            <Download :size="19" />
            {{ downloading ? t.studentTranscript.downloading : downloadLabel }}
          </button>
        </div>

        <p class="muted demo-note">
          <FileText :size="15" />
          {{ t.studentTranscript.demoNote }}
        </p>

        <p v-if="downloadError" class="error-text" role="alert">{{ downloadError }}</p>
        <p v-if="previewNotice" class="error-text" role="alert">{{ previewNotice }}</p>
      </div>
    </form>
    </div>

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
  padding: 32px 32px 48px;
  box-sizing: border-box;
  background: #f5f7fb;
  color: #17213c;
  font-size: var(--fs-body);
}

/* จัดกลางหน้า กว้างพอให้การ์ดสองคอลัมน์ไม่อึดอัด */
.transcript-container {
  max-width: 1120px;
  margin: 0 auto;
}

.page-heading {
  margin-bottom: 24px;
}

.page-heading h1 {
  margin: 0 0 6px;
  color: #172d68;
  font-size: 28px;
}

.page-heading p,
.muted {
  margin: 0;
  color: #8793aa;
  font-size: var(--fs-body);
}

.options-card,
.error-card {
  border: 1px solid #dfe4ee;
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(23, 45, 104, 0.04), 0 8px 24px rgba(23, 45, 104, 0.05);
  box-sizing: border-box;
}

.options-card {
  overflow: hidden;
}

.error-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 24px 28px;
  color: #b42318;
}

.option-section {
  padding: 32px 36px;
}

.option-section + .option-section {
  border-top: 1px solid #edf0f6;
}

.section-heading {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 20px;
}

.section-heading h2 {
  margin: 0;
  color: #172d68;
  font-size: 21px;
  line-height: 32px;
}

.section-heading .muted {
  margin-top: 2px;
}

.step {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f1eafd;
  color: #6d28d9;
  font-size: var(--fs-small);
  font-weight: 700;
}

input[type="radio"] {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

/* การ์ดที่เลือกได้ (รูปแบบ + ประเภท) ใช้สถานะร่วมกัน */
.style-card,
.choice {
  position: relative;
  border: 1.5px solid #dfe4ee;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.18s, box-shadow 0.18s, background-color 0.18s;
}

.style-card:hover,
.choice:hover {
  border-color: #c4b1ef;
}

.style-card.selected,
.choice.selected {
  border-color: #6d28d9;
  box-shadow: 0 0 0 4px rgba(109, 40, 217, 0.1);
}

.style-card:focus-within,
.choice:focus-within {
  outline: 2px solid #6d28d9;
  outline-offset: 2px;
}

/* รูปแบบเอกสาร */
.style-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.style-card {
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  overflow: hidden;
}

.check-mark {
  position: absolute;
  top: 14px;
  right: 14px;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: 1.5px solid #cfd6e4;
  border-radius: 50%;
  background: #fff;
  color: transparent;
  transition: 0.18s;
}

.selected .check-mark {
  border-color: #6d28d9;
  background: #6d28d9;
  color: #fff;
}

.thumb-stage {
  display: flex;
  justify-content: center;
  padding: 26px 20px;
  overflow: hidden;
  background: linear-gradient(180deg, #f3f5fa 0%, #e9edf5 100%);
  transition: background 0.18s;
}

.style-card.selected .thumb-stage {
  background: linear-gradient(180deg, #f6f1fe 0%, #ece3fc 100%);
}

/* หน้า A4 ย่อ (สัดส่วน 1:1.414) */
.thumb {
  display: flex;
  flex-direction: column;
  gap: 9px;
  width: 160px;
  height: 226px;
  padding: 14px 15px;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 6px 20px rgba(23, 45, 104, 0.14);
  box-sizing: border-box;
  transition: transform 0.2s;
}

.style-card:hover .thumb,
.style-card.selected .thumb {
  transform: translateY(-4px);
}

/* :where = specificity 0 ไม่ทับ display: flex/grid ของแต่ละส่วนด้านล่าง */
:where(.thumb span) {
  display: block;
}

.thumb-head {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.thumb-title {
  width: 70%;
  height: 5px;
  border-radius: 2px;
  background: #aab4c8;
}

.thumb-title.short {
  width: 45%;
  height: 3px;
  background: #cfd6e4;
}

.thumb-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 10px;
}

.thumb-info span {
  height: 3px;
  border-radius: 2px;
  background: #dde2ec;
}

.thumb-table {
  display: flex;
  flex-direction: column;
}

.thumb-table span {
  height: 9px;
}

.thumb-skills {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
}

.thumb-foot {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-top: auto;
}

.thumb-sign {
  width: 42%;
  height: 3px;
  border-radius: 2px;
  background: #aab4c8;
}

/* แบบ A คลาสสิก: ตราตรงกลาง ตารางมีเส้นขอบ คะแนนเป็นช่องตัวเลข */
.thumb-A .thumb-seal {
  width: 22px;
  height: 22px;
  border: 2px solid #9aa6bd;
  border-radius: 50%;
}

.thumb-A .thumb-table {
  border: 1px solid #9aa6bd;
}

.thumb-A .thumb-table span + span {
  border-top: 1px solid #c3cad8;
}

.thumb-A .thumb-table span:first-child {
  background: #e4e8f0;
}

.thumb-A .thumb-skills span {
  height: 11px;
  border: 1px solid #b6bfd0;
  border-radius: 2px;
}

.thumb-A .thumb-qr {
  display: none;
}

/* แบบ B ทันสมัย: แถบสีหัวกระดาษ คะแนนเป็นแถบ ตารางโล่ง มี QR */
.thumb-B {
  padding-top: 0;
}

.thumb-B .thumb-head {
  align-items: flex-start;
  margin: 0 -15px;
  padding: 12px 15px 10px;
  border-radius: 6px 6px 0 0;
  background: #23306b;
}

.thumb-B .thumb-seal {
  display: none;
}

.thumb-B .thumb-title {
  background: rgba(255, 255, 255, 0.85);
}

.thumb-B .thumb-title.short {
  background: rgba(255, 255, 255, 0.45);
}

.thumb-B .thumb-table span:nth-child(odd) {
  background: #f0f2f7;
}

.thumb-B .thumb-table span:first-child {
  background: #d9deea;
}

.thumb-B .thumb-skills {
  grid-template-columns: 1fr 1fr;
}

.thumb-B .thumb-skills span {
  height: 5px;
  border-radius: 3px;
  background: linear-gradient(90deg, #4f5fb3 var(--fill, 65%), #e3e7f0 var(--fill, 65%));
}

.thumb-B .thumb-skills span:nth-child(2) { --fill: 85%; }
.thumb-B .thumb-skills span:nth-child(3) { --fill: 45%; }
.thumb-B .thumb-skills span:nth-child(4) { --fill: 75%; }
.thumb-B .thumb-skills span:nth-child(5) { --fill: 55%; }

.thumb-B .thumb-qr {
  width: 22px;
  height: 22px;
  border-radius: 2px;
  background:
    conic-gradient(#23306b 25%, #fff 0 50%, #23306b 0 75%, #fff 0) 0 0 / 8px 8px;
  outline: 1px solid #23306b;
}

.style-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 18px 22px 20px;
  border-top: 1px solid #edf0f6;
}

.style-text strong {
  color: #172d68;
  font-size: var(--fs-lead);
}

.style-text small {
  color: #6b7a96;
  font-size: var(--fs-small);
  line-height: 1.6;
}

/* ประเภทกิจกรรม */
.choice-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-auto-rows: 1fr;
  gap: 14px;
}

.choice {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 84px;
  padding: 16px 20px;
  border-radius: 14px;
}

.choice-icon {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: #f1f3f8;
  color: #52617d;
  transition: 0.18s;
}

.choice.selected .choice-icon {
  background: #6d28d9;
  color: #fff;
}

.choice-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.choice-text strong {
  color: #172d68;
  font-weight: 600;
}

.choice-text small {
  color: #6b7a96;
  font-size: var(--fs-small);
}

.count {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  color: #8793aa;
  font-size: var(--fs-caption);
  line-height: 1.3;
}

.count b {
  color: #172d68;
  font-size: 24px;
  font-weight: 700;
}

.choice.selected .count b {
  color: #6d28d9;
}

.language-badge {
  font-size: var(--fs-small);
  font-weight: 700;
}

.choice.empty .count b {
  color: #b3bccd;
}

/* ปุ่ม */
.actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 32px 36px 36px;
  border-top: 1px solid #edf0f6;
  background: #fafbfd;
  text-align: center;
}

.summary {
  margin: 0;
  color: #52617d;
  font-weight: 600;
}

.demo-note {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-small);
}

.primary-btn,
.ghost-btn,
.secondary-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-radius: 12px;
  font: inherit;
  cursor: pointer;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 14px;
}

.action-buttons .primary-btn,
.action-buttons .secondary-btn {
  min-width: 220px;
  min-height: 54px;
  padding: 14px 28px;
  font-size: var(--fs-lead);
}

.primary-btn {
  flex-shrink: 0;
  padding: 11px 20px;
  border: none;
  background: #6d28d9;
  color: #fff;
  font-weight: 600;
  transition: background-color 0.18s, box-shadow 0.18s;
}

.action-buttons .primary-btn {
  box-shadow: 0 6px 16px rgba(109, 40, 217, 0.3);
}

.primary-btn:not(:disabled):hover {
  background: #5b21b6;
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

.secondary-btn {
  padding: 10px 18px;
  border: 1.5px solid #6d28d9;
  background: #fff;
  color: #6d28d9;
  font-weight: 600;
  transition: background-color 0.18s;
}

.secondary-btn:not(:disabled):hover {
  background: #f6f1fe;
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
  font-size: 20px;
}

.preview-heading p {
  margin: 0;
  color: #6b7a96;
  font-size: var(--fs-body);
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
  margin: 0;
  color: #b42318;
  font-size: var(--fs-body);
}

@media (max-width: 900px) {
  .option-section {
    padding: 28px 24px;
  }

  .actions {
    padding: 28px 24px 30px;
  }


}

@media (max-width: 720px) {
  .transcript-page {
    padding: 20px 16px 32px;
  }

  .page-heading h1 {
    font-size: 24px;
  }

  .option-section {
    padding: 22px 16px;
  }

  .actions {
    padding: 22px 16px 24px;
  }

  .style-grid,
  .choice-list {
    grid-template-columns: 1fr;
  }

  .style-grid {
    gap: 14px;
  }

  /* scale ไม่ย่อกล่อง layout จึงล็อกความสูง stage = 226 * 0.8 + padding */
  .thumb-stage {
    height: 221px;
    padding: 20px;
    box-sizing: border-box;
  }

  .thumb {
    transform: scale(0.8);
    transform-origin: top center;
  }

  .style-card:hover .thumb,
  .style-card.selected .thumb {
    transform: scale(0.8) translateY(-4px);
  }

  .choice {
    min-height: 72px;
    padding: 14px 16px;
  }


  .action-buttons {
    flex-direction: column-reverse;
    align-self: stretch;
  }

  .action-buttons .primary-btn,
  .action-buttons .secondary-btn {
    min-width: 0;
    width: 100%;
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
