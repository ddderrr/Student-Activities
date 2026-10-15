<script setup>
import { computed, nextTick, onBeforeUnmount, ref, useId, watch } from 'vue'
import { Check, ChevronDown } from 'lucide-vue-next'
import { moveActiveIndex, shouldOpenUpward, typeaheadIndex } from '../../utils/dropdownNavigation'

/*
  Dropdown แทน <select> ที่รายการเปิดลงใต้ช่องเสมอ (ยกเว้นใกล้ขอบล่างของจอจะเปิดขึ้นด้านบน)
  <select> ปกติบน Windows เด้งรายการขึ้นมาทับช่อง จึงทำเองตามแบบ ARIA "select-only combobox"

  v-model: ค่าที่เลือก (ตรงกับ option.value) ส่ง update:modelValue แล้วตามด้วย change
  เฉพาะตอนค่าเปลี่ยน เหมือน <select>
  options: [{ value, label }]
  id: ใส่ที่ปุ่มของช่อง ใช้กับ <label for> ให้คลิกชื่อช่องแล้วโฟกัสช่องได้
  labelledby: id ของ <label> ที่อธิบายช่องนี้ (screen reader อ่านชื่อช่อง)

  รายการ Teleport ไปไว้ที่ body และวางตำแหน่งตามช่อง (position: fixed) เพื่อไม่ให้การ์ดที่
  ครอบอยู่ (overflow) ตัดรายการ
*/

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  options: {
    type: Array,
    required: true
  },
  id: {
    type: String,
    default: undefined
  },
  labelledby: {
    type: String,
    default: undefined
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const MENU_MAX_HEIGHT = 300
const MENU_GAP = 6
const TYPEAHEAD_RESET_MS = 600
const VIEWPORT_MARGIN = 16

const listboxId = useId()
const trigger = ref(null)
const menu = ref(null)
const open = ref(false)
const activeIndex = ref(-1)
const menuStyle = ref({})
const openUpward = ref(false)

let typeaheadQuery = ''
let typeaheadTimer = null

const selectedIndex = computed(() =>
  props.options.findIndex((option) => option.value === props.modelValue)
)

const selectedLabel = computed(() => props.options[selectedIndex.value]?.label ?? '')

function optionId(index) {
  return `${listboxId}-option-${index}`
}

const activeDescendant = computed(() =>
  open.value && activeIndex.value >= 0 ? optionId(activeIndex.value) : undefined
)

function positionMenu() {
  if (!trigger.value) return

  const rect = trigger.value.getBoundingClientRect()
  const menuHeight = Math.min(menu.value?.scrollHeight || MENU_MAX_HEIGHT, MENU_MAX_HEIGHT)
  openUpward.value = shouldOpenUpward(rect, menuHeight, window.innerHeight, MENU_GAP)

  // กันรายการล้นขอบขวาของจอ (จอแคบ / ช่องอยู่ชิดขวา)
  const menuWidth = Math.max(menu.value?.offsetWidth || 0, rect.width)
  const left = Math.max(VIEWPORT_MARGIN, Math.min(rect.left, window.innerWidth - menuWidth - VIEWPORT_MARGIN))

  menuStyle.value = {
    left: `${left}px`,
    minWidth: `${rect.width}px`,
    ...(openUpward.value
      ? { bottom: `${window.innerHeight - rect.top + MENU_GAP}px` }
      : { top: `${rect.bottom + MENU_GAP}px` })
  }
}

function scrollActiveIntoView() {
  nextTick(() => {
    menu.value
      ?.querySelector(`#${CSS.escape(optionId(activeIndex.value))}`)
      ?.scrollIntoView({ block: 'nearest' })
  })
}

async function openMenu(startIndex = selectedIndex.value) {
  if (props.disabled || open.value) return

  activeIndex.value = startIndex >= 0 ? startIndex : 0
  open.value = true
  await nextTick()
  positionMenu()
  scrollActiveIntoView()
}

function closeMenu({ focusTrigger = false } = {}) {
  if (!open.value) return

  open.value = false
  if (focusTrigger) trigger.value?.focus()
}

function selectIndex(index) {
  const option = props.options[index]
  closeMenu({ focusTrigger: true })
  if (!option || option.value === props.modelValue) return

  emit('update:modelValue', option.value)
  emit('change', option.value)
}

function setActive(index) {
  activeIndex.value = index
  scrollActiveIntoView()
}

function handleTypeahead(key) {
  clearTimeout(typeaheadTimer)
  typeaheadQuery += key
  typeaheadTimer = setTimeout(() => {
    typeaheadQuery = ''
  }, TYPEAHEAD_RESET_MS)

  const current = open.value ? activeIndex.value : selectedIndex.value
  const index = typeaheadIndex(
    props.options.map((option) => option.label),
    typeaheadQuery,
    current
  )
  if (index < 0) return

  if (open.value) {
    setActive(index)
  } else {
    // ปิดอยู่: เปลี่ยนค่าทันทีเหมือน <select>
    selectIndex(index)
  }
}

function onKeydown(event) {
  if (props.disabled) return

  const { key } = event

  if (!open.value) {
    if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(key)) {
      event.preventDefault()
      openMenu()
    } else if (key === 'Home' || key === 'End') {
      event.preventDefault()
      openMenu(moveActiveIndex(selectedIndex.value, key, props.options.length))
    } else if (key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
      handleTypeahead(key)
    }
    return
  }

  if (['ArrowDown', 'ArrowUp', 'Home', 'End', 'PageDown', 'PageUp'].includes(key)) {
    event.preventDefault()
    if (key === 'ArrowUp' && event.altKey) {
      selectIndex(activeIndex.value)
      return
    }
    setActive(moveActiveIndex(activeIndex.value, key, props.options.length))
  } else if (key === 'Enter' || (key === ' ' && !typeaheadQuery)) {
    event.preventDefault()
    selectIndex(activeIndex.value)
  } else if (key === 'Escape') {
    event.preventDefault()
    closeMenu({ focusTrigger: true })
  } else if (key === 'Tab') {
    closeMenu()
  } else if (key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
    event.preventDefault()
    handleTypeahead(key)
  }
}

