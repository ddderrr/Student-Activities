<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import AdminSidebar from './components/Admin/AdminSideBar.vue'

const route = useRoute()


/* =========================
   Login
========================= */

const isLoginPage = computed(() => {
  return (
    route.path === '/' ||
    route.path === '/admin/login'
  )
})


/* =========================
   Admin
========================= */

const isAdminPage = computed(() => {
  return (
    route.path.startsWith('/admin/') &&
    route.path !== '/admin/login'
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
  >

    <AdminSidebar />

    <main class="main-content">

      <RouterView />

    </main>

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

</style>