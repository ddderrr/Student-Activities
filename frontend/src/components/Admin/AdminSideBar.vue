<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  LayoutDashboard,
  CalendarDays,
  GraduationCap,
  CircleCheck,
  Settings,
  PanelLeftClose,
  PanelLeftOpen,
  LogOut,
  Languages
} from 'lucide-vue-next'

import { useLanguage } from '../../composables/useLanguage'
import {
  clearAdminSession,
  getAdminSession
} from '../../constants/currentAdmin'

// สถานะเปิด/ปิดอยู่ที่ App.vue (มือถือเป็น drawer ต้องคุมจาก layout)
const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggle'])

const sidebarOpen = computed(() => !props.collapsed)

const router = useRouter()
const route = useRoute()

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
    id: 'dashboard',
    name: t.value.adminSidebar.dashboard,
    icon: LayoutDashboard,
    path: '/admin/dashboard'
  },
  {
    id: 'activities',
    name: t.value.adminSidebar.activities,
    icon: CalendarDays,
    path: '/admin/activities'
  },
  {
    id: 'skills',
    name: t.value.adminSidebar.studentSkills,
    icon: GraduationCap,
    path: '/admin/student-skills'
  },
  {
    id: 'approvals',
    name: t.value.adminSidebar.approvals,
    icon: CircleCheck,
    path: '/admin/approvals'
  }
])


/* =========================
   Sidebar
========================= */

const toggleSidebar = () => {
  emit('toggle')
}


/* =========================
   Navigation
========================= */

const selectMenu = (item) => {
  router.push(item.path)
}

const goToSettings = () => {
  router.push('/admin/settings')
}


/* =========================
   Logout
========================= */

// แอดมินที่เลือกไว้ตอน login (โหมด bypass) router guard ตรวจกับ backend ก่อนเข้าทุกหน้าแล้ว
// อ่านใหม่ทุกครั้งที่เปลี่ยนหน้า เผื่อสลับแอดมินโดยที่ sidebar ยังไม่ถูก unmount
const currentAdmin = computed(() => {
  void route.fullPath
  return getAdminSession()
})

const adminEmail = computed(() => currentAdmin.value?.email || '')

const adminMajor = computed(() => {
  const admin = currentAdmin.value

  if (!admin) return ''

  return admin.is_central
    ? t.value.adminSidebar.centralAdmin
    : `${t.value.adminSidebar.majorPrefix} ${admin.major}`
})

const adminInitials = computed(() =>
  (adminEmail.value || 'AD').slice(0, 2).toUpperCase()
)

const logout = () => {
  clearAdminSession()
  router.push('/admin/login')
}
</script>


<template>

  <!-- SIDEBAR -->

  <aside
    class="sidebar"
    :class="{ collapsed: !sidebarOpen }"
  >

    <!-- HEADER -->

    <div class="sidebar-header">

      <div class="brand">

        <h2>
          {{ t.adminSidebar.faculty }}
        </h2>

        <p>
          {{ t.adminSidebar.subtitle }}
        </p>

      </div>


      <button
        class="close-sidebar-btn"
        @click="toggleSidebar"
        :title="sidebarOpen
          ? t.adminSidebar.closeSidebar
          : t.adminSidebar.openSidebar"
      >
        <PanelLeftClose v-if="sidebarOpen" :size="19" />
        <PanelLeftOpen v-else :size="19" />
      </button>

    </div>


    <!-- MENU -->

    <nav class="menu">

      <button
        v-for="item in menuItems"
        :key="item.id"
        class="menu-item"
        :class="{
          active: route.path === item.path
        }"
        @click="selectMenu(item)"
        :title="!sidebarOpen ? item.name : ''"
      >

        <component
          :is="item.icon"
          class="menu-icon"
          :size="19"
        />

        <span>
          {{ item.name }}
        </span>

      </button>

    </nav>


    <!-- FOOTER -->

    <div class="sidebar-footer">

      <!-- LANGUAGE -->

      <div class="language-box">

        <div class="language-title">

          <Languages :size="17" />

          <span>
            {{ t.common.language }}
          </span>

        </div>


        <div class="language-switch">

          <button
            :class="{
              active: currentLanguage === 'TH'
            }"
            @click="setLanguage('TH')"
          >
            ไทย
          </button>

          <button
            :class="{
              active: currentLanguage === 'EN'
            }"
            @click="setLanguage('EN')"
          >
            EN
          </button>

        </div>

        <button
          class="collapsed-language-button"
          type="button"
          :title="t.common.language"
          @click="setLanguage(currentLanguage === 'TH' ? 'EN' : 'TH')"
        >
          {{ currentLanguage }}
        </button>

      </div>


      <!-- SETTINGS -->

      <button
        class="menu-item"
        :class="{
          active: route.path === '/admin/settings'
        }"
        @click="goToSettings"
        :title="!sidebarOpen ? t.common.settings : ''"
      >

        <Settings
          class="menu-icon"
          :size="19"
        />

        <span>
          {{ t.common.settings }}
        </span>

      </button>


      <!-- ADMIN PROFILE -->

      <div class="profile-card">

        <span class="profile-avatar">
          {{ adminInitials }}
        </span>


        <div class="profile-info">

          <strong :title="adminEmail" data-testid="admin-email">
            {{ adminEmail }}
          </strong>

          <small :title="adminMajor" data-testid="admin-major">
            {{ adminMajor }}
          </small>

        </div>


        <button
          class="logout-btn"
          @click="logout"
          :title="t.common.logout"
        >
          <LogOut :size="17" />
        </button>

      </div>

    </div>

  </aside>

