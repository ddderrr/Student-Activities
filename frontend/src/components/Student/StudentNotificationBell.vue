<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, BellOff, CheckCheck, CircleCheck, CircleX, Trash2 } from 'lucide-vue-next'

import { useLanguage } from '../../composables/useLanguage'
import { API_BASE, studentHeaders } from '../../constants/currentStudent'

// กระดิ่งแจ้งเตือนของนักศึกษา: ผลการอนุมัติ / ไม่อนุมัติคำขอ (GET /api/student/me/notifications)
// ดึงใหม่ทุก 30 วินาทีตอนแท็บเปิดอยู่ + ตอนกลับมาที่แท็บ + ตอนเปิด dropdown
const POLL_MS = 30_000

const { t, currentLanguage } = useLanguage()
const router = useRouter()

const notifications = ref([])
const unreadCount = ref(0)
const hasMore = ref(false)
const open = ref(false)
const loading = ref(false)
const loadingMore = ref(false)
// ลบทั้งหมด: กดแล้วขึ้นแถวยืนยันก่อน
const confirmingClear = ref(false)
const clearing = ref(false)
const clearError = ref(false)
const loadError = ref(false)
const wrapper = ref(null)
// ใช้คำนวณ "x นาทีที่แล้ว" ใหม่ทุกครั้งที่ poll
const now = ref(Date.now())

let pollTimer = null

const badgeText = computed(() => (unreadCount.value > 99 ? '99+' : String(unreadCount.value)))

async function loadNotifications() {
  if (loading.value) return
  loading.value = true

  try {
    const response = await fetch(`${API_BASE}/api/student/me/notifications`, { headers: studentHeaders() })
    if (!response.ok) throw new Error()
    const data = await response.json()
    applyFirstPage(data.notifications, data.has_more)
    // นับจากทั้งหมดที่ backend (หน้าละ 30 รายการ)
    unreadCount.value = data.unread_count
    loadError.value = false
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
    now.value = Date.now()
  }
}

// หน้าแรกจาก poll: ถ้าผู้ใช้กด "ดูเพิ่มเติม" ไว้แล้ว เก็บรายการที่เก่ากว่าหน้าแรกไว้ด้วย ไม่ให้หายตอนรีเฟรช
function applyFirstPage(page, pageHasMore) {
  const oldestOnPage = page.at(-1)?.id
  const older = oldestOnPage == null ? [] : notifications.value.filter((item) => item.id < oldestOnPage)
  notifications.value = [...page, ...older]
  if (!older.length) hasMore.value = pageHasMore
}

// ดูเพิ่มเติม: หน้าถัดไปที่เก่ากว่ารายการสุดท้ายที่มี
async function loadMore() {
  const last = notifications.value.at(-1)
  if (!last || loadingMore.value) return
  loadingMore.value = true

  try {
    const response = await fetch(`${API_BASE}/api/student/me/notifications?before_id=${last.id}`, { headers: studentHeaders() })
    if (!response.ok) throw new Error()
    const data = await response.json()
    const known = new Set(notifications.value.map((item) => item.id))
    notifications.value.push(...data.notifications.filter((item) => !known.has(item.id)))
    hasMore.value = data.has_more
    unreadCount.value = data.unread_count
  } catch {
    // โหลดไม่สำเร็จ: ปุ่มยังอยู่ให้กดใหม่ได้
  } finally {
    loadingMore.value = false
  }
}

function messageParts(item) {
  const text = t.value.studentNotifications
  let template = item.type === 'approved' ? text.approved : text.rejected
  if (item.source === 'student_request') template = item.type === 'approved' ? text.requestApproved : text.requestRejected
  // แยกข้อความตาม {title} / {reason} เพื่อทำตัวหนาเฉพาะชื่อกิจกรรม
  return template.split(/(\{title\}|\{reason\})/).filter(Boolean).map((part) => {
    if (part === '{title}') return { text: item.title, strong: true }
    if (part === '{reason}') return { text: item.message, strong: false }
    return { text: part, strong: false }
  })
}

function relativeTime(iso) {
  if (!iso) return ''
  const seconds = Math.round((new Date(iso).getTime() - now.value) / 1000)
  if (Math.abs(seconds) < 60) return t.value.studentNotifications.justNow

  const formatter = new Intl.RelativeTimeFormat(currentLanguage.value === 'TH' ? 'th' : 'en', { numeric: 'auto' })
  const units = [['day', 86400], ['hour', 3600], ['minute', 60]]
  const [unit, size] = units.find(([, unitSeconds]) => Math.abs(seconds) >= unitSeconds)
  return formatter.format(Math.round(seconds / size), unit)
}

function toggle() {
  open.value = !open.value
  confirmingClear.value = false
  if (open.value) loadNotifications()
}

function askClear() {
  clearError.value = false
  confirmingClear.value = true
}

