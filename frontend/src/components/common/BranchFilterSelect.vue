<script setup>
import { computed } from 'vue'
import { useLanguage } from '../../composables/useLanguage'
import { getAdminSession } from '../../constants/currentAdmin'
import { ALL_BRANCHES_VALUE, BRANCHES, FACULTY_ACTIVITIES_VALUE } from '../../constants/branches'

/*
  Branch (สาขา) filter -- เฉพาะแอดมินกลางเท่านั้น (แอดมินสาขาถูก scope ตาม
  สาขาตัวเองอยู่แล้ว จึงไม่ต้องมี filter นี้) ใช้ร่วมกันในหน้า Dashboard,
  Activities, Student Skills, Approvals

  v-model ค่าเป็น ALL_BRANCHES_VALUE ("ทุกสาขา") หรือชื่อสาขาจาก BRANCHES

  showFacultyOption (หน้า Activities): เพิ่มตัวเลือก FACULTY_ACTIVITIES_VALUE
  ("กิจกรรมส่วนกลางของคณะ") และแสดงให้แอดมินสาขาด้วย (เห็นเฉพาะตัวเลือกนี้กับ "ทุกสาขา")
*/

const props = defineProps({
  modelValue: {
    type: String,
    default: ALL_BRANCHES_VALUE
  },
  showFacultyOption: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const { t } = useLanguage()

const isCentralAdmin = computed(() => getAdminSession()?.is_central === true)
</script>

<template>
  <div v-if="isCentralAdmin || props.showFacultyOption" class="branch-filter-field">
    <label>{{ t.common.branchLabel }}</label>

    <select
      :value="modelValue"
      @change="emit('update:modelValue', $event.target.value)"
    >
      <option :value="ALL_BRANCHES_VALUE">{{ t.common.allBranches }}</option>
      <option v-if="props.showFacultyOption" :value="FACULTY_ACTIVITIES_VALUE">
        {{ t.common.facultyActivities }}
      </option>
      <template v-if="isCentralAdmin">
        <option
          v-for="branch in BRANCHES"
          :key="branch"
          :value="branch"
        >
          {{ branch }}
        </option>
      </template>
    </select>
  </div>
</template>

<style scoped>
.branch-filter-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  max-width: 100%;
}

.branch-filter-field label {
  font-size: var(--fs-small);
  font-weight: 600;
  color: #66758c;
}

.branch-filter-field select {
  height: 42px;
  padding: 0 12px;

  border: 1px solid #dce5ef;
  border-radius: 9px;

  background: #fff;
  color: #34445a;

  font: inherit;
  font-size: var(--fs-body);

  cursor: pointer;
  max-width: 100%;
}

.branch-filter-field select:focus {
  outline: none;
  border-color: #7bb1f5;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}
</style>
