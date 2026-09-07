<script setup>
import Sidebar from './components/Admin/AdminSideBar.vue'
</script>

<template>
  <div class="app-layout">
    <Sidebar />

    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family:
    Inter,
    Arial,
    sans-serif;

  background: #f7f8fc;
}

.app-layout {
  display: flex;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  min-width: 0;
  min-height: 100vh;
}
</style>