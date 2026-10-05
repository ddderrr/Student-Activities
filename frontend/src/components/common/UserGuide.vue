<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, BookOpen, ChevronDown, Lightbulb } from 'lucide-vue-next'

// หน้าคู่มือการใช้งาน (นักศึกษา / แอดมิน ใช้ร่วมกัน)
// sections: [{ key, icon, tone, path, title, summary, topics: [{ heading, badge?, text?, steps?, groups?, tip? }] }]
// labels: { title, subtitle, jumpTo, expandAll, collapseAll, openPage, tip }
const props = defineProps({
  sections: { type: Array, required: true },
  labels: { type: Object, required: true },
  // สีหลักของหน้า: purple = นักศึกษา, blue = แอดมิน
  accent: { type: String, default: 'purple' }
})

const route = useRoute()
const router = useRouter()

const sectionKeys = computed(() => props.sections.map((section) => section.key))

// ทางลัด: ไม่เกิน 4 หัวข้อ = แถวเดียว, มากกว่านั้น = 3 คอลัมน์ (6 หัวข้อ = 3 + 3)
const quickColumns = computed(() => Math.min(props.sections.length, 4) === props.sections.length ? props.sections.length : 3)

// เปิดได้หลายหัวข้อพร้อมกัน เริ่มที่หัวข้อแรก (หรือหัวข้อใน #hash)
const openKeys = ref(new Set())
const allOpen = computed(() => sectionKeys.value.every((key) => openKeys.value.has(key)))

function isOpen(key) {
  return openKeys.value.has(key)
}

