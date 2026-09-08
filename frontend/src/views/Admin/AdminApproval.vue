<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  SlidersHorizontal,
  ArrowUpDown,
  X
} from 'lucide-vue-next'

const API_BASE = 'http://127.0.0.1:8000'
const PAGE_SIZE = 10

const AVATAR_COLORS = ['#2f5fdb', '#1c2b4a', '#8ea0ba', '#7c5cd6']

const REQUEST_TYPE_OPTIONS = [
  { value: '', label: 'All Types' },
  { value: 'skill_validation', label: 'Skill Validation' },
  { value: 'special_request', label: 'Special Request' }
]

const REQUEST_TYPE_ICONS = {
  skill_validation: ShieldCheck,
  special_request: AlertTriangle
}

const stats = ref({ total_pending: 0, approved_today: 0, rejected_today: 0 })
const requests = ref([])
const total = ref(0)
const page = ref(1)

const pageLoading = ref(true)
const loadError = ref('')
const actionLoadingId = ref(null)
const actionError = ref('')

const filterType = ref('')
const sortOrder = ref('date_desc')
const showFilterMenu = ref(false)

const detailRequest = ref(null)

const totalPages = computed(() =>
  Math.max(1, Math.ceil(total.value / PAGE_SIZE))
)

const rangeStart = computed(() =>
  total.value === 0 ? 0 : (page.value - 1) * PAGE_SIZE + 1
)

const rangeEnd = computed(() =>
  Math.min(page.value * PAGE_SIZE, total.value)
)

function initials(name) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()
}

function avatarColor(id) {
  return AVATAR_COLORS[id % AVATAR_COLORS.length]
}

function formatDate(value) {
  if (!value) return '-'

  const date = new Date(value)

  const datePart = date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })

  const timePart = date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })

  return `${datePart} | ${timePart}`
}

async function fetchStats() {
  try {
    const response = await fetch(`${API_BASE}/api/requests/stats`)
    if (!response.ok) return
    stats.value = await response.json()
  } catch {
    // stat cards are non-critical, silently ignore
  }
}

async function fetchRequests() {
  pageLoading.value = true
  loadError.value = ''

  try {
    const params = new URLSearchParams({
      status: 'pending',
      sort: sortOrder.value,
      page: String(page.value),
      page_size: String(PAGE_SIZE)
    })

    if (filterType.value) params.set('request_type', filterType.value)

    const response = await fetch(`${API_BASE}/api/requests?${params}`)

    if (!response.ok) throw new Error('โหลดข้อมูลไม่สำเร็จ')

    const data = await response.json()
    requests.value = data.requests
    total.value = data.total
  } catch (error) {
    loadError.value = error.message || 'โหลดข้อมูลไม่สำเร็จ'
  } finally {
    pageLoading.value = false
  }
}

function refreshAll() {
  fetchStats()
  fetchRequests()
}

onMounted(refreshAll)

watch([filterType, sortOrder], () => {
  page.value = 1
  fetchRequests()
})

function goToPage(next) {
  if (next < 1 || next > totalPages.value) return
  page.value = next
  fetchRequests()
}

function toggleSort() {
  sortOrder.value = sortOrder.value === 'date_desc' ? 'date_asc' : 'date_desc'
}

