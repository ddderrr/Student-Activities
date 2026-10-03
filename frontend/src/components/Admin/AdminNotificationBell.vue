<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, BellOff, CheckCheck, FilePlus2, RefreshCw } from 'lucide-vue-next'

import { useLanguage } from '../../composables/useLanguage'
import { adminFetch } from '../../constants/currentAdmin'
import { API_BASE } from '../../constants/currentStudent'

// กระดิ่งแจ้งเตือนของแอดมิน: backend กรองตามสาขาให้แล้ว (แอดมินกลางเห็นทุกสาขา)
// ดึงใหม่ทุก 30 วินาทีตอนแท็บเปิดอยู่ + ตอนกลับมาที่แท็บ + ตอนเปิด dropdown
const POLL_MS = 30_000

const { t, currentLanguage } = useLanguage()
const router = useRouter()

const notifications = ref([])
const unreadCount = ref(0)
const open = ref(false)
const loading = ref(false)
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
    const response = await adminFetch(`${API_BASE}/api/admin/notifications`)
    if (!response.ok) throw new Error()
    const data = await response.json()
    notifications.value = data.notifications
    unreadCount.value = data.unread_count
    loadError.value = false
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
    now.value = Date.now()
  }
}

function messageParts(item) {
  const text = t.value.adminNotifications
  const template = item.type === 'external_resubmitted' ? text.externalResubmitted : text.externalSubmitted
  // แยกข้อความตาม {name} / {title} เพื่อทำตัวหนาเฉพาะชื่อ
  return template.split(/(\{name\}|\{title\})/).filter(Boolean).map((part) => {
    if (part === '{name}') return { text: item.student_name, strong: true }
    if (part === '{title}') return { text: item.activity_title, strong: true }
    return { text: part, strong: false }
  })
}

function relativeTime(iso) {
  const seconds = Math.round((new Date(iso).getTime() - now.value) / 1000)
  if (Math.abs(seconds) < 60) return t.value.adminNotifications.justNow

  const formatter = new Intl.RelativeTimeFormat(currentLanguage.value === 'TH' ? 'th' : 'en', { numeric: 'auto' })
  const units = [['day', 86400], ['hour', 3600], ['minute', 60]]
  const [unit, size] = units.find(([, unitSeconds]) => Math.abs(seconds) >= unitSeconds)
  return formatter.format(Math.round(seconds / size), unit)
}

function toggle() {
  open.value = !open.value
  if (open.value) loadNotifications()
}

async function markRead(item) {
  if (item.is_read) return
  item.is_read = true
  unreadCount.value = Math.max(0, unreadCount.value - 1)

  try {
    const response = await adminFetch(`${API_BASE}/api/admin/notifications/${item.id}/read`, { method: 'PATCH' })
    if (!response.ok) throw new Error()
  } catch {
    // บันทึกไม่สำเร็จ: ดึงสถานะจริงกลับมา
    loadNotifications()
  }
}

async function openNotification(item) {
  open.value = false
  markRead(item)
  router.push(item.link)
}

async function markAllRead() {
  if (!unreadCount.value) return
  notifications.value.forEach((item) => { item.is_read = true })
  unreadCount.value = 0

  try {
    const response = await adminFetch(`${API_BASE}/api/admin/notifications/read-all`, { method: 'PATCH' })
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
      :aria-label="unreadCount ? `${t.adminNotifications.title} (${unreadCount})` : t.adminNotifications.title"
      :title="t.adminNotifications.title"
      :aria-expanded="open"
      aria-haspopup="true"
      data-testid="admin-notification-bell"
      @click="toggle"
    >
      <Bell :size="20" />
      <span v-if="unreadCount" class="badge" data-testid="admin-notification-badge">{{ badgeText }}</span>
    </button>

    <div v-if="open" class="dropdown" role="dialog" :aria-label="t.adminNotifications.title" data-testid="admin-notification-dropdown">
      <div class="dropdown-header">
        <strong>{{ t.adminNotifications.title }}</strong>
        <button
          type="button"
          class="mark-all"
          :disabled="!unreadCount"
          data-testid="admin-notification-mark-all"
          @click="markAllRead"
        >
          <CheckCheck :size="15" />
          {{ t.adminNotifications.markAllRead }}
        </button>
      </div>

      <p v-if="loadError && !notifications.length" class="dropdown-state">{{ t.adminNotifications.loadError }}</p>

      <div v-else-if="!notifications.length" class="dropdown-state empty">
        <BellOff :size="22" />
        <span>{{ t.adminNotifications.empty }}</span>
      </div>

      <ul v-else class="notification-list">
        <li v-for="item in notifications" :key="item.id">
          <button
            type="button"
            class="notification-item"
            :class="{ unread: !item.is_read }"
            :data-notification-id="item.id"
            @click="openNotification(item)"
          >
            <span class="item-icon" :class="item.type" aria-hidden="true">
              <RefreshCw v-if="item.type === 'external_resubmitted'" :size="16" />
              <FilePlus2 v-else :size="16" />
            </span>

            <span class="item-body">
              <span class="item-message">
                <template v-for="(part, index) in messageParts(item)" :key="index">
                  <b v-if="part.strong">{{ part.text }}</b>
                  <template v-else>{{ part.text }}</template>
                </template>
              </span>
              <span class="item-time">{{ relativeTime(item.created_at) }}</span>
            </span>

            <span v-if="!item.is_read" class="unread-dot" :aria-label="t.adminNotifications.unread"></span>
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
  width: 40px;
  height: 40px;
  border: 1px solid #e3e8f0;
  border-radius: 11px;
  display: grid;
  place-items: center;
  background: #fff;
  color: #42526b;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.bell-button:hover,
.bell-button.active {
  border-color: #c9d6ee;
  background: #f3f7ff;
  color: #2f5fdb;
}

.badge {
  position: absolute;
  top: -6px;
  right: -6px;
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
  border: 1px solid #e3e8f0;
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
  gap: 10px;
}

.dropdown-header strong {
  color: #1c293d;
  font-size: var(--fs-body);
}

.mark-all {
  border: 0;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: none;
  color: #2f5fdb;
  font: inherit;
  font-size: var(--fs-caption);
  font-weight: 600;
  cursor: pointer;
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
  border-top: 1px solid #f1f4f8;
}

.notification-item {
  width: 100%;
  padding: 13px 16px;
  border: 0;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: #fff;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.notification-item:hover {
  background: #f7f9fc;
}

.notification-item.unread {
  background: #f5f8ff;
}

.notification-item.unread:hover {
  background: #edf2ff;
}

.item-icon {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: #eaf0ff;
  color: #2f5fdb;
}

.item-icon.external_resubmitted {
  background: #fff4e5;
  color: #b25e09;
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
  color: #8a97ab;
  font-size: var(--fs-caption);
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