</template>


<style scoped>

.sidebar {
  width: 230px;
  height: 100vh;

  position: sticky;
  top: 0;

  align-self: flex-start;

  background: #ffffff;

  border-right: 1px solid #e5eaf2;

  display: flex;
  flex-direction: column;

  box-sizing: border-box;

  padding: 18px 12px;

  flex-shrink: 0;

  overflow-x: hidden;
  overflow-y: auto;

  z-index: 100;

  transition:
    width 0.25s ease,
    padding 0.25s ease;
}

.sidebar.collapsed {
  width: 72px;
  padding: 18px 10px;
}


/* =========================
   HEADER
========================= */

.sidebar-header {
  min-height: 60px;

  display: flex;

  align-items: flex-start;
  justify-content: space-between;

  gap: 8px;

  margin-bottom: 20px;
}


/* =========================
   BRAND
========================= */

.brand {
  padding-left: 8px;

  min-width: 0;
}


.brand h2 {
  margin: 0;

  font-size: var(--fs-lead);
  font-weight: 700;

  color: #173f95;

  white-space: nowrap;
}


.brand p {
  margin: 3px 0 0;

  font-size: var(--fs-badge);
  letter-spacing: 0.7px;

  color: #94a3b8;

  white-space: nowrap;
}


/* =========================
   CLOSE BUTTON
========================= */

.close-sidebar-btn {
  width: 32px;
  height: 32px;

  flex-shrink: 0;

  border: none;
  border-radius: 8px;

  background: transparent;

  color: #64748b;

  cursor: pointer;

  display: flex;

  align-items: center;
  justify-content: center;

  transition: 0.2s;
}


.close-sidebar-btn:hover {
  background: #f3e8ff;
  color: #7c3aed;
}


/* =========================
   MENU
========================= */

.menu {
  display: flex;
  flex-direction: column;

  gap: 6px;
}


.menu-item {
  width: 100%;
  height: 42px;

  border: none;
  border-radius: 8px;

  background: transparent;

  padding: 0 13px;

  box-sizing: border-box;

  display: flex;

  align-items: center;

  gap: 12px;

  font-size: var(--fs-small);

  color: #52617a;

  cursor: pointer;

  position: relative;

  transition: 0.2s;

  white-space: nowrap;

  text-align: left;
}


.menu-item:hover {
  background: #f4f7fc;
}


.menu-icon {
  min-width: 19px;

  color: #8799b3;
}


/* =========================
   ACTIVE
========================= */

.menu-item.active {
  background: #edf4ff;

  color: #1e4d8f;
}


.menu-item.active .menu-icon {
  color: #2563eb;
}


.menu-item.active::after {
  content: '';

  position: absolute;

  right: 0;
  top: 7px;
  bottom: 7px;

  width: 3px;

  background: #2563eb;

  border-radius: 3px;
}


/* =========================
   FOOTER
========================= */

.sidebar-footer {
  margin-top: auto;

  border-top: 1px solid #edf0f4;

  padding-top: 12px;
}


/* =========================
   LANGUAGE
========================= */

.language-box {
  margin-bottom: 12px;

  padding: 10px;

  border-radius: 9px;

  background: #f8f5ff;
}


.language-title {
  display: flex;

  align-items: center;

  gap: 8px;

  margin-bottom: 8px;

  font-size: var(--fs-small);
  font-weight: 600;

  color: #6d28d9;
}


