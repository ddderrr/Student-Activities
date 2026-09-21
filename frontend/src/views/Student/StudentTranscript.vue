<script setup>
import { useLanguage } from '../../composables/useLanguage'

const { t } = useLanguage()
</script>

<template>

  <div class="placeholder-page">

    <h1>{{ t.studentTranscript.title }}</h1>

    <p>
      {{ t.studentTranscript.comingSoon }}
    </p>

  </div>

</template>

<style scoped>

.placeholder-page {
  padding: 30px;
}

.placeholder-page h1 {
  color: #1d3268;
}

.placeholder-page p {
  color: #8492a6;
}

</style>
