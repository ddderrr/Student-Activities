<script setup>
import { computed } from 'vue'
import { useLanguage } from '../../composables/useLanguage'
import { getAdminSession } from '../../constants/currentAdmin'
import {
  ALL_BRANCHES_VALUE,
  BRANCHES,
  FACULTY_ACTIVITIES_VALUE,
  MY_BRANCH_ONLY_VALUE
} from '../../constants/branches'

/*
  Branch (สาขา) filter -- เฉพาะแอดมินกลางเท่านั้น (แอดมินสาขาถูก scope ตาม
  สาขาตัวเองอยู่แล้ว จึงไม่ต้องมี filter นี้) ใช้ร่วมกันในหน้า Dashboard,
  Activities, Student Skills, Approvals

  v-model ค่าเป็น ALL_BRANCHES_VALUE ("ทุกสาขา") หรือชื่อสาขาจาก BRANCHES

  activityScopeOptions (หน้า Activities): ตัวเลือกขอบเขตกิจกรรม และแสดงให้แอดมินสาขาด้วย
  - ทุกคน: FACULTY_ACTIVITIES_VALUE ("กิจกรรมส่วนกลางของคณะ")
  - แอดมินกลาง: เลือกสาขาแล้วมี checkbox "รวมกิจกรรมส่วนกลาง" (v-model:includeFaculty)
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
  },
  includeFaculty: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'update:includeFaculty'])

const { t } = useLanguage()

const isCentralAdmin = computed(() => getAdminSession()?.is_central === true)
const isBranchAdminScope = computed(() => props.activityScopeOptions && !isCentralAdmin.value)
// checkbox มีผลเฉพาะตอนแอดมินกลางเลือกสาขาใดสาขาหนึ่ง
const showIncludeFaculty = computed(() =>
  props.activityScopeOptions &&
  isCentralAdmin.value &&
  BRANCHES.includes(props.modelValue)
)
</script>

<template>
  <div v-if="isCentralAdmin || props.activityScopeOptions" class="branch-filter-field">
    <label>{{ t.common.branchLabel }}</label>

    <div class="branch-filter-controls">
      <select
        :value="modelValue"
        @change="emit('update:modelValue', $event.target.value)"
      >
        <option :value="ALL_BRANCHES_VALUE">
          {{ isBranchAdminScope ? t.common.myBranchAndFaculty : t.common.allBranches }}
        </option>
        <option v-if="props.activityScopeOptions" :value="FACULTY_ACTIVITIES_VALUE">
          {{ t.common.facultyActivities }}
        </option>
        <option v-if="isBranchAdminScope" :value="MY_BRANCH_ONLY_VALUE">
          {{ t.common.myBranchOnly }}
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

      <label v-if="showIncludeFaculty" class="include-faculty">
        <input
          type="checkbox"
          :checked="includeFaculty"
          @change="emit('update:includeFaculty', $event.target.checked)"
        >
        {{ t.common.includeFacultyActivities }}
      </label>
    </div>
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

.branch-filter-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

/* เต็มความกว้างเหมือนเดิมเมื่อไม่มี checkbox (หน้าอื่น) */
.branch-filter-controls select {
  flex: 1 1 180px;
  min-width: 0;
}

.branch-filter-field .include-faculty {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #34445a;
  font-size: var(--fs-body);
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
}

.branch-filter-field select:focus {
  outline: none;
  border-color: #7bb1f5;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}
</style>
