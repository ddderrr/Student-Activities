<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Menu } from 'lucide-vue-next'

import AdminSidebar from './components/Admin/AdminSideBar.vue'
import { useLanguage } from './composables/useLanguage'

const route = useRoute()
const { t } = useLanguage()


/* =========================
   Admin Sidebar
   จอ ≤700px sidebar เป็น drawer ทับหน้า (breakpoint เดียวกับฝั่งนักศึกษา)
   จึงเริ่มแบบปิด ส่วนจอใหญ่เริ่มแบบกางเหมือนเดิม
========================= */

const mobileQuery = window.matchMedia('(max-width: 700px)')
const adminSidebarOpen = ref(!mobileQuery.matches)

const toggleAdminSidebar = () => {
  adminSidebarOpen.value = !adminSidebarOpen.value
}

// ย่อ/ขยายจอข้าม breakpoint: เข้ามือถือ = ปิด drawer, กลับจอใหญ่ = กาง
const onMobileQueryChange = (event) => {
  adminSidebarOpen.value = !event.matches
}

// มือถือ: เปลี่ยนหน้าแล้วปิด drawer ไม่ให้บังหน้าใหม่
watch(
  () => route.fullPath,
  () => {
    if (mobileQuery.matches) adminSidebarOpen.value = false
  }
)

const closeAdminSidebarOnEscape = (event) => {
  if (event.key === 'Escape' && mobileQuery.matches && adminSidebarOpen.value) {
    adminSidebarOpen.value = false
  }
}

onMounted(() => {
  mobileQuery.addEventListener('change', onMobileQueryChange)
  document.addEventListener('keydown', closeAdminSidebarOnEscape)
})

onBeforeUnmount(() => {
  mobileQuery.removeEventListener('change', onMobileQueryChange)
  document.removeEventListener('keydown', closeAdminSidebarOnEscape)
})


/* =========================
   Login
========================= */

const isLoginPage = computed(() => {
  return (
    route.path === '/login'
  )
})


/* =========================
   Admin
========================= */

const isAdminPage = computed(() => {
  return (
    route.path.startsWith('/admin/') &&
    route.path !== '/login'
  )
})
</script>


<template>

  <!-- =========================
       Login
  ========================== -->

  <RouterView
    v-if="isLoginPage"
  />


  <!-- =========================
       Admin
  ========================== -->

  <div
    v-else-if="isAdminPage"
    class="app-layout"
    :class="{ 'admin-sidebar-open': adminSidebarOpen }"
  >

    <AdminSidebar
      class="admin-sidebar-component"
      :collapsed="!adminSidebarOpen"
      @toggle="toggleAdminSidebar"
    />

    <main class="main-content">

      <!-- มือถือเท่านั้น: หน้า admin ไม่มี topbar จึงต้องมีปุ่มเปิด drawer -->
      <header class="admin-mobile-topbar">
        <button
          class="admin-mobile-menu-button"
          type="button"
          :title="t.adminSidebar.openSidebar"
          :aria-label="t.adminSidebar.openSidebar"
          :aria-expanded="adminSidebarOpen"
          @click="toggleAdminSidebar"
        >
          <Menu :size="21" />
        </button>

        <strong>{{ t.adminSidebar.faculty }}</strong>
      </header>

      <RouterView />

    </main>

    <div
      v-if="adminSidebarOpen"
      class="admin-mobile-overlay"
      @click="adminSidebarOpen = false"
    ></div>

  </div>


  <!-- =========================
       Student / Other
  ========================== -->

  <RouterView v-else />

</template>


<style>

* {
  box-sizing: border-box;
}


html,
body,
#app {
  margin: 0;
  padding: 0;

  width: 100%;
  min-height: 100%;
}


body {
  /* Inter คุมภาษาอังกฤษ, Sarabun คุม fallback ภาษาไทย (Inter ไม่มี glyph ไทย
     เบราว์เซอร์จะข้ามไปใช้ Sarabun ให้อัตโนมัติเมื่อเจอตัวอักษรไทย) */
  font-family:
    'Inter',
    'Sarabun',
    Arial,
    sans-serif;

  font-weight: 400;
  line-height: 1.6;

  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;

  background: #f7f8fc;
}

h1, h2, h3, h4, h5, h6 {
  font-weight: 700;
  line-height: 1.3;
}


/* =========================
   Admin Layout
========================= */

.app-layout {
  display: flex;

  width: 100%;

  min-height: 100vh;
}


.main-content {
  flex: 1;

  min-width: 0;

  min-height: 100vh;
}


.admin-mobile-topbar,
.admin-mobile-overlay {
  display: none;
}


@media (max-width: 700px) {
  /* .sidebar ใน AdminSideBar เป็น sticky: ใช้ selector ที่เจาะจงกว่า scoped style */
  .app-layout > .admin-sidebar-component.sidebar {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 1001;

    width: 240px;
    height: 100vh;

    transform: translateX(-100%);
    transition: transform 0.25s ease;
  }

  .app-layout.admin-sidebar-open > .admin-sidebar-component.sidebar {
    transform: translateX(0);
  }

  .admin-mobile-overlay {
    position: fixed;
    inset: 0;
    z-index: 1000;

    display: block;

    background: rgba(15, 23, 42, 0.25);
  }

  .admin-mobile-topbar {
    position: sticky;
    top: 0;
    z-index: 100;

    height: 56px;
    padding: 0 14px;

    display: flex;
    align-items: center;
    gap: 10px;

    background: #fff;
    border-bottom: 1px solid #e5eaf2;

    color: #1d3268;
    font-size: var(--fs-lead);
  }

  .admin-mobile-menu-button {
    width: 38px;
    height: 38px;
    padding: 0;

    border: none;
    border-radius: 9px;

    display: grid;
    place-items: center;

    background: #f3f6fb;
    color: #1d3268;

    cursor: pointer;
  }
}

</style>