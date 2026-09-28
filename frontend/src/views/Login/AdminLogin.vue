<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLanguage } from '../../composables/useLanguage'
import {
  clearAdminSession,
  fetchAdminBypassStatus,
  setAdminSession,
  verifyAdminSession
} from '../../constants/currentAdmin'

import {
  GraduationCap,
  Mail,
  ArrowRight,
  Undo2,
  TriangleAlert
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const { t } = useLanguage()

/*
  ADMIN LOGIN (โหมด bypass สำหรับพัฒนา)
  เลือกหรือพิมพ์อีเมลจากรายชื่อแอดมินทดสอบที่ backend ส่งมา ไม่ต้องใส่รหัสผ่าน
  เปลี่ยนเป็น login จริงทีหลัง: แก้หน้านี้ + constants/currentAdmin.js
*/

const loading = ref(true)
const bypassEnabled = ref(false)
const backendError = ref(false)
const accounts = ref([])
const email = ref('')
const errorMessage = ref('')
const submitting = ref(false)

const unauthorized = computed(() => route.query.reason === 'unauthorized')

const majorLabel = (account) =>
  account.is_central ? t.value.adminLogin.centralMajor : account.major

const loadBypassStatus = async () => {
  loading.value = true
  backendError.value = false

  try {
    const status = await fetchAdminBypassStatus()
    bypassEnabled.value = status.enabled
    accounts.value = status.accounts || []

    if (!status.enabled) {
      clearAdminSession()
    }
  } catch {
    backendError.value = true
  } finally {
    loading.value = false
  }
}

const chooseAccount = (account) => {
  email.value = account.email
  errorMessage.value = ''
}

const loginAdmin = async () => {
  errorMessage.value = ''

  const normalized = email.value.trim().toLowerCase()
  const account = accounts.value.find((item) => item.email === normalized)

  if (!account) {
    errorMessage.value = t.value.adminLogin.unknownEmail
    return
  }

  submitting.value = true

  try {
    setAdminSession(account)
    const admin = await verifyAdminSession()

    if (!admin) {
      errorMessage.value = t.value.adminLogin.unknownEmail
      await loadBypassStatus()
      return
    }

    const redirect = typeof route.query.redirect === 'string' &&
      route.query.redirect.startsWith('/admin/')
      ? route.query.redirect
      : '/admin/dashboard'

    router.push(redirect)
  } catch {
    clearAdminSession()
    errorMessage.value = t.value.adminLogin.backendUnavailable
  } finally {
    submitting.value = false
  }
}

const goBack = () => {
  router.push('/')
}

onMounted(loadBypassStatus)
</script>


<template>
  <div class="admin-login-page">

    <!-- LEFT -->
    <div class="image-side">
      <div class="image-overlay"></div>
    </div>


    <!-- RIGHT -->
    <div class="login-side">

      <!-- Back -->
      <button
        class="back-btn"
        type="button"
        @click="goBack"
      >
        <Undo2 :size="26" />
      </button>


      <div class="login-container">

        <!-- Header -->
        <div class="admin-title">

          <div class="admin-icon">
            <GraduationCap :size="22" />
          </div>

          <div>
            <h1>{{ t.adminLogin.title }}</h1>
            <p>{{ t.adminLogin.subtitle }}</p>
          </div>

        </div>


        <p v-if="loading" class="status-text">
          {{ t.adminLogin.loading }}
        </p>


        <!-- ต่อ backend ไม่ได้ -->
        <div v-else-if="backendError" class="notice notice-error" role="alert">
          <TriangleAlert :size="18" />
          <div>
            <strong>{{ t.adminLogin.backendUnavailable }}</strong>
            <button class="retry-btn" type="button" @click="loadBypassStatus">
              {{ t.adminLogin.retry }}
            </button>
          </div>
        </div>


        <!-- bypass ปิดอยู่ -->
        <div
          v-else-if="!bypassEnabled"
          class="notice notice-warning"
          role="alert"
          data-testid="bypass-disabled"
        >
          <TriangleAlert :size="18" />
          <div>
            <strong>{{ t.adminLogin.bypassDisabledTitle }}</strong>
            <p>{{ t.adminLogin.bypassDisabledStep1 }}</p>
            <code>ADMIN_BYPASS_ENABLED=true</code>
            <p>{{ t.adminLogin.bypassDisabledStep2 }}</p>
            <code>docker compose up -d backend</code>
            <button class="retry-btn" type="button" @click="loadBypassStatus">
              {{ t.adminLogin.retry }}
            </button>
          </div>
        </div>


        <!-- Form -->
        <form v-else @submit.prevent="loginAdmin">

          <div class="notice notice-info">
            <TriangleAlert :size="18" />
            <p>{{ t.adminLogin.bypassNotice }}</p>
          </div>

          <p v-if="unauthorized" class="error-text" role="alert">
            {{ t.adminLogin.sessionExpired }}
          </p>

          <div class="form-group">

            <label for="admin-email">
              {{ t.adminLogin.emailLabel }}
            </label>

            <div class="input-wrapper">

              <Mail
                class="input-icon"
                :size="17"
              />

              <input
                id="admin-email"
                v-model="email"
                type="email"
                list="admin-email-options"
                autocomplete="off"
                :placeholder="t.adminLogin.emailPlaceholder"
              />

              <datalist id="admin-email-options">
                <option
                  v-for="account in accounts"
                  :key="account.email"
                  :value="account.email"
                >
                  {{ majorLabel(account) }}
                </option>
              </datalist>

            </div>

          </div>


          <p class="accounts-title">{{ t.adminLogin.accountsTitle }}</p>

          <div class="account-list">
            <button
              v-for="account in accounts"
              :key="account.email"
              type="button"
              class="account-option"
              :class="{ selected: email.trim().toLowerCase() === account.email }"
              @click="chooseAccount(account)"
            >
              <strong>{{ account.email }}</strong>
              <small>{{ majorLabel(account) }}</small>
            </button>
          </div>


          <p v-if="errorMessage" class="error-text" role="alert">
            {{ errorMessage }}
          </p>


          <!-- Login -->
          <button
            class="sign-in-btn"
            type="submit"
            :disabled="submitting"
          >

            {{ t.adminLogin.signInButton }}

            <ArrowRight :size="20" />

          </button>

        </form>

      </div>

    </div>

  </div>
</template>


<style scoped>
* {
  box-sizing: border-box;
}

.admin-login-page {
  width: 100%;
  min-height: 100vh;

  display: flex;

  background: white;
}


/* =========================
   Image Side
========================= */

.image-side {
  width: 51%;
  min-height: 100vh;

  position: relative;

  /*
    ใส่รูปของคุณเองตรงนี้ภายหลัง
  */
  background-image:
    linear-gradient(
      rgba(0, 63, 111, 0.05),
      rgba(0, 63, 111, 0.08)
    ),
    url('/admin-building.jpg');

  background-position: center;
  background-size: cover;
  background-repeat: no-repeat;

  background-color: #16658e;
}


/* =========================
   Login Side
========================= */

.login-side {
  width: 49%;

  min-height: 100vh;

  display: flex;
  justify-content: center;
  align-items: center;

  position: relative;

  padding: 60px;
}

.login-container {
  width: 100%;
  max-width: 520px;
}


/* =========================
   Back button
========================= */

.back-btn {
  position: absolute;

  right: 38px;
  top: 34px;

  width: 48px;
  height: 48px;

  border: none;
  border-radius: 9px;

  background: #a60bd5;
  color: white;

  display: flex;
  align-items: center;
  justify-content: center;

  cursor: pointer;

  transition: 0.2s;
}

.back-btn:hover {
  background: #9005bb;
}


/* =========================
   Title
========================= */

.admin-title {
  display: flex;
  align-items: center;
  gap: 14px;

  margin-bottom: 48px;
}

.admin-icon {
  width: 43px;
  height: 43px;

  display: flex;
  align-items: center;
  justify-content: center;

  border-radius: 9px;

  background: #a60bd5;
  color: white;
}

.admin-title h1 {
  margin: 0;

  color: #071442;

  font-size: 25px;
  font-weight: 600;
}

.admin-title p {
  margin: 3px 0 0;

  color: #777b85;

  font-size: 13px;
}


/* =========================
   Form
========================= */

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;

  margin-bottom: 9px;

  font-size: 13px;

  color: #374151;
}