function onTriggerClick() {
  if (open.value) {
    closeMenu()
  } else {
    openMenu()
  }
}

// คลิกข้างนอก (ทั้งนอกช่องและนอกรายการ) = ปิด
function onDocumentPointerDown(event) {
  if (trigger.value?.contains(event.target) || menu.value?.contains(event.target)) return
  closeMenu()
}

// เลื่อนหน้า/ย่อขยายจอ: ขยับรายการตามช่อง (เลื่อนในรายการเองไม่ต้องขยับ)
function onViewportChange(event) {
  if (event?.target && menu.value?.contains(event.target)) return
  positionMenu()
}

watch(open, (isOpen) => {
  if (isOpen) {
    document.addEventListener('pointerdown', onDocumentPointerDown, true)
    window.addEventListener('scroll', onViewportChange, true)
    window.addEventListener('resize', onViewportChange)
  } else {
    document.removeEventListener('pointerdown', onDocumentPointerDown, true)
    window.removeEventListener('scroll', onViewportChange, true)
    window.removeEventListener('resize', onViewportChange)
  }
})

onBeforeUnmount(() => {
  clearTimeout(typeaheadTimer)
  document.removeEventListener('pointerdown', onDocumentPointerDown, true)
  window.removeEventListener('scroll', onViewportChange, true)
  window.removeEventListener('resize', onViewportChange)
})
</script>