function toggle(key) {
  const next = new Set(openKeys.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  openKeys.value = next
}

function toggleAll() {
  openKeys.value = allOpen.value ? new Set() : new Set(sectionKeys.value)
}

const sectionFromHash = () => {
  const key = route.hash.slice(1)
  return sectionKeys.value.includes(key) ? key : null
}

async function openAndScroll(key) {
  openKeys.value = new Set([...openKeys.value, key])
  await nextTick()
  document.getElementById(`guide-${key}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// ลิงก์ .../guide#skills เปิดหัวข้อนั้น (การเปลี่ยน hash จะเรียก watch ด้านล่าง)
function jumpTo(key) {
  if (route.hash === `#${key}`) openAndScroll(key)
  else router.replace({ hash: `#${key}` })
}

watch(() => route.hash, () => {
  const key = sectionFromHash()
  if (key) openAndScroll(key)
})

onMounted(() => {
  const key = sectionFromHash()
  if (key) openAndScroll(key)
  else if (sectionKeys.value.length) openKeys.value = new Set([sectionKeys.value[0]])
})
</script>

<template>
  <div class="guide-page" :class="`accent-${accent}`">
    <div class="guide-container">
      <header class="page-heading">
        <span class="heading-icon" aria-hidden="true"><BookOpen :size="26" /></span>
        <div>
          <h1>{{ labels.title }}</h1>
          <p>{{ labels.subtitle }}</p>
          <slot name="badge" />
        </div>
      </header>

      <nav class="quick-nav" :style="{ '--quick-cols': quickColumns }" :aria-label="labels.jumpTo">
        <button
          v-for="section in sections"
          :key="section.key"
          type="button"
          class="quick-card"
          :class="section.tone"
          :data-testid="`guide-jump-${section.key}`"
          @click="jumpTo(section.key)"
        >
          <span class="section-icon" :class="section.tone"><component :is="section.icon" :size="20" /></span>
          <span class="quick-text">
            <strong>{{ section.title }}</strong>
            <small>{{ section.summary }}</small>
          </span>
        </button>
      </nav>

      <div class="list-toolbar">
        <button type="button" class="text-button" data-testid="guide-toggle-all" @click="toggleAll">
          {{ allOpen ? labels.collapseAll : labels.expandAll }}
        </button>
      </div>

      <section
        v-for="section in sections"
        :id="`guide-${section.key}`"
        :key="section.key"
        class="guide-section"
        :class="{ open: isOpen(section.key) }"
        :data-section="section.key"
      >
        <h2 class="section-header">
          <button
            type="button"
            class="section-toggle"
            :aria-expanded="isOpen(section.key)"
            :aria-controls="`guide-body-${section.key}`"
            :data-testid="`guide-toggle-${section.key}`"
            @click="toggle(section.key)"
          >
            <span class="section-icon" :class="section.tone" aria-hidden="true">
              <component :is="section.icon" :size="22" />
            </span>
            <span class="section-text">
              <span class="section-title">{{ section.title }}</span>
              <span class="section-summary">{{ section.summary }}</span>
            </span>
            <ChevronDown class="chevron" :size="20" aria-hidden="true" />
          </button>
        </h2>

        <div v-show="isOpen(section.key)" :id="`guide-body-${section.key}`" class="section-body">
          <article v-for="(topic, index) in section.topics" :key="index" class="topic">
            <h3>
              <span class="topic-number" :class="section.tone">{{ index + 1 }}</span>
              {{ topic.heading }}
              <span v-if="topic.badge" class="topic-badge">{{ topic.badge }}</span>
            </h3>

            <p v-if="topic.text" class="topic-text">{{ topic.text }}</p>

            <ol v-if="topic.steps" class="steps">
              <li v-for="(step, stepIndex) in topic.steps" :key="stepIndex">{{ step }}</li>
            </ol>

            <div v-for="(group, groupIndex) in topic.groups || []" :key="groupIndex" class="term-group">
              <h4 v-if="group.label">{{ group.label }}</h4>
              <dl class="terms">
                <div v-for="item in group.items" :key="item.term" class="term">
                  <dt>{{ item.term }}</dt>
                  <dd>{{ item.text }}</dd>
                </div>
              </dl>
            </div>

            <p v-if="topic.tip" class="tip">
              <Lightbulb :size="16" aria-hidden="true" />
              <span><b>{{ labels.tip }}:</b> {{ topic.tip }}</span>
            </p>
          </article>

          <div v-if="section.path" class="section-footer">
            <button type="button" class="open-page" :class="section.tone" @click="router.push(section.path)">
              {{ labels.openPage }} “{{ section.title }}”
              <ArrowRight :size="16" />
            </button>
          </div>
        </div>
      </section>

      <slot name="footer" />
    </div>
  </div>
</template>

<style scoped>
.guide-page {
  --guide-accent: #8d00c4;
  --guide-accent-soft: #f3e6fb;
  --guide-accent-border: #d6c3ec;
  --guide-accent-hover: #faf7fd;
  width: 100%;
  min-height: 100vh;
  padding: 32px 32px 48px;
  box-sizing: border-box;
  background: #f5f7fb;
  color: #17213c;
  font-size: var(--fs-body);
  line-height: 1.6;
}

.guide-page.accent-blue {
  --guide-accent: #2f5fdb;
  --guide-accent-soft: #e8f0ff;
  --guide-accent-border: #c3d4f5;
  --guide-accent-hover: #f6f9ff;
}

.guide-container {
  max-width: 980px;
  margin: 0 auto;
}

.page-heading {
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.heading-icon {
  flex-shrink: 0;
  width: 54px;
  height: 54px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: var(--guide-accent-soft);
  color: var(--guide-accent);
}

.page-heading h1 {
  margin: 0 0 4px;
  color: #172d68;
  font-size: 28px;
  line-height: 1.3;
}

.page-heading p {
  margin: 0;
  color: #6b7891;
}

/* ทางลัดไปหัวข้อ */
.quick-nav {
  display: grid;
  grid-template-columns: repeat(var(--quick-cols, 4), minmax(0, 1fr));
  gap: 12px;
}

.quick-card {
  padding: 14px;
  border: 1px solid #dfe4ee;
  border-radius: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: #fff;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
}

.quick-card:hover {
  border-color: var(--guide-accent-border);
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(23, 45, 104, 0.07);
}

.quick-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.quick-text strong {
  color: #172d68;
  font-size: var(--fs-small);
  line-height: 1.4;
}

.quick-text small {
  color: #7b879c;
  font-size: var(--fs-caption);
  line-height: 1.45;
}

.section-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
}

.section-icon.purple { background: #f3e6fb; color: #8d00c4; }
.section-icon.green { background: #e6f6ec; color: #16803c; }
.section-icon.amber { background: #fff3db; color: #b45f06; }
.section-icon.blue { background: #e8f0ff; color: #2f5fdb; }
.section-icon.rose { background: #ffe9ee; color: #c8264e; }
.section-icon.slate { background: #eceff4; color: #42526b; }

.list-toolbar {
  margin: 22px 0 10px;
  display: flex;
  justify-content: flex-end;
}

.text-button {
  border: 0;
  background: none;
  color: var(--guide-accent);
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 600;
  cursor: pointer;
}

.text-button:hover {
  text-decoration: underline;
}

/* หัวข้อแบบพับได้ */
.guide-section {
  margin-bottom: 14px;
  border: 1px solid #dfe4ee;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(23, 45, 104, 0.04);
  scroll-margin-top: 80px;
  overflow: hidden;
}

.guide-section.open {
  border-color: var(--guide-accent-border);
  box-shadow: 0 8px 24px rgba(23, 45, 104, 0.06);
}

.section-header {
  margin: 0;
}

.section-toggle {
  width: 100%;
  padding: 18px 22px;
  border: 0;
  display: flex;
  align-items: center;
  gap: 16px;
  background: #fff;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.section-toggle:hover {
  background: var(--guide-accent-hover);
}

.section-toggle:focus-visible {
  outline: 3px solid rgba(141, 0, 196, 0.25);
  outline-offset: -3px;
}

.section-toggle .section-icon {
  width: 46px;
  height: 46px;
}

.section-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.section-title {
  color: #172d68;
  font-size: var(--fs-lead);
  font-weight: 700;
  line-height: 1.4;
}

.section-summary {
  color: #7b879c;
  font-size: var(--fs-small);
  font-weight: 400;
}

.chevron {
  flex-shrink: 0;
  color: #8793aa;
  transition: transform 0.2s ease;
}

.guide-section.open .chevron {
  transform: rotate(180deg);
}

.section-body {
  padding: 4px 22px 22px;
  border-top: 1px solid #f0edf5;
}

.topic {
  padding: 18px 0;
  border-bottom: 1px dashed #e6e9f0;
}

.topic:last-of-type {
  border-bottom: 0;
}

.topic h3 {
  margin: 0 0 10px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  color: #1c293d;
  font-size: var(--fs-body);
  font-weight: 700;
}

.topic-number {
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: var(--fs-caption);
  font-weight: 700;
}

.topic-number.purple { background: #f3e6fb; color: #8d00c4; }
.topic-number.green { background: #e6f6ec; color: #16803c; }
.topic-number.amber { background: #fff3db; color: #b45f06; }
.topic-number.blue { background: #e8f0ff; color: #2f5fdb; }
.topic-number.rose { background: #ffe9ee; color: #c8264e; }
.topic-number.slate { background: #eceff4; color: #42526b; }

.topic-badge {
  padding: 2px 9px;
  border-radius: 999px;
  background: #eef1f6;
  color: #42526b;
  font-size: var(--fs-caption);
  font-weight: 600;
  white-space: nowrap;
}

.topic-text {
  margin: 0;
  padding-left: 36px;
  color: #34445a;
}

.steps {
  margin: 0;
  padding-left: 58px;
  color: #34445a;
}

.steps li + li {
  margin-top: 6px;
}

.steps li::marker {
  color: #8793aa;
  font-weight: 700;
}

.term-group {
  padding-left: 36px;
}

.term-group + .term-group {
  margin-top: 14px;
}

.term-group h4 {
  margin: 0 0 8px;
  color: #5b6b82;
  font-size: var(--fs-small);
  font-weight: 700;
}

.terms {
  margin: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.term {
  padding: 10px 14px;
  border: 1px solid #eceff5;
  border-radius: 12px;
  background: #fafbfd;
}

.term dt {
  color: #1c293d;
  font-size: var(--fs-small);
  font-weight: 700;
}

.term dd {
  margin: 2px 0 0;
  color: #5b6b82;
  font-size: var(--fs-small);
}

.tip {
  margin: 12px 0 0 36px;
  padding: 10px 14px;
  border-radius: 12px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #fff8e6;
  color: #7a4b00;
  font-size: var(--fs-small);
}

.tip svg {
  flex-shrink: 0;
  margin-top: 3px;
}

.section-footer {
  padding-top: 6px;
  display: flex;
  justify-content: flex-end;
}

.open-page {
  height: 40px;
  padding: 0 16px;
  border: 0;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font: inherit;
  font-size: var(--fs-small);
  font-weight: 600;
  cursor: pointer;
}

.open-page.purple { background: #f3e6fb; color: #7a00aa; }
.open-page.green { background: #e6f6ec; color: #126b32; }
.open-page.amber { background: #fff3db; color: #96500a; }
.open-page.blue { background: #e8f0ff; color: #2550c0; }
.open-page.rose { background: #ffe9ee; color: #b01f44; }
.open-page.slate { background: #eceff4; color: #34445a; }

.open-page:hover {
  filter: brightness(0.96);
}

@media (max-width: 900px) {
  .quick-nav {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .guide-page {
    padding: 20px 16px 36px;
  }

  .page-heading h1 {
    font-size: 24px;
  }

  .heading-icon {
    width: 46px;
    height: 46px;
  }

  .quick-nav {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .quick-card {
    padding: 10px;
    align-items: center;
  }

  .quick-card .section-icon {
    width: 34px;
    height: 34px;
  }

  /* จอเล็ก: ทางลัดเหลือแค่ชื่อหัวข้อ คำอธิบายอยู่ในหัวข้อด้านล่างแล้ว */
  .quick-text small {
    display: none;
  }

  .section-toggle {
    padding: 16px;
    gap: 12px;
  }

  .section-body {
    padding: 4px 16px 18px;
  }

  .topic-text,
  .term-group {
    padding-left: 0;
  }

  .steps {
    padding-left: 22px;
  }

  .tip {
    margin-left: 0;
  }

  .terms {
    grid-template-columns: 1fr;
  }
}
</style>