.input-wrapper {
  position: relative;
}

.input-wrapper input {
  width: 100%;
  height: 52px;

  padding: 0 45px;

  /* พื้นหลังขาวอมเทา */
  background: #f8fafc !important;

  border: 1px solid #d8dee9;
  border-radius: 7px;

  outline: none;

  /* สีตัวหนังสือตอนพิมพ์ */
  color: #1f2937 !important;

  font-size: 15px;
  font-family: inherit;

  color-scheme: light;

  transition: 0.2s;
}

/* Placeholder */
.input-wrapper input::placeholder {
  color: #9aa5b5;
  opacity: 1;
}

/* ตอนคลิกช่องกรอก */
.input-wrapper input:focus {
  background: #ffffff !important;

  border-color: #a60bd5;

  box-shadow:
    0 0 0 3px rgba(166, 11, 213, 0.08);
}

/* ป้องกัน Chrome Autofill เปลี่ยนสีช่อง */
.input-wrapper input:-webkit-autofill,
.input-wrapper input:-webkit-autofill:hover,
.input-wrapper input:-webkit-autofill:focus {
  -webkit-text-fill-color: #1f2937 !important;
  -webkit-box-shadow:
    0 0 0 1000px #f8fafc inset !important;

  transition:
    background-color 9999s ease-in-out 0s;
}