.language-switch {
  display: flex;

  padding: 3px;

  border-radius: 7px;

  background: #ede9fe;
}


.language-switch button {
  flex: 1;

  border: none;
  border-radius: 5px;

  padding: 6px 8px;

  background: transparent;

  color: #7c3aed;

  font-size: var(--fs-small);
  font-weight: 700;

  cursor: pointer;

  transition: 0.2s;
}


.language-switch button.active {
  background: #7c3aed;

  color: white;
}


/* =========================
   PROFILE
========================= */

.profile-card {
  display: flex;

  align-items: center;

  gap: 10px;

  margin-top: 12px;

  padding: 10px;

  border-radius: 10px;

  background: #f4f7fc;

  box-sizing: border-box;
}


.profile-avatar {
  width: 32px;
  height: 32px;

  border-radius: 50%;

  flex-shrink: 0;

  display: flex;

  align-items: center;
  justify-content: center;

  font-size: var(--fs-small);
  font-weight: 700;

  color: #ffffff;

  background:
    linear-gradient(
      135deg,
      #a855f7,
      #6366f1
    );
}


/* =========================
   PROFILE INFO
========================= */

.profile-info {
  min-width: 0;

  flex: 1;

  display: flex;

  flex-direction: column;

  overflow: hidden;
}


.profile-info strong {
  font-size: var(--fs-small);

  color: #1c293d;

  white-space: nowrap;

  overflow: hidden;

  text-overflow: ellipsis;
}


/* อีเมลและสาขาของแอดมินต้องอ่านได้ครบ จึงให้ขึ้นบรรทัดใหม่แทนการตัดด้วย ... */
.profile-info [data-testid="admin-email"],
.profile-info [data-testid="admin-major"] {
  white-space: normal;

  overflow-wrap: anywhere;
}

.profile-info [data-testid="admin-email"] {
  font-size: var(--fs-small);
}


.profile-info small {
  margin-top: 2px;

  font-size: var(--fs-caption);

  color: #8ea0ba;

  white-space: nowrap;

  overflow: hidden;

  text-overflow: ellipsis;
}


/* =========================
   LOGOUT
========================= */

.logout-btn {
  width: 30px;
  height: 30px;

  flex-shrink: 0;

  border: none;
  border-radius: 7px;

  background: transparent;

  color: #7c3aed;

  cursor: pointer;

  display: flex;

  align-items: center;
  justify-content: center;

  transition: 0.2s;
}


.logout-btn:hover {
  background: #ede9fe;

  color: #6d28d9;

  transform: translateX(2px);
}



/* =========================
   COLLAPSED
========================= */

.collapsed .sidebar-header {
  justify-content: center;
}

.collapsed .brand {
  display: none;
}

.collapsed .close-sidebar-btn {
  width: 38px;
  height: 38px;
  background: #f8f5ff;
  color: #7c3aed;
}

.collapsed .menu {
  align-items: center;
}

.collapsed .menu-item {
  width: 46px;
  height: 46px;
  padding: 0;
  justify-content: center;
  border-radius: 8px;
}

.collapsed .menu-item span {
  display: none;
}

.collapsed .menu-item.active::after {
  right: 0;
  top: 7px;
  bottom: 7px;
}

.collapsed .sidebar-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 12px;
}

.collapsed .language-box {
  width: 46px;
  margin-bottom: 12px;
  padding: 6px 4px;
  box-sizing: border-box;
  display: flex;
  justify-content: center;
}

.collapsed .language-title,
.collapsed .language-switch {
  display: none;
}

.collapsed-language-button {
  display: none;
}

.collapsed .collapsed-language-button {
  width: 36px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: #7c3aed;
  color: #ffffff;
  font-size: var(--fs-caption);
  font-weight: 800;
  cursor: pointer;
}

.collapsed .profile-card {
  width: 46px;
  margin-top: 12px;
  padding: 7px;
  justify-content: center;
}

.collapsed .profile-avatar,
.collapsed .profile-info {
  display: none;
}

.collapsed .logout-btn {
  width: 32px;
  height: 32px;
}

/* =========================
   SCROLLBAR
========================= */

.sidebar::-webkit-scrollbar {
  width: 5px;
}


.sidebar::-webkit-scrollbar-track {
  background: transparent;
}


.sidebar::-webkit-scrollbar-thumb {
  background: #dbe3ef;

  border-radius: 10px;
}


.sidebar::-webkit-scrollbar-thumb:hover {
  background: #c4cfdd;
}

</style>