async function clearAll() {
  if (clearing.value) return
  clearing.value = true
  clearError.value = false

  try {
    const response = await fetch(`${API_BASE}/api/student/me/notifications`, { method: 'DELETE', headers: studentHeaders() })
    if (!response.ok) throw new Error()
    notifications.value = []
    unreadCount.value = 0
    hasMore.value = false
    confirmingClear.value = false
  } catch {
    clearError.value = true
  } finally {
    clearing.value = false
  }
}

function markRead(item) {
  if (item.read) return
  item.read = true
  unreadCount.value = Math.max(0, unreadCount.value - 1)

  fetch(`${API_BASE}/api/student/me/notifications/${item.id}/read`, { method: 'PATCH', headers: studentHeaders() })
    .then((response) => { if (!response.ok) throw new Error() })
    // บันทึกไม่สำเร็จ: ดึงสถานะจริงกลับมา
    .catch(loadNotifications)
}

function openNotification(item) {
  open.value = false
  markRead(item)
  // link = /student/activities?open=ID (เปิดคำขอนั้นในแท็บรายการที่ส่ง) คำขอบางประเภทไม่มีหน้าให้เปิด
  if (item.link) router.push(item.link)
}

async function markAllRead() {
  if (!unreadCount.value) return
  notifications.value.forEach((item) => { item.read = true })
  unreadCount.value = 0

  try {
    const response = await fetch(`${API_BASE}/api/student/me/notifications/read-all`, { method: 'PATCH', headers: studentHeaders() })
    if (!response.ok) throw new Error()
  } catch {
    loadNotifications()
  }
}

function onDocumentClick(event) {
  if (open.value && wrapper.value && !wrapper.value.contains(event.target)) open.value = false
}

function onKeydown(event) {
  if (event.key === 'Escape' && open.value) open.value = false
}

function onVisibilityChange() {
  if (!document.hidden) loadNotifications()
}