.input-icon {
  position: absolute;

  left: 14px;
  top: 50%;

  transform: translateY(-50%);

  color: #8c929c;
}

/* =========================
   Login button
========================= */

.sign-in-btn {
  width: 100%;
  height: 58px;

  border: none;
  border-radius: 7px;

  background: #a60bd5;

  color: white;

  font-size: 21px;

  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;

  cursor: pointer;

  box-shadow:
    0 10px 20px rgba(166, 11, 213, 0.15);

  transition: 0.2s;
}

.sign-in-btn:hover {
  background: #9005bb;
}


/* =========================
   Responsive
========================= */

@media (max-width: 900px) {

  .image-side {
    display: none;
  }

  .login-side {
    width: 100%;

    padding: 35px;
  }

  .admin-title {
    margin-bottom: 36px;
  }

}

@media (max-width: 500px) {

  .login-side {
    padding: 25px;
  }

  .back-btn {
    right: 20px;
    top: 20px;

    width: 42px;
    height: 42px;
  }

  .admin-title h1 {
    font-size: 22px;
  }

}


/* =========================
   Bypass notice / accounts
========================= */

.status-text {
  color: #777b85;
  font-size: 14px;
}

.notice {
  display: flex;
  gap: 10px;
  align-items: flex-start;

  margin-bottom: 24px;
  padding: 14px 16px;

  border-radius: 8px;

  font-size: 13.5px;
  line-height: 1.5;
}

.notice svg {
  flex-shrink: 0;
  margin-top: 2px;
}

.notice p {
  margin: 0;
}

.notice strong {
  display: block;
  margin-bottom: 6px;
}

.notice code {
  display: block;

  margin: 6px 0 10px;
  padding: 7px 10px;

  border-radius: 6px;

  background: rgba(0, 0, 0, 0.06);

  font-size: 13px;
  word-break: break-all;
}

.notice-info {
  background: #f5eafa;
  color: #6b2a80;
}

.notice-warning {
  background: #fff7e6;
  color: #7a4b00;
  border: 1px solid #f5d38b;
}

.notice-error {
  background: #fdecec;
  color: #8a1c1c;
}

.retry-btn {
  margin-top: 4px;
  padding: 6px 14px;

  border: 1px solid currentColor;
  border-radius: 6px;

  background: transparent;
  color: inherit;

  font-size: 13px;
  font-family: inherit;

  cursor: pointer;
}

.accounts-title {
  margin: 0 0 9px;

  font-size: 13px;
  color: #374151;
}

.account-list {
  display: flex;
  flex-direction: column;
  gap: 8px;

  margin-bottom: 24px;
}

.account-option {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;

  width: 100%;
  padding: 10px 14px;

  border: 1px solid #d8dee9;
  border-radius: 7px;

  background: #f8fafc;

  font-family: inherit;
  text-align: left;

  cursor: pointer;

  transition: 0.2s;
}

.account-option strong {
  color: #1f2937;
  font-size: 14px;
  font-weight: 600;
  word-break: break-all;
}

.account-option small {
  color: #777b85;
  font-size: 12.5px;
}

.account-option:hover,
.account-option.selected {
  border-color: #a60bd5;
  background: #ffffff;
}

.account-option.selected {
  box-shadow: 0 0 0 3px rgba(166, 11, 213, 0.08);
}

.error-text {
  margin: -8px 0 18px;

  color: #b42318;
  font-size: 13px;
}

.sign-in-btn:disabled {
  opacity: 0.7;
  cursor: wait;
}
</style>