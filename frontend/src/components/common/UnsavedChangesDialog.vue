<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { TriangleAlert } from 'lucide-vue-next'

import { useLanguage } from '../../composables/useLanguage'

// popup "ยังไม่เสร็จสิ้น ต้องการละทิ้งหรือไม่" ใช้คู่กับ useUnsavedChanges
// คลิกนอกกรอบไม่ปิด ต้องเลือกปุ่ม (Esc = อยู่ต่อ)
const props = defineProps({
  open: { type: Boolean, default: false },
  message: { type: String, default: '' }
})
const emit = defineEmits(['stay', 'leave'])

const { t } = useLanguage()
const stayButton = ref(null)

function onKeydown(event) {
  if (event.key === 'Escape') emit('stay')
}

watch(
  () => props.open,
  async (open) => {
    if (open) {
      document.addEventListener('keydown', onKeydown)
      await nextTick()
      stayButton.value?.focus()
    } else {
      document.removeEventListener('keydown', onKeydown)
    }
  }
)

onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="unsaved-backdrop" data-testid="unsaved-dialog">
      <div
        class="unsaved-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="unsaved-title"
        aria-describedby="unsaved-message"
      >
        <span class="unsaved-icon" aria-hidden="true"><TriangleAlert :size="28" /></span>
        <h3 id="unsaved-title">{{ t.unsavedChanges.title }}</h3>
        <p id="unsaved-message">{{ message || t.unsavedChanges.message }}</p>

        <div class="unsaved-actions">
          <button ref="stayButton" type="button" class="stay-button" data-testid="unsaved-stay" @click="emit('stay')">
            {{ t.unsavedChanges.stay }}
          </button>
          <button type="button" class="leave-button" data-testid="unsaved-leave" @click="emit('leave')">
            {{ t.unsavedChanges.leave }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.unsaved-backdrop {
  position: fixed;
  inset: 0;
  z-index: 2000;
  padding: 20px;
  display: grid;
  place-items: center;
  background: rgba(28, 41, 61, 0.45);
}

.unsaved-dialog {
  width: min(440px, 100%);
  padding: 30px 28px 24px;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 24px 60px rgba(28, 41, 61, 0.25);
  text-align: center;
}

.unsaved-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 14px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #fff4e5;
  color: #d97706;
}

.unsaved-dialog h3 {
  margin: 0 0 8px;
  color: #1c293d;
  font-size: 20px;
}

.unsaved-dialog p {
  margin: 0;
  color: #5b6b82;
  font-size: var(--fs-body);
  line-height: 1.6;
}

.unsaved-actions {
  margin-top: 22px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.unsaved-actions button {
  min-height: 44px;
  border-radius: 10px;
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 700;
  cursor: pointer;
}

.stay-button {
  border: 1px solid #dce5ef;
  background: #fff;
  color: #2f5fdb;
}

.stay-button:hover {
  background: #f3f7ff;
}

.leave-button {
  border: 0;
  background: #dc2626;
  color: #fff;
}

.leave-button:hover {
  background: #b91c1c;
}
</style>
