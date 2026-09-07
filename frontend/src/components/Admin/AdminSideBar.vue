<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  LayoutDashboard,
  CalendarDays,
  GraduationCap,
  CircleCheck,
  Settings,
  PanelLeftClose,
  PanelLeftOpen
} from 'lucide-vue-next'

const collapsed = ref(false)
const router = useRouter()
const route = useRoute()

const menuItems = [
  { id: 'dashboard', name: 'Dashboard', icon: LayoutDashboard, path: '/admin/dashboard' },
  { id: 'activities', name: 'Activities', icon: CalendarDays, path: '/admin/activities' },
  { id: 'skills', name: 'Student Skills', icon: GraduationCap, path: '/admin/student-skills' },
  { id: 'approvals', name: 'Approvals', icon: CircleCheck, path: '/admin/approvals' }
]

const toggleSidebar = () => {
  collapsed.value = !collapsed.value
}

const selectMenu = (item) => {
  router.push(item.path)
}

const goToSettings = () => {
  router.push('/admin/settings')
}
</script>

<template>
  <aside class="sidebar" :class="{ collapsed: collapsed }">
    <div class="sidebar-header">
      <div v-if="!collapsed" class="brand">
        <h2>Faculty of Science</h2>
        <p>UNIVERSITY PORTAL</p>
      </div>

      <div v-else class="brand-collapsed">Sci</div>

      <button class="toggle-btn" @click="toggleSidebar">
        <PanelLeftOpen v-if="collapsed" :size="19" />
        <PanelLeftClose v-else :size="19" />
      </button>
    </div>

    <nav class="menu">
      <button
        v-for="item in menuItems"
        :key="item.id"
        class="menu-item"
        :class="{ active: route.path === item.path }"
        @click="selectMenu(item)"
        :title="collapsed ? item.name : ''"
      >
        <component :is="item.icon" class="menu-icon" :size="19" />
        <span v-if="!collapsed">{{ item.name }}</span>
      </button>
    </nav>

    <div class="sidebar-footer">
      <button
        class="menu-item"
        :class="{ active: route.path === '/admin/settings' }"
        @click="goToSettings"
        :title="collapsed ? 'Settings' : ''"
      >
        <Settings class="menu-icon" :size="19" />
        <span v-if="!collapsed">Settings</span>
      </button>
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

  padding: 18px 12px;

  transition: width 0.25s ease;

  flex-shrink: 0;

  overflow-y: auto;

  z-index: 100;
}

.sidebar.collapsed { width: 72px; }

.sidebar-header {
  height: 60px;
  display: flex;
  align-items: flex-start;
  position: relative;
  margin-bottom: 20px;
}

.brand {
  padding-left: 8px;
  white-space: nowrap;
  overflow: hidden;
}

.brand h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #173f95;
}

.brand p {
  margin: 3px 0 0;
  font-size: 9px;
  letter-spacing: 0.7px;
  color: #94a3b8;
}

.brand-collapsed {
  width: 100%;
  text-align: center;
  color: #173f95;
  font-size: 15px;
  font-weight: 800;
}

.toggle-btn {
  position: absolute;
  right: -28px;
  top: 5px;
  width: 30px;
  height: 34px;
  border: 1px solid #e5eaf2;
  border-left: none;
  border-radius: 0 8px 8px 0;
  background: white;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: 0.2s;
  z-index: 10;
}

.toggle-btn:hover {
  background: #eff6ff;
  color: #2563eb;
}

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
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #52617a;
  cursor: pointer;
  position: relative;
  transition: 0.2s;
  white-space: nowrap;
}

.menu-item:hover { background: #f4f7fc; }
.menu-icon { min-width: 19px; color: #8799b3; }

.menu-item.active {
  background: #edf4ff;
  color: #1e4d8f;
}

.menu-item.active .menu-icon { color: #2563eb; }

.menu-item.active::after {
  content: '';
  position: absolute;
  right: -12px;
  height: 100%;
  width: 3px;
  background: #2563eb;
  border-radius: 3px 0 0 3px;
}

.sidebar-footer {
  margin-top: auto;
  border-top: 1px solid #edf0f4;
  padding-top: 12px;
}

.sidebar.collapsed .menu-item {
  justify-content: center;
  padding: 0;
  gap: 0;
}

.sidebar.collapsed .menu-item.active::after { right: -12px; }
</style>