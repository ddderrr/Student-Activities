<script setup>
import { computed, useId } from 'vue'
import { useLanguage } from '../../composables/useLanguage'
import { getAdminSession } from '../../constants/currentAdmin'
import {
  ALL_BRANCHES_VALUE,
  BRANCHES,
  FACULTY_ACTIVITIES_VALUE,
  MY_BRANCH_ONLY_VALUE
} from '../../constants/branches'
import SelectDropdown from './SelectDropdown.vue'

/*
  Branch (สาขา) filter -- เฉพาะแอดมินกลางเท่านั้น (แอดมินสาขาถูก scope ตาม
  สาขาตัวเองอยู่แล้ว จึงไม่ต้องมี filter นี้) ใช้ร่วมกันในหน้า Dashboard,
  Activities, Student Skills, Approvals

  v-model ค่าเป็น ALL_BRANCHES_VALUE ("ทุกสาขา") หรือชื่อสาขาจาก BRANCHES

  activityScopeOptions (หน้า Activities): ตัวเลือกขอบเขตกิจกรรม และแสดงให้แอดมินสาขาด้วย
  - ทุกคน: FACULTY_ACTIVITIES_VALUE ("กิจกรรมส่วนกลางของคณะ")
  - แอดมินกลาง: เลือกสาขา = เฉพาะกิจกรรมของสาขานั้น ไม่รวมส่วนกลาง (ดู utils/activityBranchFilter.js)
  - แอดมินสาขา: "สาขาของฉันและส่วนกลาง" (= ALL_BRANCHES_VALUE) และ MY_BRANCH_ONLY_VALUE
*/

const props = defineProps({
  modelValue: {
    type: String,
    default: ALL_BRANCHES_VALUE
  },
  activityScopeOptions: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const { t } = useLanguage()

const isCentralAdmin = computed(() => getAdminSession()?.is_central === true)
const isBranchAdminScope = computed(() => props.activityScopeOptions && !isCentralAdmin.value)

const fieldId = useId()
const labelId = useId()

// ลำดับตัวเลือกเหมือน <select> เดิม
const branchOptions = computed(() => [
  {
    value: ALL_BRANCHES_VALUE,
    label: isBranchAdminScope.value ? t.value.common.myBranchAndFaculty : t.value.common.allBranches
  },
  ...(props.activityScopeOptions
    ? [{ value: FACULTY_ACTIVITIES_VALUE, label: t.value.common.facultyActivities }]
    : []),
  ...(isBranchAdminScope.value
    ? [{ value: MY_BRANCH_ONLY_VALUE, label: t.value.common.myBranchOnly }]
    : []),
  ...(isCentralAdmin.value ? BRANCHES.map((branch) => ({ value: branch, label: branch })) : [])
])
</script>

<template>
  <div v-if="isCentralAdmin || props.activityScopeOptions" class="branch-filter-field">
    <label :id="labelId" :for="fieldId">{{ t.common.branchLabel }}</label>

    <SelectDropdown
      :id="fieldId"
      :model-value="modelValue"
      :options="branchOptions"
      :labelledby="labelId"
      @update:model-value="emit('update:modelValue', $event)"
    />
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
</style>