onMounted(() => {
  loadNotifications()
  pollTimer = setInterval(() => {
    if (!document.hidden) loadNotifications()
  }, POLL_MS)
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onKeydown)
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onBeforeUnmount(() => {
  clearInterval(pollTimer)
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onKeydown)
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>

<template>
  <div ref="wrapper" class="notification-bell">
    <button
      type="button"
      class="bell-button"
      :class="{ active: open }"
      :aria-label="unreadCount ? `${t.studentNotifications.title} (${unreadCount})` : t.studentNotifications.title"
      :title="t.studentNotifications.title"
      :aria-expanded="open"
      aria-haspopup="true"
      data-testid="student-notification-bell"
      @click="toggle"
    >
      <Bell :size="19" />
      <span v-if="unreadCount" class="badge" data-testid="student-notification-badge">{{ badgeText }}</span>
    </button>

    <div v-if="open" class="dropdown" role="dialog" :aria-label="t.studentNotifications.title" data-testid="student-notification-dropdown">
      <div class="dropdown-header">
        <strong>{{ t.studentNotifications.title }}</strong>
        <div class="header-actions">
          <button
          type="button"
          class="mark-all"
          :disabled="!unreadCount"
          data-testid="student-notification-mark-all"
          @click="markAllRead"
        >
          <CheckCheck :size="15" />
          {{ t.studentNotifications.markAllRead }}
          </button>
          <button
            type="button"
            class="clear-all"
            :disabled="!notifications.length"
            :title="t.studentNotifications.clearAll"
            data-testid="student-notification-clear-all"
            @click="askClear"
          >
            <Trash2 :size="15" />
            {{ t.studentNotifications.clearAll }}
          </button>
        </div>
      </div>

      <div v-if="confirmingClear" class="clear-confirm" role="alert" data-testid="student-notification-clear-confirm">
        <p>{{ clearError ? t.studentNotifications.clearFailed : t.studentNotifications.clearConfirm }}</p>
        <div class="clear-confirm-actions">
          <button type="button" class="ghost" :disabled="clearing" @click="confirmingClear = false">{{ t.studentNotifications.cancel }}</button>
          <button type="button" class="danger" :disabled="clearing" data-testid="student-notification-clear-yes" @click="clearAll">
            {{ clearing ? t.studentNotifications.clearing : t.studentNotifications.confirmClear }}
          </button>
        </div>
      </div>

      <p v-if="loadError && !notifications.length" class="dropdown-state">{{ t.studentNotifications.loadError }}</p>

      <div v-else-if="!notifications.length" class="dropdown-state empty">
        <BellOff :size="22" />
        <span>{{ t.studentNotifications.empty }}</span>
      </div>

      <ul v-else class="notification-list">
        <li v-for="item in notifications" :key="item.id">
          <button
            type="button"
            class="notification-item"
            :class="[item.type, { unread: !item.read }]"
            :data-notification-id="item.id"
            @click="openNotification(item)"
          >
            <span class="item-icon" aria-hidden="true">
              <CircleCheck v-if="item.type === 'approved'" :size="17" />
              <CircleX v-else :size="17" />
            </span>

            <span class="item-body">
              <span class="item-message">
                <template v-for="(part, index) in messageParts(item)" :key="index">
                  <b v-if="part.strong">{{ part.text }}</b>
                  <template v-else>{{ part.text }}</template>
                </template>
              </span>
              <span class="item-time">{{ relativeTime(item.createdAt) }}</span>
            </span>

            <span v-if="!item.read" class="unread-dot" :aria-label="t.studentNotifications.unread"></span>
          </button>
        </li>
        <li v-if="hasMore" class="load-more-row">
          <button type="button" class="load-more" :disabled="loadingMore" data-testid="student-notification-load-more" @click="loadMore">
            {{ loadingMore ? t.studentNotifications.loadingMore : t.studentNotifications.loadMore }}
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.notification-bell {
  position: relative;
}

.bell-button {
  position: relative;
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: transparent;
  color: inherit;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.bell-button:hover,
.bell-button.active {
  background: #f1f4ff;
  color: #345eea;
}

.badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 19px;
  height: 19px;
  padding: 0 5px;
  border: 2px solid #fff;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: #e5484d;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}

.dropdown {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 1100;
  width: 380px;
  max-width: calc(100vw - 24px);
  border: 1px solid #e4e8ef;
  border-radius: 14px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 18px 48px rgba(28, 41, 61, 0.18);
}

.dropdown-header {
  padding: 14px 16px;
  border-bottom: 1px solid #eef1f6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  row-gap: 8px;
  gap: 10px;
}

.dropdown-header strong {
  white-space: nowrap;
  color: #1c293d;
  font-size: var(--fs-body);
}

.mark-all {
  white-space: nowrap;
  border: 0;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: none;
  color: #8d00c4;
  font: inherit;
  font-size: var(--fs-caption);
  font-weight: 600;
  cursor: pointer;
}

.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 14px;
}

.clear-all {
  white-space: nowrap;
  border: 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  color: #c2410c;
  font: inherit;
  font-size: var(--fs-caption);
  font-weight: 600;
  cursor: pointer;
}

.clear-all:disabled {
  color: #a3aebf;
  cursor: default;
}

.clear-confirm {
  padding: 12px 16px;
  border-bottom: 1px solid #fde2d6;
  background: #fff7f3;
}

.clear-confirm p {
  margin: 0 0 10px;
  color: #7c2d12;
  font-size: var(--fs-small);
  line-height: 1.5;
}

.clear-confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.clear-confirm-actions button {
  height: 32px;
  padding: 0 14px;
  border-radius: 8px;
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 600;
  cursor: pointer;
}

.clear-confirm-actions .ghost {
  border: 1px solid #e4e8ef;
  background: #fff;
  color: #42526b;
}

.clear-confirm-actions .danger {
  border: 0;
  background: #dc2626;
  color: #fff;
}

.clear-confirm-actions button:disabled {
  opacity: 0.6;
  cursor: wait;
}

.mark-all:disabled {
  color: #a3aebf;
  cursor: default;
}

.dropdown-state {
  margin: 0;
  padding: 28px 16px;
  color: #7b8ba3;
  font-size: var(--fs-small);
  text-align: center;
}

.dropdown-state.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.notification-list {
  max-height: 420px;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  list-style: none;
}

.notification-list li + li {
  border-top: 1px solid #fff;
}

/* พื้นหลังตามผล: เขียว = อนุมัติ, แดงอมส้ม = ไม่อนุมัติ (อ่านแล้วสีจางลง) */
.notification-item {
  width: 100%;
  padding: 13px 16px;
  border: 0;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: filter 0.15s ease;
}

.notification-item:hover {
  filter: brightness(0.97);
}

.notification-item.approved {
  background: #f3fbf5;
}

.notification-item.approved.unread {
  background: #e3f6e8;
}

.notification-item.rejected {
  background: #fff7f3;
}

.notification-item.rejected.unread {
  background: #ffebe3;
}

.item-icon {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
}

.approved .item-icon {
  background: #c9eed3;
  color: #157a37;
}

.rejected .item-icon {
  background: #ffd5c4;
  color: #c2410c;
}

.item-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.item-message {
  color: #34445a;
  font-size: var(--fs-small);
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.item-message b {
  color: #1c293d;
  font-weight: 600;
}

.item-time {
  color: #7a8699;
  font-size: var(--fs-caption);
}

.load-more-row {
  padding: 10px 16px;
  background: #fff;
}

.load-more {
  width: 100%;
  height: 36px;
  border: 1px solid #e4e8ef;
  border-radius: 9px;
  background: #fff;
  color: #8d00c4;
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 600;
  cursor: pointer;
}

.load-more:hover:not(:disabled) {
  background: #faf5ff;
}

.load-more:disabled {
  color: #a3aebf;
  cursor: wait;
}

.unread-dot {
  flex-shrink: 0;
  width: 9px;
  height: 9px;
  margin-top: 6px;
  border-radius: 50%;
  background: #2f6bff;
}

@media (max-width: 700px) {
  .dropdown {
    position: fixed;
    top: 62px;
    right: 12px;
    left: 12px;
    width: auto;
    max-width: none;
  }
}
</style>
