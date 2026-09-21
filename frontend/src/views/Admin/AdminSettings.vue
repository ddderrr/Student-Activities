<script setup>
import { useLanguage } from '../../composables/useLanguage'

const { t } = useLanguage()
</script>

<template>
  <div class="settings-page">
    <h1>{{ t.adminSettings.title }}</h1>
    <p>{{ t.adminSettings.comingSoon }}</p>
  </div>
</template>

<style scoped>
.settings-page {
  padding: 32px;
}

h1 {
  color: #162f65;
}
</style>
