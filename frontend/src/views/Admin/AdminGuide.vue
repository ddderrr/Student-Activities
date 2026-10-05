<script setup>
import { computed } from 'vue'
import {
  Bell,
  CalendarDays,
  CircleCheck,
  GraduationCap,
  LayoutDashboard,
  Settings,
  ShieldCheck,
  UserCog
} from 'lucide-vue-next'

import UserGuide from '../../components/common/UserGuide.vue'
import { useLanguage } from '../../composables/useLanguage'
import { getAdminSession } from '../../constants/currentAdmin'

const { t } = useLanguage()

// router guard ตรวจ session กับ backend ก่อนเข้าหน้านี้แล้ว (is_central / major เป็นค่าล่าสุด)
const admin = getAdminSession()
const isCentral = Boolean(admin?.is_central)

// ลำดับและไอคอนตรงกับเมนูใน AdminSideBar เนื้อหาอยู่ใน locales (adminGuide.sections)
// centralOnly = ซ่อนทั้งหัวข้อสำหรับแอดมินสาขา
const SECTIONS = [
  { key: 'dashboard', icon: LayoutDashboard, path: '/admin/dashboard', tone: 'blue' },
  { key: 'activities', icon: CalendarDays, path: '/admin/activities', tone: 'purple' },
  { key: 'skills', icon: GraduationCap, path: '/admin/student-skills', tone: 'green' },
  { key: 'approvals', icon: CircleCheck, path: '/admin/approvals', tone: 'amber' },
  { key: 'settings', icon: Settings, path: '/admin/settings', tone: 'slate' },
  { key: 'notifications', icon: Bell, path: null, tone: 'rose' }
]

// หัวข้อย่อยระบุ audience: 'central' (เฉพาะแอดมินกลาง) / 'branch' (เฉพาะแอดมินสาขา) / ไม่ระบุ = ทุกคน
const sections = computed(() => {
  const text = t.value.adminGuide
  const viewer = isCentral ? 'central' : 'branch'

  return SECTIONS
    .filter((section) => isCentral || !section.centralOnly)
    .map((section) => ({
      ...section,
      ...text.sections[section.key],
      topics: text.sections[section.key].topics
        .filter((topic) => !topic.audience || topic.audience === viewer)
        .map((topic) => ({
          ...topic,
          badge: topic.audience === 'central' ? text.centralOnlyBadge : ''
        }))
    }))
})

const roleLabel = computed(() =>
  isCentral
    ? t.value.adminGuide.roleCentral
    : t.value.adminGuide.roleBranch.replace('{major}', admin?.major || '')
)
</script>

<template>
  <UserGuide :sections="sections" :labels="t.adminGuide" accent="blue">
    <template #badge>
      <p class="role-badge" :class="{ central: isCentral }" data-testid="guide-role-badge">
        <component :is="isCentral ? ShieldCheck : UserCog" :size="16" aria-hidden="true" />
        <span>{{ t.adminGuide.guideFor }}</span>
        <strong>{{ roleLabel }}</strong>
      </p>
    </template>
  </UserGuide>
</template>

<style scoped>
.role-badge {
  margin: 10px 0 0;
  padding: 5px 12px;
  border: 1px solid #c3d4f5;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #f3f7ff;
  color: #2550c0;
  font-size: var(--fs-small);
}

.role-badge.central {
  border-color: #d6c3ec;
  background: #faf5ff;
  color: #7a00aa;
}

.role-badge strong {
  font-weight: 700;
}
</style>
