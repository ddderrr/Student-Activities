<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import AdminSidebar from './components/Admin/AdminSideBar.vue'
// import StudentSidebar from './components/Student/StudentSideBar.vue'

const route = useRoute()

const isLoginPage = computed(() => {
  return (
    route.path === '/' ||
    route.path === '/admin/login'
  )
})

const isAdminPage = computed(() => {
  return route.path.startsWith('/admin/')
})

const isStudentPage = computed(() => {
  return route.path.startsWith('/student/')
})
</script>

<template>

  <!-- =====================
       Login
  ====================== -->

  <RouterView v-if="isLoginPage" />


  <!-- =====================
       Admin
  ====================== -->

  <div
    v-else-if="isAdminPage"
    class="app-layout"
  >

    <AdminSidebar />

    <main class="main-content">
      <RouterView />
    </main>

  </div>


  <!-- =====================
       Student
  ====================== -->

  <div
    v-else-if="isStudentPage"
    class="app-layout"
  >

    <!-- ตอนทำ Student ค่อยเปิด -->
    <!-- <StudentSidebar /> -->

    <main class="main-content">
      <RouterView />
    </main>

  </div>


  <!-- =====================
       Other
  ====================== -->

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
  font-family:
    Inter,
    Arial,
    sans-serif;

  background: #f7f8fc;
}

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