<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'

// popup ยืนยันแทน window.confirm (ซึ่งขึ้นหัวว่า "localhost says")
// คลิกนอกกรอบไม่ปิด ต้องเลือกปุ่ม (Esc = ยกเลิก)
const props = defineProps({
  open: { type: Boolean, default: false },
  message: { type: String, required: true },
  confirmLabel: { type: String, required: true },
  cancelLabel: { type: String, required: true },
  busy: { type: Boolean, default: false }
})
const emit = defineEmits(['confirm', 'cancel'])

const cancelButton = ref(null)

function onKeydown(event) {
  if (event.key === 'Escape' && !props.busy) emit('cancel')
}

watch(
  () => props.open,
  async (open) => {
    if (open) {
      document.addEventListener('keydown', onKeydown)
      await nextTick()
      cancelButton.value?.focus()
    } else {
      document.removeEventListener('keydown', onKeydown)
    }
  }
)

onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="confirm-backdrop" data-testid="confirm-dialog">
      <div
        class="confirm-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-message"
      >
        <h3 id="confirm-message">{{ message }}</h3>

        <div class="confirm-actions">
          <button
            ref="cancelButton"
            type="button"
            class="cancel-button"
            data-testid="confirm-cancel"
            :disabled="busy"
            @click="emit('cancel')"
          >
            {{ cancelLabel }}
          </button>
          <button
            type="button"
            class="confirm-button"
            data-testid="confirm-ok"
            :disabled="busy"
            @click="emit('confirm')"
          >
            {{ confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.confirm-backdrop {
  position: fixed;
  inset: 0;
  z-index: 2000;
  padding: 20px;
  display: grid;
  place-items: center;
  background: rgba(28, 41, 61, 0.45);
}

.confirm-dialog {
  width: min(400px, 100%);
  padding: 28px 28px 24px;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 24px 60px rgba(28, 41, 61, 0.25);
  text-align: center;
}

.confirm-dialog h3 {
  margin: 0;
  color: #1c293d;
  font-size: 20px;
  line-height: 1.5;
}

.confirm-actions {
  margin-top: 22px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.confirm-actions button {
  min-height: 44px;
  border-radius: 10px;
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 700;
  cursor: pointer;
}

.confirm-actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cancel-button {
  border: 1px solid #dce5ef;
  background: #fff;
  color: #2f5fdb;
}

.cancel-button:hover:not(:disabled) {
  background: #f3f7ff;
}

.confirm-button {
  border: 0;
  background: #dc2626;
  color: #fff;
}

.confirm-button:hover:not(:disabled) {
  background: #b91c1c;
}
</style>
