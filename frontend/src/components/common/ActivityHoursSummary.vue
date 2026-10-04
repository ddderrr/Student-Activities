<script setup>
import { useLanguage } from '../../composables/useLanguage'
defineProps({ hours: { type: Object, default: () => ({}) }, panel: Boolean })
const { t } = useLanguage()
</script>

<template>
  <section v-if="panel" class="hours-panel" data-testid="hours-summary" :aria-label="t.activityHours.label">
    <h2>{{ t.activityHours.label }}</h2>
    <div class="hours-grid">
      <div v-for="key in ['total', 'major', 'faculty', 'external']" :key="key" class="hours-stat" :class="{ 'hours-total': key === 'total' }">
        <span>{{ t.activityHours[key] }}</span>
        <div><strong>{{ hours[key] ?? 0 }}</strong><small>{{ t.activityHours.unit }}</small></div>
      </div>
    </div>
  </section>
  <div v-else class="hours-summary" data-testid="hours-summary">
    <span><strong>{{ t.activityHours.total }}:</strong> {{ hours.total ?? 0 }} {{ t.activityHours.unit }}</span>
    <small>{{ t.activityHours.major }}: {{ hours.major ?? 0 }} {{ t.activityHours.unit }}</small>
    <small>{{ t.activityHours.faculty }}: {{ hours.faculty ?? 0 }} {{ t.activityHours.unit }}</small>
    <small>{{ t.activityHours.external }}: {{ hours.external ?? 0 }} {{ t.activityHours.unit }}</small>
  </div>
</template>

<style scoped>
.hours-summary { display: flex; flex-wrap: wrap; gap: 6px 14px; margin: 8px 0; align-items: baseline; font-size: 14px; }
.hours-summary small { color: #64748b; }
.hours-panel { padding: 16px 20px; border: 1px solid #dce4ef; border-radius: 12px; background: #f8faff; }
.hours-panel h2 { margin: 0 0 12px; color: #465776; font-size: 14px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
.hours-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px 20px; }
.hours-stat { min-width: 0; color: #53627a; font-size: 14px; line-height: 1.5; }
.hours-stat > span { display: block; }
.hours-stat > div { display: flex; align-items: baseline; gap: 7px; margin-top: 4px; }
.hours-stat strong { color: #17356e; font-size: 22px; font-weight: 700; }
.hours-stat small { font-size: 13px; color: #64748b; }
.hours-total strong { font-weight: 800; color: #214fad; }
@media (max-width: 700px) { .hours-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 360px) { .hours-grid { grid-template-columns: 1fr; } }
</style>
