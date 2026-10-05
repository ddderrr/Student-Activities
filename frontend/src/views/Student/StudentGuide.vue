<script setup>
import { computed } from 'vue'
import { CalendarDays, CirclePlus, FileText, Mail, Zap } from 'lucide-vue-next'

import UserGuide from '../../components/common/UserGuide.vue'
import { useLanguage } from '../../composables/useLanguage'
import { HELP_CENTER_EMAIL } from '../../constants/currentStudent'

const { t } = useLanguage()

// ลำดับและไอคอนตรงกับเมนูใน StudentSideBar เนื้อหาอยู่ใน locales (studentGuide.sections)
const SECTIONS = [
  { key: 'activities', icon: CalendarDays, path: '/student/activities', tone: 'purple' },
  { key: 'external', icon: CirclePlus, path: '/student/external-activity', tone: 'green' },
  { key: 'skills', icon: Zap, path: '/student/skills', tone: 'amber' },
  { key: 'transcript', icon: FileText, path: '/student/transcript', tone: 'blue' }
]

const sections = computed(() =>
  SECTIONS.map((section) => ({ ...section, ...t.value.studentGuide.sections[section.key] }))
)
</script>

<template>
  <UserGuide :sections="sections" :labels="t.studentGuide" accent="purple">
    <template #footer>
      <p class="help-note">
        <Mail :size="16" aria-hidden="true" />
        {{ t.studentGuide.stillNeedHelp }}
        <a :href="`mailto:${HELP_CENTER_EMAIL}`">{{ HELP_CENTER_EMAIL }}</a>
      </p>
    </template>
  </UserGuide>
</template>

<style scoped>
.help-note {
  margin: 24px 0 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #6b7891;
  font-size: var(--fs-small);
}

.help-note a {
  color: #8d00c4;
  font-weight: 600;
}
</style>
