<script setup>
import { useLanguage } from '../../composables/useLanguage'

const { t } = useLanguage()

const props = defineProps({
  definitions: {
    type: Array,
    required: true
  },
  // { [skillKey]: level (1-5) | null = ไม่เกี่ยวข้อง }
  modelValue: {
    type: Object,
    required: true
  },
  compact: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

// จำ level ล่าสุดไว้ เวลาติ๊ก "ไม่เกี่ยวข้อง" ออกจะได้กลับไปค่าเดิม
const lastLevels = {}

function isRelated(key) {
  return props.modelValue[key] !== null && props.modelValue[key] !== undefined
}

function setLevel(key, level) {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: level
  })
}

function setRelated(key, related) {
  if (related) {
    setLevel(key, lastLevels[key] ?? 3)
    return
  }

  lastLevels[key] = props.modelValue[key]
  setLevel(key, null)
}
</script>

<template>
  <div class="skill-list" :class="{ compact }">
    <article
      v-for="skill in definitions"
      :key="skill.key"
      class="skill-row"
      :class="{ 'not-related': !isRelated(skill.key) }"
      :data-skill="skill.key"
    >
      <div class="skill-topline">
        <div class="skill-name">
          <div class="skill-icon"><component :is="skill.icon" :size="18" /></div>
          <div>
            <strong>{{ skill.label }}</strong>
            <small>{{ skill.description }}</small>
          </div>
        </div>

        <div class="skill-controls">
          <label class="not-related-toggle">
            <input
              type="checkbox"
              :checked="!isRelated(skill.key)"
              @change="setRelated(skill.key, !$event.target.checked)"
            />
            {{ t.skillLevelEditor.notRelated }}
          </label>

          <span class="level-badge">
            {{ isRelated(skill.key) ? `${t.skillLevelEditor.level} ${modelValue[skill.key]}` : t.skillLevelEditor.notApplicable }}
          </span>
        </div>
      </div>

      <input
        :value="modelValue[skill.key] ?? lastLevels[skill.key] ?? 3"
        class="skill-range"
        type="range"
        min="1"
        max="5"
        step="1"
        :disabled="!isRelated(skill.key)"
        @input="setLevel(skill.key, Number($event.target.value))"
      />

      <div class="range-labels">
        <span v-for="level in 5" :key="level">{{ level }}</span>
      </div>
    </article>
  </div>
</template>

<style scoped>
.skill-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skill-row {
  padding: 17px 18px;
  border: 1px solid #e7ebf1;
  border-radius: 12px;
  background: #fbfcfe;
}

.skill-list.compact {
  gap: 8px;
}

.skill-list.compact .skill-row {
  padding: 11px 13px;
}

.skill-topline {
  margin-bottom: 13px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.skill-list.compact .skill-topline {
  margin-bottom: 7px;
}

.skill-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.skill-icon {
  width: 35px;
  height: 35px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: #f5f4f4;
  color: #1769dc;
}

.skill-name strong {
  display: block;
  color: #26364b;
  font-size: 12px;
}

.skill-name small {
  display: block;
  margin-top: 2px;
  color: #94a1b1;
  font-size: 9px;
}

.level-badge {
  padding: 5px 9px;
  border-radius: 999px;
  background: #e8f8ee;
  color: #17864d;
  font-size: 9px;
  font-weight: 800;
  white-space: nowrap;
}

.skill-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.not-related-toggle {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #66758c;
  font-size: 10px;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
}

.not-related-toggle input {
  width: 14px;
  height: 14px;
  margin: 0;
  accent-color: #155bc7;
  cursor: pointer;
}

.skill-row.not-related {
  background: #f6f7f9;
}

.skill-row.not-related .skill-name,
.skill-row.not-related .range-labels {
  opacity: 0.5;
}

.skill-row.not-related .level-badge {
  background: #eceff3;
  color: #7a8799;
}

.skill-range {
  width: 100%;
  accent-color: #155bc7;
  cursor: pointer;
}

.skill-range:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

.range-labels {
  margin-top: 3px;
  display: flex;
  justify-content: space-between;
  color: #8290a2;
  font-size: 9px;
}
</style>
