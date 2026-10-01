<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  CalendarDays,
  Zap,
  CirclePlus,
  FileText,
  CircleHelp,
  LogOut,
  Languages,
  PanelLeftClose,
  PanelLeftOpen
} from 'lucide-vue-next'

import { useLanguage } from '../../composables/useLanguage'
import { logout as logoutAll } from '../../constants/auth'
import { HELP_CENTER_EMAIL } from '../../constants/currentStudent'

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggle'])

const route = useRoute()
const router = useRouter()

/* =========================
   Language
========================= */

const {
  currentLanguage,
  setLanguage,
  t
} = useLanguage()

/* =========================
   Menu Items
========================= */

const menuItems = computed(() => [
  {
    name: t.value.studentSidebar.myActivities,
    path: '/student/activities',
    icon: CalendarDays
  },
  {
    name: t.value.studentSidebar.mySkills,
    path: '/student/skills',
    icon: Zap
  },
  {
    name: t.value.studentSidebar.addExternalActivity,
    path: '/student/external-activity',
    icon: CirclePlus
  },
  {
    name: t.value.studentSidebar.transcript,
    path: '/student/transcript',
    icon: FileText
  }
])

/* =========================
   Navigation
========================= */

const goTo = (path) => {
  router.push(path)
}

const isActive = (path) => {
  return route.path === path
}

/* =========================
   Logout
========================= */

const logout = () => {
  logoutAll()
  router.push('/login')
}
</script>

<template>
  <aside
    class="student-sidebar"
    :class="{ collapsed: props.collapsed }"
  >
    <!-- Brand -->
    <div class="brand">
      <div class="brand-text">
        <h2>
          {{ t.studentSidebar.faculty }}
        </h2>

        <p>
          {{ t.studentSidebar.subtitle }}
        </p>
      </div>

      <button
        class="collapse-button"
        :title="props.collapsed ? t.studentSidebar.openSidebar : t.studentSidebar.closeSidebar"
        @click="emit('toggle')"
      >
        <PanelLeftOpen
          v-if="props.collapsed"
          :size="20"
        />

        <PanelLeftClose
          v-else
          :size="20"
        />
      </button>
    </div>

    <!-- Menu -->
    <nav class="menu">
      <button
        v-for="item in menuItems"
        :key="item.path"
        class="menu-item"
        :class="{ active: isActive(item.path) }"
        :title="props.collapsed ? item.name : ''"
        @click="goTo(item.path)"
      >
        <component
          :is="item.icon"
          :size="18"
          class="menu-icon"
        />

        <span class="menu-text">
          {{ item.name }}
        </span>
      </button>
    </nav>

    <!-- Bottom -->
    <div class="bottom-menu">
      <!-- Language -->
      <div
        class="language-box"
        :title="props.collapsed ? t.common.language : ''"
      >
        <div class="language-title">
          <Languages :size="17" />

          <span>
            {{ t.common.language }}
          </span>
        </div>

        <div class="language-switch">
          <button
            :class="{ active: currentLanguage === 'TH' }"
            @click="setLanguage('TH')"
          >
            ไทย
          </button>

          <button
            :class="{ active: currentLanguage === 'EN' }"
            @click="setLanguage('EN')"
          >
            EN
          </button>
        </div>

        <!-- ตอนพับ แสดงปุ่มภาษาแบบสั้น -->
        <button
          class="collapsed-language-button"
          @click="setLanguage(currentLanguage === 'TH' ? 'EN' : 'TH')"
        >
          {{ currentLanguage }}
        </button>
      </div>

      <!-- Help: ติดต่อทางอีเมล -->
      <a
        class="menu-item"
        :href="`mailto:${HELP_CENTER_EMAIL}`"
        :title="`${t.common.helpCenterContact} ${HELP_CENTER_EMAIL}`"
        :aria-label="`${t.common.helpCenter}: ${t.common.helpCenterContact} ${HELP_CENTER_EMAIL}`"
      >
        <CircleHelp
          :size="18"
          class="menu-icon"
        />

        <span class="menu-text">
          {{ t.common.helpCenter }}
        </span>
      </a>

      <!-- Logout -->
      <button
        class="menu-item logout-item"
        :title="props.collapsed ? t.common.logout : ''"
        @click="logout"
      >
        <LogOut
          :size="18"
          class="menu-icon"
        />

        <span class="menu-text">
          {{ t.common.logout }}
        </span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.student-sidebar {
  width: 240px;
  min-width: 240px;
  height: 100vh;

  position: sticky;
  top: 0;

  display: flex;
  flex-direction: column;

  box-sizing: border-box;

  background: #8d00c4;
  color: white;

  padding: 26px 18px;

  overflow: hidden;

  transition:
    width 0.25s ease,
    min-width 0.25s ease,
    padding 0.25s ease;
}

/* =========================
   Collapsed Sidebar
========================= */

.student-sidebar.collapsed {
  width: 72px;
  min-width: 72px;

  padding: 22px 10px;
}

/* =========================
   Brand
========================= */

