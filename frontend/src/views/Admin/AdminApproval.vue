<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  FileText,
  Globe2,
  LoaderCircle,
  ShieldCheck,
  SlidersHorizontal,
  ArrowUpDown,
  TriangleAlert,
  X
} from 'lucide-vue-next'
import {
  PARTICIPANT_SKILLS,
  STAFF_SKILLS
} from '../../constants/activitySkills'
import { useLanguage } from '../../composables/useLanguage'

const { t } = useLanguage()

const API_BASE = 'http://127.0.0.1:8000'
const PAGE_SIZE = 10

const AVATAR_COLORS = ['#2f5fdb', '#1c2b4a', '#8ea0ba', '#7c5cd6']

const REQUEST_TYPE_OPTIONS = computed(() => [
  { value: '', label: t.value.adminApproval.filterAllTypes },
  { value: 'skill_validation', label: t.value.adminApproval.filterSkillValidation },
  { value: 'special_request', label: t.value.adminApproval.filterSpecialRequest },
  { value: 'external_activity', label: t.value.adminApproval.filterExternalActivity }
])

const REQUEST_TYPE_ICONS = {
  skill_validation: ShieldCheck,
  special_request: AlertTriangle,
  external_activity: Globe2
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

const STATUS_TABS = computed(() => [
  { value: 'pending', label: t.value.adminApproval.pendingTab },
  { value: 'rejected', label: t.value.adminApproval.rejectedTab }
])
const statusFilter = ref('pending')

const detailRequest = ref(null)
const successMessage = ref('')

// /api/requests รวม 2 แหล่ง id ซ้ำกันได้ ต้องใช้ source ประกอบ key
function rowKey(request) {
  return `${request.source}-${request.id}`
}

function isExternal(request) {
  return request.source === 'external_activity'
}

/* =========================
   External activity review
========================= */
const reviewItem = ref(null)
const reviewOpen = ref(false)
const reviewLoading = ref(false)
const reviewError = ref('')

// Skill Mapping ที่นักศึกษาตั้งมา (แสดงอย่างเดียว admin ไม่ต้องแก้)
const reviewSkillRows = computed(() => {
  if (!reviewItem.value) return []

  const definitions =
    reviewItem.value.skill_target_role === 'staff'
      ? STAFF_SKILLS
      : PARTICIPANT_SKILLS

  return definitions
    .map((skill) => ({
      ...skill,
      level: reviewItem.value.skills?.[skill.key] ?? null
    }))
    .sort((a, b) => (b.level ?? 0) - (a.level ?? 0))
})

const relatedSkillCount = computed(() =>
  reviewSkillRows.value.filter((skill) => skill.level !== null).length
)

async function openReview(request) {
  reviewOpen.value = true
  reviewLoading.value = true
  reviewError.value = ''
  reviewItem.value = null
  successMessage.value = ''

  try {
    const response = await fetch(`${API_BASE}/api/external-activities/${request.id}`)
    const data = await response.json().catch(() => null)

    if (!response.ok) throw new Error(data?.detail || t.value.adminApproval.loadDetailError)

    reviewItem.value = data
  } catch (error) {
    reviewError.value = error.message || t.value.adminApproval.loadDetailError
  } finally {
    reviewLoading.value = false
  }
}

function closeReview() {
  reviewOpen.value = false
  reviewItem.value = null
}

/* =========================
   Approve / reject from the table
   (View Detail ใช้ดูอย่างเดียว)
========================= */
const decisionTarget = ref(null)
const decisionComment = ref('')
const decisionError = ref('')
const deciding = ref(false)

// Skill Mapping ที่นักศึกษาตั้งไว้ โชว์ให้ admin ยืนยันก่อนอนุมัติกิจกรรมภายนอก
const decisionSkillItem = ref(null)
const decisionSkillLoading = ref(false)

const decisionSkillRows = computed(() => {
  if (!decisionSkillItem.value) return []

  const definitions =
    decisionSkillItem.value.skill_target_role === 'staff'
      ? STAFF_SKILLS
      : PARTICIPANT_SKILLS

  return definitions
    .map((skill) => ({
      ...skill,
      level: decisionSkillItem.value.skills?.[skill.key] ?? null
    }))
    .sort((a, b) => (b.level ?? 0) - (a.level ?? 0))
})

async function openDecision(request, status) {
  decisionTarget.value = { request, status }
  decisionComment.value = ''
  decisionError.value = ''
  successMessage.value = ''
  decisionSkillItem.value = null

  if (status !== 'approved' || !isExternal(request)) return

  decisionSkillLoading.value = true

  try {
    const response = await fetch(`${API_BASE}/api/external-activities/${request.id}`)
    const data = await response.json().catch(() => null)

    if (response.ok) decisionSkillItem.value = data
  } finally {
    decisionSkillLoading.value = false
  }
}

function closeDecision() {
  if (deciding.value) return
  decisionTarget.value = null
  decisionSkillItem.value = null
}

async function confirmDecision() {
  if (!decisionTarget.value || deciding.value) return

  const { request, status } = decisionTarget.value
  const comment = decisionComment.value.trim()

  decisionError.value = ''

  if (status === 'rejected' && !comment) {
    decisionError.value = t.value.adminApproval.rejectReasonRequired
    return
  }

  deciding.value = true

  // external activity ใช้ /decision ส่วนคำขอทั่วไปใช้ /api/requests/{id} ตรง ๆ
  const endpoint = isExternal(request)
    ? `${API_BASE}/api/external-activities/${request.id}/decision`
    : `${API_BASE}/api/requests/${request.id}`

  try {
    const response = await fetch(endpoint, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(
        status === 'approved'
          ? { status }
          // คอมเมนต์นี้แสดงให้นักศึกษาเห็นใน My Submissions และส่งเป็น Notification
          : { status, reject_reason: comment }
      )
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) throw new Error(data?.detail || t.value.adminApproval.saveFailed)

    const label = request.detail || request.requester_name

    successMessage.value =
      status === 'approved'
        ? `${t.value.adminApproval.approvedMessagePrefix}"${label}"${t.value.adminApproval.approvedMessageSuffix}`
        : `${t.value.adminApproval.rejectedMessagePrefix}"${label}"${t.value.adminApproval.rejectedMessageSuffix}`

    deciding.value = false
    closeDecision()
    refreshAll()
  } catch (error) {
    decisionError.value = error.message || t.value.adminApproval.saveFailed
  } finally {
    deciding.value = false
  }
}

function formatDay(value) {
  if (!value) return t.value.adminApproval.emptyPlaceholder

  const [year, month, day] = value.split('-').map(Number)

  return new Date(year, month - 1, day).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

function reviewDateRange(item) {
  return item.start_date === item.end_date
    ? formatDay(item.start_date)
    : `${formatDay(item.start_date)} – ${formatDay(item.end_date)}`
}

function formatBytes(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

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
  if (!value) return t.value.adminApproval.emptyPlaceholder

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

// External activity ไม่เก็บเวลาจากฟอร์ม (มีแค่วันที่) จึงโชว์วันที่สั้น ๆ พอ ไม่โชว์เวลา
function formatDateOnly(value) {
  if (!value) return t.value.adminApproval.emptyPlaceholder

  return new Date(value).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
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
      status: statusFilter.value,
      sort: sortOrder.value,
      page: String(page.value),
      page_size: String(PAGE_SIZE)
    })

    if (filterType.value) params.set('request_type', filterType.value)

    const response = await fetch(`${API_BASE}/api/requests?${params}`)

    if (!response.ok) throw new Error(t.value.adminApproval.loadRequestsError)

    const data = await response.json()
    requests.value = data.requests
    total.value = data.total
  } catch (error) {
    loadError.value = error.message || t.value.adminApproval.loadRequestsError
  } finally {
    pageLoading.value = false
  }
}