<template>
  <div class="select-dropdown" :class="{ open, disabled }">
    <button
      :id="id"
      ref="trigger"
      type="button"
      class="select-dropdown-trigger"
      role="combobox"
      aria-haspopup="listbox"
      :aria-expanded="open ? 'true' : 'false'"
      :aria-controls="listboxId"
      :aria-labelledby="labelledby"
      :aria-activedescendant="activeDescendant"
      :disabled="disabled"
      @click="onTriggerClick"
      @keydown="onKeydown"
    >
      <span class="select-dropdown-value">
        <span class="select-dropdown-label">{{ selectedLabel }}</span>
        <!-- กว้างเท่าตัวเลือกที่ยาวที่สุดเหมือน <select> ปกติ layout ของหน้าเดิมจึงไม่เปลี่ยน -->
        <span
          v-for="option in options"
          :key="`sizer-${option.value}`"
          class="select-dropdown-sizer"
          aria-hidden="true"
        >{{ option.label }}</span>
      </span>
      <ChevronDown class="select-dropdown-chevron" :size="16" aria-hidden="true" />
    </button>

    <Teleport to="body">
      <ul
        v-show="open"
        :id="listboxId"
        ref="menu"
        class="select-dropdown-menu"
        :class="{ upward: openUpward }"
        role="listbox"
        :aria-labelledby="labelledby"
        :style="menuStyle"
        tabindex="-1"
      >
        <li
          v-for="(option, index) in options"
          :id="optionId(index)"
          :key="option.value"
          class="select-dropdown-option"
          :class="{ active: index === activeIndex, selected: index === selectedIndex }"
          role="option"
          :aria-selected="index === selectedIndex ? 'true' : 'false'"
          @mousemove="activeIndex = index"
          @mousedown.prevent
          @click="selectIndex(index)"
        >
          <span>{{ option.label }}</span>
          <Check
            v-if="index === selectedIndex"
            class="select-dropdown-check"
            :size="15"
            aria-hidden="true"
          />
        </li>
      </ul>
    </Teleport>
  </div>
</template>

<style scoped>
.select-dropdown {
  position: relative;
  width: 100%;
  min-width: 0;
}

.select-dropdown-trigger {
  width: 100%;
  height: 42px;
  padding: 0 10px 0 12px;

  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;

  border: 1px solid #dce5ef;
  border-radius: 9px;
  background: #fff;
  color: #34445a;

  font: inherit;
  font-size: var(--fs-body);
  text-align: left;

  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.select-dropdown-trigger:hover:not(:disabled) {
  border-color: #c5d3e4;
}

.select-dropdown-trigger:focus-visible,
.select-dropdown.open .select-dropdown-trigger {
  outline: none;
  border-color: #7bb1f5;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

.select-dropdown-trigger:disabled {
  background: #f5f7fa;
  color: #94a3b8;
  cursor: not-allowed;
}

/* ความกว้างขั้นต่ำ = ตัวเลือกที่ยาวที่สุด (ไม่หดเหมือน <select>) ถ้าหน้ากำหนดความกว้างช่องเอง
   ข้อความที่ยาวเกินจะถูกตัดเหมือน <select> */
.select-dropdown-value {
  display: grid;
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
}

.select-dropdown-label,
.select-dropdown-sizer {
  grid-area: 1 / 1;
  white-space: nowrap;
}

.select-dropdown-sizer {
  visibility: hidden;
  height: 0;
}

.select-dropdown-chevron {
  flex-shrink: 0;
  color: #7a8aa3;
  transition: transform 0.15s ease;
}

.select-dropdown.open .select-dropdown-chevron {
  transform: rotate(180deg);
}

.select-dropdown-menu {
  position: fixed;
  z-index: 1000;

  max-width: min(360px, calc(100vw - 32px));
  max-height: 300px;
  margin: 0;
  padding: 6px;
  overflow-y: auto;
  overscroll-behavior: contain;

  list-style: none;
  border: 1px solid #e3eaf3;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.12);

  font-size: var(--fs-body);
}

.select-dropdown-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;

  min-height: 36px;
  padding: 8px 10px;

  border-radius: 7px;
  color: #34445a;
  line-height: 1.35;
  cursor: pointer;
}

.select-dropdown-option.active {
  background: #f2f7ff;
}

.select-dropdown-option.selected {
  color: #1265d8;
  font-weight: 600;
}

.select-dropdown-check {
  flex-shrink: 0;
}
</style>