.brand {
  min-height: 52px;
  margin-bottom: 36px;

  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.brand-text {
  min-width: 0;
  overflow: hidden;

  transition:
    opacity 0.18s ease,
    width 0.25s ease;
}

.brand h2 {
  margin: 0;

  font-size: var(--fs-lead);
  font-weight: 700;

  color: white;

  white-space: nowrap;
}

.brand p {
  margin: 3px 0 0;

  font-size: var(--fs-badge);
  letter-spacing: 0.7px;

  opacity: 0.7;

  min-width: 150px;
  white-space: normal;
}

.collapse-button {
  width: 34px;
  height: 34px;
  min-width: 34px;

  display: flex;
  align-items: center;
  justify-content: center;

  border: none;
  border-radius: 7px;

  background: rgba(255, 255, 255, 0.1);
  color: white;

  cursor: pointer;

  transition:
    background 0.15s ease,
    transform 0.15s ease;
}

.collapse-button:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.student-sidebar.collapsed .brand {
  justify-content: center;
}

.student-sidebar.collapsed .brand-text {
  width: 0;
  opacity: 0;
  pointer-events: none;
}

/* =========================
   Menu
========================= */

.menu {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.menu-item {
  width: 100%;
  min-height: 46px;

  display: flex;
  align-items: center;
  gap: 10px;

  padding: 13px 12px;

  border: none;
  border-radius: 6px;

  background: transparent;
  color: rgba(255, 255, 255, 0.82);

  text-align: left;
  text-decoration: none;

  cursor: pointer;

  overflow: hidden;

  transition:
    background 0.15s ease,
    color 0.15s ease,
    padding 0.25s ease;
}

.menu-icon {
  flex: 0 0 auto;
}

.menu-text {
  min-width: 0;
  white-space: normal;

  font-size: var(--fs-small);
  font-weight: 500;

  transition:
    opacity 0.15s ease,
    width 0.25s ease;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: white;
}

.menu-item.active {
  background: rgba(255, 255, 255, 0.12);

  border-left: 3px solid #4cff89;

  color: white;
}

.student-sidebar.collapsed .menu-item {
  justify-content: center;

  padding: 13px 0;
}

.student-sidebar.collapsed .menu-item.active {
  border-left: none;
  box-shadow: inset 3px 0 0 #4cff89;
}

.student-sidebar.collapsed .menu-text {
  display: none;
}

/* =========================
   Bottom Menu
========================= */

.bottom-menu {
  margin-top: auto;
}

/* =========================
   Language
========================= */

.language-box {
  margin-bottom: 12px;
  padding: 12px;

  border-radius: 8px;

  background: rgba(255, 255, 255, 0.08);
}

.language-title {
  display: flex;
  align-items: center;
  gap: 8px;

  margin-bottom: 10px;

  font-size: var(--fs-small);
  font-weight: 600;

  color: rgba(255, 255, 255, 0.85);
}

.language-switch {
  display: flex;

  padding: 3px;

  border-radius: 6px;

  background: rgba(255, 255, 255, 0.12);
}

.language-switch button {
  flex: 1;

  padding: 7px 8px;

  border: none;
  border-radius: 5px;

  background: transparent;
  color: rgba(255, 255, 255, 0.7);

  font-size: var(--fs-small);
  font-weight: 700;

  cursor: pointer;
}

.language-switch button.active {
  background: white;
  color: #8d00c4;
}

.collapsed-language-button {
  display: none;
}

.student-sidebar.collapsed .language-box {
  padding: 7px 5px;

  display: flex;
  justify-content: center;

  background: rgba(255, 255, 255, 0.08);
}

.student-sidebar.collapsed .language-title,
.student-sidebar.collapsed .language-switch {
  display: none;
}

.student-sidebar.collapsed .collapsed-language-button {
  width: 38px;
  height: 32px;

  display: flex;
  align-items: center;
  justify-content: center;

  border: none;
  border-radius: 6px;

  background: white;
  color: #8d00c4;

  font-size: var(--fs-caption);
  font-weight: 800;

  cursor: pointer;
}

/* =========================
   Logout
========================= */

.logout-item {
  color: rgba(255, 255, 255, 0.82);
}

/* =========================
   Responsive
========================= */

@media (max-width: 800px) {
  .student-sidebar:not(.collapsed) {
    width: 200px;
    min-width: 200px;
  }

  .brand h2 {
    font-size: var(--fs-lead);
  }

  .menu-text {
    font-size: var(--fs-small);
  }
}

@media (max-width: 700px) {
  .student-sidebar,
  .student-sidebar.collapsed {
    width: 240px;
    min-width: 240px;
    padding: 26px 18px;
  }

  .student-sidebar.collapsed .brand {
    justify-content: space-between;
  }

  .student-sidebar.collapsed .brand-text {
    width: auto;
    opacity: 1;
    pointer-events: auto;
  }

  .student-sidebar.collapsed .menu-item {
    justify-content: flex-start;
    padding: 13px 14px;
  }

  .student-sidebar.collapsed .menu-item.active {
    border-left: 3px solid #4cff89;
    box-shadow: none;
  }

  .student-sidebar.collapsed .menu-text {
    display: inline;
  }

  .student-sidebar.collapsed .language-box {
    display: block;
    padding: 12px;
  }

  .student-sidebar.collapsed .language-title,
  .student-sidebar.collapsed .language-switch {
    display: flex;
  }

  .student-sidebar.collapsed .collapsed-language-button {
    display: none;
  }
}

</style>