function refreshAll() {
  fetchStats()
  fetchRequests()
}

onMounted(refreshAll)

watch([filterType, sortOrder, statusFilter], () => {
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
  actionLoadingId.value = rowKey(request)
  actionError.value = ''

  try {
    const response = await fetch(`${API_BASE}/api/requests/${request.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    })

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null)
      throw new Error(errorBody?.detail || t.value.adminApproval.saveFailed)
    }

    refreshAll()
  } catch (error) {
    actionError.value = error.message || t.value.adminApproval.saveFailed
  } finally {
    actionLoadingId.value = null
  }
}
</script>

<template>
  <section class="approval-page">
    <header class="page-header">
      <div>
        <h1>{{ t.adminApproval.pageTitle }}</h1>
        <p class="subtitle">{{ t.adminApproval.pageSubtitle }}</p>
      </div>
    </header>

    <div class="stat-grid">
      <div class="stat-card">
        <span class="stat-label">{{ t.adminApproval.statTotalPending }}</span>
        <strong class="stat-value">{{ stats.total_pending }}</strong>
      </div>

      <div class="stat-card">
        <span class="stat-label">{{ t.adminApproval.statApprovedToday }}</span>
        <strong class="stat-value stat-approved">{{ stats.approved_today }}</strong>
      </div>

      <div class="stat-card">
        <span class="stat-label">{{ t.adminApproval.statRejectedToday }}</span>
        <strong class="stat-value stat-rejected">{{ stats.rejected_today }}</strong>
      </div>
    </div>

    <div class="status-tabs" role="tablist" :aria-label="t.adminApproval.statusTabsAriaLabel">
      <button
        v-for="tab in STATUS_TABS"
        :key="tab.value"
        type="button"
        role="tab"
        :aria-selected="statusFilter === tab.value"
        :class="{ active: statusFilter === tab.value }"
        @click="statusFilter = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <section class="table-card">
      <div class="table-heading">
        <h2>
          {{
            statusFilter === 'rejected'
              ? t.adminApproval.rejectedRequestsHeading
              : t.adminApproval.pendingRequestsHeading
          }}
        </h2>

        <div class="heading-actions">
          <div class="filter-wrapper">
            <button class="tool-button" @click="showFilterMenu = !showFilterMenu">
              <SlidersHorizontal :size="14" />
              {{ t.adminApproval.filterButton }}
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
            {{ t.adminApproval.sortButton }}
          </button>
        </div>
      </div>

      <p v-if="pageLoading" class="load-status">{{ t.adminApproval.loadingRequests }}</p>
      <p v-else-if="loadError" class="load-status load-status-error">{{ loadError }}</p>
      <p v-else-if="requests.length === 0" class="load-status">
        {{ statusFilter === 'rejected' ? t.adminApproval.noRejectedRequests : t.adminApproval.noPendingRequests }}
      </p>

      <div v-else class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>{{ t.adminApproval.tableHeaderRequesterName }}</th>
              <th>{{ t.adminApproval.tableHeaderRequestType }}</th>
              <th>{{ t.adminApproval.tableHeaderDateSubmitted }}</th>
              <th>{{ t.adminApproval.tableHeaderDetails }}</th>
              <th>{{ t.adminApproval.tableHeaderActions }}</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="request in requests"
              :key="rowKey(request)"
              :data-source="request.source"
              :data-id="request.id"
            >
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
                    <small>{{ t.adminApproval.idLabel }} {{ request.requester_student_id }}</small>
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

              <td class="date-cell">
                {{ isExternal(request) ? formatDateOnly(request.submitted_at) : formatDate(request.submitted_at) }}
              </td>

              <td>
                <button
                  class="detail-button"
                  @click="isExternal(request) ? openReview(request) : (detailRequest = request)"
                >
                  {{ t.adminApproval.viewDetailButton }}
                </button>
              </td>

              <td>
                <template v-if="statusFilter !== 'pending'">
                  <span class="no-actions">{{ t.adminApproval.emptyPlaceholder }}</span>
                </template>

                <div v-else-if="isExternal(request)" class="row-actions">
                  <button
                    class="approve-button"
                    :disabled="deciding"
                    @click="openDecision(request, 'approved')"
                  >
                    {{ t.adminApproval.approveButton }}
                  </button>

                  <button
                    class="reject-button"
                    :disabled="deciding"
                    @click="openDecision(request, 'rejected')"
                  >
                    {{ t.adminApproval.rejectButton }}
                  </button>
                </div>

                <div v-else class="row-actions">
                  <button
                    class="approve-button"
                    :disabled="actionLoadingId === rowKey(request)"
                    @click="decideRequest(request, 'approved')"
                  >
                    {{ t.adminApproval.approveButton }}
                  </button>

                  <button
                    class="reject-button"
                    :disabled="actionLoadingId === rowKey(request)"
                    @click="openDecision(request, 'rejected')"
                  >
                    {{ t.adminApproval.cancelButton }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="!pageLoading && total > 0" class="pagination">
        <span>{{ t.adminApproval.paginationShowing }} {{ rangeStart }}-{{ rangeEnd }} {{ t.adminApproval.paginationOf }} {{ total }} {{ t.adminApproval.paginationPendingRequests }}</span>

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
      <div v-if="successMessage" class="action-success" role="status">
        <CheckCircle2 :size="15" />
        {{ successMessage }}
      </div>
    </section>

    <div v-if="detailRequest" class="modal-backdrop" @click.self="detailRequest = null">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ t.adminApproval.detailModalTitle }}</h3>
          <button class="modal-close" @click="detailRequest = null">
            <X :size="16" />
          </button>
        </div>

        <dl>
          <dt>{{ t.adminApproval.detailRequesterLabel }}</dt>
          <dd>{{ detailRequest.requester_name }} ({{ t.adminApproval.idLabel }} {{ detailRequest.requester_student_id }})</dd>

          <dt>{{ t.adminApproval.detailRequestTypeLabel }}</dt>
          <dd>{{ detailRequest.request_type_label }}</dd>

          <dt>{{ t.adminApproval.detailFieldLabel }}</dt>
          <dd>{{ detailRequest.detail || t.adminApproval.emptyPlaceholder }}</dd>

          <dt>{{ t.adminApproval.submittedLabel }}</dt>
          <dd>{{ formatDate(detailRequest.submitted_at) }}</dd>
        </dl>
      </div>
    </div>

    <div v-if="reviewOpen" class="modal-backdrop" @click.self="closeReview">
      <div class="modal review-modal" role="dialog" :aria-label="t.adminApproval.reviewModalAriaLabel">
        <div class="modal-header">
          <div>
            <p class="review-eyebrow">{{ t.adminApproval.reviewEyebrow }}</p>
            <h3>{{ reviewItem ? reviewItem.title : t.adminApproval.loadingShort }}</h3>
          </div>
          <button class="modal-close" @click="closeReview">
            <X :size="16" />
          </button>
        </div>

        <p v-if="reviewLoading" class="load-status">{{ t.adminApproval.loadingReviewDetail }}</p>

        <div v-else-if="reviewItem" class="review-grid">
          <div class="review-left">
            <section class="review-section">
              <h4>{{ t.adminApproval.studentLabel }}</h4>
              <p class="review-student">
                {{ reviewItem.student.first_name }} {{ reviewItem.student.last_name }}
                <small>{{ t.adminApproval.idLabel }} {{ reviewItem.student_id }} · {{ reviewItem.student.major }}</small>
              </p>
            </section>

            <section class="review-section">
              <h4>{{ t.adminApproval.activityDetailsLabel }}</h4>
              <dl class="review-details">
                <dt>{{ t.adminApproval.externalOrganizerLabel }}</dt>
                <dd data-field="organization">{{ reviewItem.organization }}</dd>
                <dt>{{ t.adminApproval.categoryLabel }}</dt>
                <dd data-field="activity_type">{{ reviewItem.activity_type }}</dd>
                <dt>{{ t.adminApproval.roleLabel }}</dt>
                <dd data-field="role">{{ reviewItem.role === 'organizer' ? t.adminApproval.roleOrganizer : t.adminApproval.roleParticipant }}</dd>
                <dt>{{ t.adminApproval.dateLabel }}</dt>
                <dd data-field="date">{{ reviewDateRange(reviewItem) }}</dd>
                <dt>{{ t.adminApproval.locationLabel }}</dt>
                <dd data-field="location">{{ reviewItem.location }}</dd>
                <dt>{{ t.adminApproval.submittedLabel }}</dt>
                <dd>{{ formatDateOnly(reviewItem.submitted_at) }}</dd>
              </dl>
              <div class="review-description" data-field="description">
                {{ reviewItem.description || t.adminApproval.noDescriptionText }}
              </div>

              <div v-if="reviewItem.status === 'rejected' && reviewItem.reject_reason" class="review-reject-reason">
                <strong>{{ t.adminApproval.rejectReasonLabel }}</strong>
                <p>{{ reviewItem.reject_reason }}</p>
              </div>
            </section>

            <section class="review-section">
              <h4>{{ t.adminApproval.evidenceLabel }}</h4>
              <img
                v-if="reviewItem.evidence.content_type.startsWith('image/')"
                class="evidence-preview"
                :src="`${API_BASE}${reviewItem.evidence.url}`"
                :alt="reviewItem.evidence.original_name"
              />
              <a
                class="evidence-file"
                :href="`${API_BASE}${reviewItem.evidence.url}`"
                target="_blank"
                rel="noopener"
              >
                <FileText :size="15" />
                <span>{{ reviewItem.evidence.original_name }}</span>
                <small>{{ formatBytes(reviewItem.evidence.size) }}</small>
                <ExternalLink :size="13" />
              </a>
            </section>
          </div>

          <div class="review-right">
            <section class="review-section">
              <div class="skills-heading">
                <h4>{{ t.adminApproval.skillMappingLabel }}</h4>
                <span class="skill-count">
                  {{ relatedSkillCount }} {{ t.adminApproval.relatedLabel }} ·
                  {{ reviewItem.skill_target_role === 'staff' ? t.adminApproval.staffSkillsLabel : t.adminApproval.participantSkillsLabel }}
                </span>
              </div>

              <ul class="skill-readonly">
                <li
                  v-for="skill in reviewSkillRows"
                  :key="skill.key"
                  :data-skill="skill.key"
                  :class="{ 'not-related': skill.level === null }"
                >
                  <div class="skill-readonly-name">
                    <strong>{{ skill.label }}</strong>
                    <small>{{ skill.description }}</small>
                  </div>

                  <div class="skill-readonly-level">
                    <span v-if="skill.level !== null" class="level-bar" aria-hidden="true">
                      <i
                        v-for="level in 5"
                        :key="level"
                        :class="{ filled: level <= skill.level }"
                      ></i>
                    </span>
                    <span class="level-text">
                      {{ skill.level === null ? t.adminApproval.notRelatedLabel : `${t.adminApproval.levelPrefix} ${skill.level}` }}
                    </span>
                  </div>
                </li>
              </ul>
            </section>
          </div>
        </div>

        <div v-if="reviewError" class="review-error" role="alert">
          <TriangleAlert :size="15" />
          {{ reviewError }}
        </div>
      </div>
    </div>

    <!-- ยืนยันอนุมัติ / ไม่อนุมัติ (เปิดจากปุ่มในตาราง) -->
    <div v-if="decisionTarget" class="modal-backdrop" @click.self="closeDecision">
      <div
        class="modal decision-modal"
        role="dialog"
        :aria-label="decisionTarget.status === 'approved' ? t.adminApproval.confirmApprovalAriaLabel : t.adminApproval.rejectWithCommentAriaLabel"
        :data-status="decisionTarget.status"
      >
        <div class="modal-header">
          <h3>
            {{ decisionTarget.status === 'approved' ? t.adminApproval.confirmApprovalTitle : t.adminApproval.rejectActivityTitle }}
          </h3>
          <button class="modal-close" :disabled="deciding" @click="closeDecision">
            <X :size="16" />
          </button>
        </div>

        <div class="decision-summary">
          <strong>{{ decisionTarget.request.detail }}</strong>
          <span>
            {{ decisionTarget.request.requester_name }}
            ({{ t.adminApproval.idLabel }} {{ decisionTarget.request.requester_student_id }})
            · {{ decisionTarget.request.request_type_label }}
          </span>
        </div>

        <template v-if="decisionTarget.status === 'approved'">
          <p v-if="isExternal(decisionTarget.request)" class="decision-text">
            {{ t.adminApproval.confirmApprovalExternalText }}
          </p>
          <p v-else class="decision-text">
            {{ t.adminApproval.confirmApprovalGenericText }}
          </p>

          <div v-if="isExternal(decisionTarget.request)" class="decision-skill-summary">
            <h4>{{ t.adminApproval.skillMappingLabel }}</h4>

            <p v-if="decisionSkillLoading" class="load-status">{{ t.adminApproval.loadingSkillMapping }}</p>

            <ul v-else class="skill-readonly compact">
              <li
                v-for="skill in decisionSkillRows"
                :key="skill.key"
                :data-skill="skill.key"
                :class="{ 'not-related': skill.level === null }"
              >
                <div class="skill-readonly-name">
                  <strong>{{ skill.label }}</strong>
                </div>

                <div class="skill-readonly-level">
                  <span v-if="skill.level !== null" class="level-bar" aria-hidden="true">
                    <i
                      v-for="level in 5"
                      :key="level"
                      :class="{ filled: level <= skill.level }"
                    ></i>
                  </span>
                  <span class="level-text">
                    {{ skill.level === null ? t.adminApproval.notRelatedLabel : `${t.adminApproval.levelPrefix} ${skill.level}` }}
                  </span>
                </div>
              </li>
            </ul>
          </div>
        </template>

        <label v-else class="reject-field">
          <span>{{ t.adminApproval.rejectCommentLabel }}</span>
          <textarea
            v-model="decisionComment"
            rows="4"
            :placeholder="t.adminApproval.rejectCommentPlaceholder"
            @input="decisionError = ''"
          ></textarea>
          <small class="decision-hint">{{ t.adminApproval.rejectCommentHint }}</small>
        </label>

        <div v-if="decisionError" class="review-error" role="alert">
          <TriangleAlert :size="15" />
          {{ decisionError }}
        </div>

        <div class="decision-actions">
          <button class="reject-button" :disabled="deciding" @click="closeDecision">
            {{ t.adminApproval.cancelButton }}
          </button>

          <button
            v-if="decisionTarget.status === 'approved'"
            class="approve-button"
            :disabled="deciding"
            @click="confirmDecision"
          >
            <LoaderCircle v-if="deciding" class="spin" :size="14" />
            {{ t.adminApproval.confirmApproveButton }}
          </button>

          <button
            v-else
            class="confirm-reject-button"
            :disabled="deciding"
            @click="confirmDecision"
          >
            <LoaderCircle v-if="deciding" class="spin" :size="14" />
            {{ t.adminApproval.confirmRejectButton }}
          </button>
        </div>
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

.status-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 14px;
}

.status-tabs button {
  padding: 8px 16px;
  border: 1px solid #e5eaf2;
  border-radius: 8px;
  background: #fff;
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.15s;
}

.status-tabs button:hover {
  border-color: #c7d2e0;
}

.status-tabs button.active {
  background: #173f95;
  border-color: #173f95;
  color: #fff;
}

.no-actions {
  color: #9aa5b5;
  font-size: 12px;
}

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

.action-success {
  margin: 12px 0 0;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #15803d;
  font-size: 12.5px;
}

.review-modal {
  width: min(960px, calc(100vw - 32px));
  max-height: 90vh;
  overflow-y: auto;
  padding: 22px 24px;
}

.review-eyebrow {
  margin: 0 0 3px;
  color: #8ea0ba;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.review-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 18px;
}

.review-left,
.review-right {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}

.review-section {
  padding: 14px 16px;
  border: 1px solid #e5eaf2;
  border-radius: 12px;
}

.review-section h4 {
  margin: 0 0 10px;
  color: #52617a;
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.review-student {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-size: 14px;
  font-weight: 600;
}

.review-student small {
  color: #8ea0ba;
  font-size: 12px;
  font-weight: 400;
}

.modal .review-details {
  display: grid;
  grid-template-columns: 130px minmax(0, 1fr);
  gap: 6px 10px;
}

.modal .review-details dt,
.modal .review-details dt:first-child {
  margin: 0;
}

.modal .review-details dd {
  margin: 0;
  overflow-wrap: anywhere;
}

.review-description {
  margin-top: 12px;
  padding: 10px 12px;
  border-left: 3px solid #7c5cd6;
  border-radius: 6px;
  background: #f7f5ff;
  color: #3b4a61;
  font-size: 12.5px;
  white-space: pre-wrap;
}

.review-reject-reason {
  margin-top: 12px;
  padding: 10px 12px;
  border-left: 3px solid #dc2626;
  border-radius: 6px;
  background: #fef2f2;
  color: #7f1d1d;
  font-size: 12.5px;
}

.review-reject-reason strong {
  display: block;
  margin-bottom: 4px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.review-reject-reason p {
  margin: 0;
  white-space: pre-wrap;
}

.evidence-preview {
  width: 100%;
  max-height: 260px;
  margin-bottom: 10px;
  border-radius: 8px;
  object-fit: contain;
  background: #f4f7fc;
}

.evidence-file {
  padding: 9px 11px;
  border: 1px solid #e5eaf2;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #2f5fdb;
  font-size: 12.5px;
  text-decoration: none;
}

.evidence-file span {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.evidence-file small {
  color: #8ea0ba;
}

.skills-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.skill-count {
  color: #52617a;
  font-size: 11px;
}

.review-hint {
  margin: 0 0 10px;
  color: #8ea0ba;
  font-size: 11.5px;
}

.skill-readonly {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.skill-readonly li {
  padding: 9px 11px;
  border: 1px solid #edf0f5;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.skill-readonly li.not-related {
  background: #f8f9fb;
  color: #9aa6b8;
}

.skill-readonly-name {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.skill-readonly-name strong {
  font-size: 12.5px;
}

.skill-readonly-name small {
  color: #8ea0ba;
  font-size: 10.5px;
}

.skill-readonly-level {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.level-bar {
  display: inline-flex;
  gap: 3px;
}

.level-bar i {
  width: 14px;
  height: 6px;
  border-radius: 3px;
  background: #e5eaf2;
}

.level-bar i.filled {
  background: #2f5fdb;
}

.level-text {
  min-width: 52px;
  font-size: 11.5px;
  font-weight: 700;
  text-align: right;
}

.not-related .level-text {
  font-weight: 500;
}

.reject-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #b42318;
  font-size: 12px;
  font-weight: 600;
}

.reject-field textarea {
  padding: 9px 11px;
  border: 1px solid #f1c3c0;
  border-radius: 8px;
  background: #fff;
  color: #1c293d;
  font: inherit;
  font-size: 13px;
  resize: vertical;
}

.review-error {
  margin-top: 14px;
  padding: 9px 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 7px;
  background: #fdeaea;
  color: #b42318;
  font-size: 12.5px;
}

.decision-modal {
  width: min(480px, calc(100vw - 32px));
}

.decision-summary {
  padding: 11px 13px;
  border: 1px solid #e5eaf2;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: #f8fafd;
}

.decision-summary strong {
  font-size: 13.5px;
}

.decision-summary span {
  color: #64748b;
  font-size: 12px;
}

.decision-text {
  margin: 14px 0 0;
  color: #3b4a61;
  font-size: 13px;
  line-height: 1.55;
}

.decision-modal .reject-field {
  margin-top: 14px;
}

.decision-skill-summary {
  margin-top: 14px;
  padding: 12px 13px;
  border: 1px solid #e5eaf2;
  border-radius: 10px;
  background: #f8fafd;
  max-height: 260px;
  overflow-y: auto;
}

.decision-skill-summary h4 {
  margin: 0 0 8px;
  font-size: 12px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.skill-readonly.compact li {
  padding: 8px 0;
}

.skill-readonly.compact .skill-readonly-name small {
  display: none;
}

.decision-hint {
  color: #8ea0ba;
  font-size: 11px;
  font-weight: 400;
}

.decision-actions {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.decision-actions button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.confirm-reject-button {
  padding: 7px 14px;
  border: none;
  border-radius: 8px;
  background: #dc2626;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.decision-actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spin {
  animation: spin 0.75s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 760px) {
  .review-grid {
    grid-template-columns: 1fr;
  }
}
</style>