async function decideRequest(request, status) {
  actionLoadingId.value = request.id
  actionError.value = ''

  try {
    const response = await fetch(`${API_BASE}/api/requests/${request.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    })

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null)
      throw new Error(errorBody?.detail || 'บันทึกไม่สำเร็จ')
    }

    refreshAll()
  } catch (error) {
    actionError.value = error.message || 'บันทึกไม่สำเร็จ'
  } finally {
    actionLoadingId.value = null
  }
}
</script>

<template>
  <section class="approval-page">
    <header class="page-header">
      <div>
        <h1>การอนุมัติ (Approvals)</h1>
        <p class="subtitle">จัดการคำขอที่รอการตรวจสอบและอนุมัติจากระบบ</p>
      </div>
    </header>

    <div class="stat-grid">
      <div class="stat-card">
        <span class="stat-label">Total Pending</span>
        <strong class="stat-value">{{ stats.total_pending }}</strong>
      </div>

      <div class="stat-card">
        <span class="stat-label">Approved Today</span>
        <strong class="stat-value stat-approved">{{ stats.approved_today }}</strong>
      </div>

      <div class="stat-card">
        <span class="stat-label">Rejected Today</span>
        <strong class="stat-value stat-rejected">{{ stats.rejected_today }}</strong>
      </div>
    </div>

    <section class="table-card">
      <div class="table-heading">
        <h2>รายการที่รอดำเนินการ (Pending Requests)</h2>

        <div class="heading-actions">
          <div class="filter-wrapper">
            <button class="tool-button" @click="showFilterMenu = !showFilterMenu">
              <SlidersHorizontal :size="14" />
              Filter
            </button>

            <div v-if="showFilterMenu" class="filter-menu">
              <button
                v-for="option in REQUEST_TYPE_OPTIONS"
                :key="option.value"
                class="filter-option"
                :class="{ active: filterType === option.value }"
                @click="filterType = option.value; showFilterMenu = false"
              >
                {{ option.label }}
              </button>
            </div>
          </div>

          <button class="tool-button" @click="toggleSort">
            <ArrowUpDown :size="14" />
            Sort
          </button>
        </div>
      </div>

      <p v-if="pageLoading" class="load-status">กำลังโหลดข้อมูล...</p>
      <p v-else-if="loadError" class="load-status load-status-error">{{ loadError }}</p>
      <p v-else-if="requests.length === 0" class="load-status">ไม่มีคำขอที่รอดำเนินการ</p>

      <div v-else class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>REQUESTER NAME</th>
              <th>REQUEST TYPE</th>
              <th>DATE SUBMITTED</th>
              <th>DETAILS</th>
              <th>ACTIONS</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="request in requests" :key="request.id">
              <td>
                <div class="requester-cell">
                  <span
                    class="avatar"
                    :style="{ background: avatarColor(request.id) }"
                  >
                    {{ initials(request.requester_name) }}
                  </span>

                  <div>
                    <div class="requester-name">{{ request.requester_name }}</div>
                    <small>ID: {{ request.requester_student_id }}</small>
                  </div>
                </div>
              </td>

              <td>
                <div class="request-type-cell">
                  <component
                    :is="REQUEST_TYPE_ICONS[request.request_type]"
                    :size="14"
                    class="type-icon"
                  />

                  <div>
                    <div class="request-type-name">{{ request.request_type_label }}</div>
                    <small>{{ request.detail }}</small>
                  </div>
                </div>
              </td>

              <td class="date-cell">{{ formatDate(request.submitted_at) }}</td>

              <td>
                <button class="detail-button" @click="detailRequest = request">
                  View Detail
                </button>
              </td>

              <td>
                <div class="row-actions">
                  <button
                    class="approve-button"
                    :disabled="actionLoadingId === request.id"
                    @click="decideRequest(request, 'approved')"
                  >
                    อนุมัติ
                  </button>

                  <button
                    class="reject-button"
                    :disabled="actionLoadingId === request.id"
                    @click="decideRequest(request, 'rejected')"
                  >
                    ยกเลิก
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="!pageLoading && total > 0" class="pagination">
        <span>Showing {{ rangeStart }}-{{ rangeEnd }} of {{ total }} pending requests</span>

        <div class="pagination-controls">
          <button
            class="page-nav"
            :disabled="page === 1"
            @click="goToPage(page - 1)"
          >
            <ChevronLeft :size="15" />
          </button>

          <button
            v-for="p in totalPages"
            :key="p"
            class="page-number"
            :class="{ active: p === page }"
            @click="goToPage(p)"
          >
            {{ p }}
          </button>

          <button
            class="page-nav"
            :disabled="page === totalPages"
            @click="goToPage(page + 1)"
          >
            <ChevronRight :size="15" />
          </button>
        </div>
      </div>

      <div v-if="actionError" class="action-error">{{ actionError }}</div>
    </section>

    <div v-if="detailRequest" class="modal-backdrop" @click.self="detailRequest = null">
      <div class="modal">
        <div class="modal-header">
          <h3>รายละเอียดคำขอ</h3>
          <button class="modal-close" @click="detailRequest = null">
            <X :size="16" />
          </button>
        </div>

        <dl>
          <dt>Requester</dt>
          <dd>{{ detailRequest.requester_name }} (ID: {{ detailRequest.requester_student_id }})</dd>

          <dt>Request Type</dt>
          <dd>{{ detailRequest.request_type_label }}</dd>

          <dt>Detail</dt>
          <dd>{{ detailRequest.detail || '-' }}</dd>

          <dt>Submitted</dt>
          <dd>{{ formatDate(detailRequest.submitted_at) }}</dd>
        </dl>
      </div>
    </div>
  </section>
</template>

<style scoped>
.approval-page {
  min-height: 100vh;
  padding: 32px 34px 48px;
  background: #f7f8fc;
  color: #1c293d;
}

.page-header {
  margin-bottom: 22px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #173f95;
}

.subtitle {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 13px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border: 1px solid #e5eaf2;
  border-radius: 12px;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat-label {
  color: #8ea0ba;
  font-size: 12px;
}

.stat-value {
  font-size: 26px;
  color: #1c293d;
}

.stat-approved { color: #16a34a; }
.stat-rejected { color: #dc2626; }

.table-card {
  background: #fff;
  border: 1px solid #e5eaf2;
  border-radius: 14px;
  padding: 20px 22px;
}

.table-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.table-heading h2 {
  margin: 0;
  font-size: 15px;
}

.heading-actions {
  display: flex;
  gap: 8px;
}

.filter-wrapper {
  position: relative;
}

.tool-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border: 1px solid #e5eaf2;
  border-radius: 8px;
  background: #fff;
  color: #52617a;
  font-size: 12.5px;
  cursor: pointer;
}

.tool-button:hover { background: #f4f7fc; }

.filter-menu {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  background: #fff;
  border: 1px solid #e5eaf2;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(28, 41, 61, 0.12);
  z-index: 10;
  min-width: 160px;
  overflow: hidden;
}

.filter-option {
  display: block;
  width: 100%;
  text-align: left;
  padding: 9px 14px;
  border: none;
  background: #fff;
  font-size: 12.5px;
  color: #52617a;
  cursor: pointer;
}

.filter-option:hover { background: #f4f7fc; }
.filter-option.active { color: #2563eb; font-weight: 600; background: #edf4ff; }

.load-status {
  padding: 40px 16px;
  text-align: center;
  color: #8ea0ba;
  font-size: 13px;
}

.load-status-error { color: #bd3c3c; }

.table-scroll { overflow-x: auto; }

table { width: 100%; border-collapse: collapse; min-width: 780px; }

thead th {
  text-align: left;
  font-size: 10.5px;
  letter-spacing: 0.04em;
  color: #8ea0ba;
  padding: 10px 12px;
  border-bottom: 1px solid #edf0f4;
  white-space: nowrap;
}

tbody td {
  padding: 14px 12px;
  border-bottom: 1px solid #f2f4f8;
  vertical-align: middle;
}

.requester-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.requester-name { font-size: 13px; font-weight: 600; }
.requester-cell small,
.request-type-cell small,
.date-cell { color: #8ea0ba; font-size: 11.5px; }

.request-type-cell {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.type-icon { color: #2563eb; margin-top: 2px; flex-shrink: 0; }
.request-type-name { font-size: 13px; font-weight: 600; }

.date-cell { font-size: 12.5px; color: #52617a; }

.detail-button {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid #e5eaf2;
  background: #f7f8fc;
  color: #52617a;
  font-size: 11.5px;
  cursor: pointer;
  white-space: nowrap;
}

.detail-button:hover { background: #edf0f4; }

.row-actions { display: flex; gap: 8px; }

.approve-button,
.reject-button {
  padding: 7px 14px;
  border-radius: 8px;
  border: 1px solid transparent;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.approve-button { background: #2f5fdb; color: #fff; }
.approve-button:hover:not(:disabled) { background: #2549ad; }

.reject-button { background: #fff; border-color: #e5eaf2; color: #52617a; }
.reject-button:hover:not(:disabled) { background: #f4f7fc; }

.approve-button:disabled,
.reject-button:disabled { opacity: 0.6; cursor: not-allowed; }

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid #f2f4f8;
  font-size: 12px;
  color: #8ea0ba;
}

.pagination-controls { display: flex; align-items: center; gap: 6px; }

.page-nav,
.page-number {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid #e5eaf2;
  background: #fff;
  color: #52617a;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.page-nav:disabled { opacity: 0.4; cursor: not-allowed; }
.page-number.active { background: #2563eb; border-color: #2563eb; color: #fff; }

.action-error {
  margin-top: 14px;
  padding: 10px 16px;
  border-radius: 8px;
  background: #fff2f2;
  color: #bd3c3c;
  font-size: 12px;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(28, 41, 61, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: #fff;
  border-radius: 14px;
  padding: 22px 24px;
  width: 360px;
  max-width: calc(100vw - 32px);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.modal-header h3 { margin: 0; font-size: 15px; }

.modal-close {
  border: none;
  background: #f4f7fc;
  border-radius: 8px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #52617a;
}

.modal dl { margin: 0; }
.modal dt { font-size: 11px; color: #8ea0ba; margin-top: 12px; }
.modal dt:first-child { margin-top: 0; }
.modal dd { margin: 3px 0 0; font-size: 13px; color: #1c293d; }
</style>
