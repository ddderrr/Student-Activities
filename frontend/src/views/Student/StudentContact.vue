<script setup>
import { Mail, MessageCircleQuestion } from 'lucide-vue-next'

import { useLanguage } from '../../composables/useLanguage'

// หน้า "ติดต่อเรา" (เมนูศูนย์ช่วยเหลือ) ยังไม่มีข้อมูลติดต่อจริง เว้นช่องไว้ให้ใส่ภายหลัง
const { t } = useLanguage()
</script>

<template>
  <div class="contact-page">
    <div class="contact-container">
      <header class="page-heading">
        <h1>{{ t.studentContact.title }}</h1>
      </header>

      <section class="contact-card" data-testid="contact-page">
        <span class="contact-icon" aria-hidden="true"><Mail :size="34" /></span>
        <p class="contact-message">{{ t.studentContact.message }}</p>

        <div class="contact-info" data-testid="contact-info">
          <h2>{{ t.studentContact.channelsTitle }}</h2>
          <!-- TODO: ใส่อีเมล / เบอร์โทร / สำนักงาน เมื่อได้ข้อมูลจริง -->
          <div class="info-placeholder">
            <MessageCircleQuestion :size="20" aria-hidden="true" />
            <span>{{ t.studentContact.comingSoon }}</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.contact-page {
  width: 100%;
  min-height: 100vh;
  padding: 32px 32px 48px;
  box-sizing: border-box;
  background: #f5f7fb;
  color: #17213c;
  font-size: var(--fs-body);
  line-height: 1.6;
}

.contact-container {
  max-width: 720px;
  margin: 0 auto;
}

.page-heading {
  margin-bottom: 20px;
}

.page-heading h1 {
  margin: 0;
  color: #172d68;
  font-size: 28px;
  line-height: 1.3;
}

.contact-card {
  padding: 40px 32px;
  border: 1px solid #dfe4ee;
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #fff;
  box-shadow: 0 1px 2px rgba(23, 45, 104, 0.04), 0 8px 24px rgba(23, 45, 104, 0.05);
  text-align: center;
}

.contact-icon {
  width: 76px;
  height: 76px;
  border-radius: 22px;
  display: grid;
  place-items: center;
  background: #f3e6fb;
  color: #8d00c4;
}

.contact-message {
  max-width: 440px;
  margin: 18px 0 0;
  color: #34445a;
  font-size: var(--fs-lead);
  font-weight: 500;
}

.contact-info {
  width: 100%;
  margin-top: 30px;
  padding-top: 24px;
  border-top: 1px solid #eef1f6;
}

.contact-info h2 {
  margin: 0 0 12px;
  color: #5b6b82;
  font-size: var(--fs-small);
  font-weight: 700;
  letter-spacing: 0.04em;
}

.info-placeholder {
  min-height: 96px;
  padding: 20px;
  border: 2px dashed #dfe4ee;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #8793aa;
  font-size: var(--fs-small);
}

@media (max-width: 700px) {
  .contact-page {
    padding: 20px 16px 36px;
  }

  .page-heading h1 {
    font-size: 24px;
  }

  .contact-card {
    padding: 28px 18px;
  }
}
</style>
