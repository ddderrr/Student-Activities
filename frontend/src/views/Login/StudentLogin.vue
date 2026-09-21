<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  GraduationCap,
  BriefcaseBusiness,
  LockKeyhole,
  Eye,
  EyeOff,
  ArrowRight
} from 'lucide-vue-next'
import { useLanguage } from '../../composables/useLanguage'

const { t } = useLanguage()

const router = useRouter()

const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const showPassword = ref(false)

/*
  MOCK LOGIN
  ตอนนี้ยังไม่ตรวจ Username / Password
*/
const loginStudent = () => {
  router.push('/student/activities')
}

const goAdminLogin = () => {
  router.push('/admin/login')
}
</script>

<template>
  <div class="login-page">

    <div class="login-card">

      <!-- Header -->
      <div class="header">
        <div class="brand">
          <div class="brand-icon">
            <GraduationCap :size="22" />
          </div>

          <div>
            <h1>{{ t.studentLogin.universityName }}</h1>
            <p>{{ t.studentLogin.facultyName }}</p>
          </div>
        </div>

        <button
          class="admin-btn"
          type="button"
          @click="goAdminLogin"
        >
          <BriefcaseBusiness :size="15" />
          {{ t.studentLogin.adminLogin }}
        </button>
      </div>


      <!-- Login Form -->
      <form @submit.prevent="loginStudent">

        <div class="form-group">
          <label>{{ t.studentLogin.usernameLabel }}</label>

          <div class="input-wrapper">
            <BriefcaseBusiness
              class="input-icon"
              :size="17"
            />

            <input
              v-model="username"
              type="text"
            />
          </div>
        </div>


        <div class="form-group">
          <label>{{ t.studentLogin.passwordLabel }}</label>

          <div class="input-wrapper">
            <LockKeyhole
              class="input-icon"
              :size="17"
            />

            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
            />

            <button
              class="eye-btn"
              type="button"
              @click="showPassword = !showPassword"
            >
              <EyeOff
                v-if="showPassword"
                :size="17"
              />

              <Eye
                v-else
                :size="17"
              />
            </button>
          </div>
        </div>


        <!-- options -->
        <div class="login-options">

          <label class="remember">
            <input
              v-model="rememberMe"
              type="checkbox"
            />

            <span>{{ t.studentLogin.rememberMe }}</span>
          </label>

          <a
            href="#"
            @click.prevent
          >
            {{ t.studentLogin.forgotPassword }}
          </a>

        </div>


        <!-- Sign In -->
        <button
          class="sign-in-btn"
          type="submit"
        >
          {{ t.studentLogin.signInButton }}
          <ArrowRight :size="19" />
        </button>


        <p class="support-text">
          {{ t.studentLogin.newToPortal }}
          <a href="#" @click.prevent>
            {{ t.studentLogin.contactItSupport }}
          </a>
          {{ t.studentLogin.forAccess }}
        </p>

      </form>

    </div>

  </div>
</template>

<style scoped>
* {
  box-sizing: border-box;
}

.login-page {
  width: 100%;
  min-height: 100vh;

  display: flex;
  justify-content: center;
  align-items: center;

  background: #ffffff;

  padding: 30px;
}

.login-card {
  width: 100%;
  max-width: 550px;
}


/* =========================
   Header
========================= */

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  margin-bottom: 120px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 40px;
  height: 40px;

  display: flex;
  align-items: center;
  justify-content: center;

  background: #a100d4;
  color: white;

  border-radius: 9px;
}

.brand h1 {
  margin: 0;

  font-size: 21px;
  font-weight: 600;

  color: #071442;
}

.brand p {
  margin: 3px 0 0;

  font-size: 11px;
  color: #7c7c86;
}


/* =========================
   Admin Button
========================= */

.admin-btn {
  height: 38px;

  padding: 0 14px;

  display: flex;
  align-items: center;
  gap: 7px;

  background: white;

  border: 1px solid #9ca3af;
  border-radius: 6px;

  color: #111827;

  cursor: pointer;

  transition: 0.2s;
}

.admin-btn:hover {
  background: #f5f5f5;
}


/* =========================
   Form
========================= */

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;

  margin-bottom: 8px;

  color: #374151;

  font-size: 13px;
}

.input-wrapper {
  position: relative;
}

.input-wrapper input {
  width: 100%;
  height: 52px;

  padding: 0 45px;

  /* ทำช่องกรอกเป็นขาวอมเทา */
  background: #f8fafc !important;

  border: 1px solid #d8dee9;
  border-radius: 7px;

  outline: none;

  /* ตัวหนังสือที่พิมพ์ */
  color: #1f2937 !important;

  font-size: 15px;
  font-family: inherit;

  transition: 0.2s;
}

/* ถ้ามี placeholder */
.input-wrapper input::placeholder {
  color: #9aa5b5;
  opacity: 1;
}

/* ตอนกดช่องกรอก */
.input-wrapper input:focus {
  background: #ffffff !important;
  border-color: #a100d4;

  box-shadow:
    0 0 0 3px rgba(161, 0, 212, 0.08);
}

/* ป้องกัน browser autofill ทำสีช่องเพี้ยน */
.input-wrapper input:-webkit-autofill,
.input-wrapper input:-webkit-autofill:hover,
.input-wrapper input:-webkit-autofill:focus {
  -webkit-text-fill-color: #1f2937;
  -webkit-box-shadow: 0 0 0 1000px #f8fafc inset;
  transition: background-color 9999s ease-in-out 0s;
}

.input-icon {
  position: absolute;

  left: 14px;
  top: 50%;

  transform: translateY(-50%);

  color: #8c929c;
}

.eye-btn {
  position: absolute;

  right: 13px;
  top: 50%;

  transform: translateY(-50%);

  border: none;
  background: none;

  color: #8c929c;

  cursor: pointer;
}


/* =========================
   Options
========================= */

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;

  margin: 3px 0 30px;
}

.remember {
  display: flex;
  align-items: center;
  gap: 8px;

  font-size: 13px;
  color: #374151;

  cursor: pointer;
}

.remember input {
  width: 16px;
  height: 16px;
}

.login-options a {
  font-size: 13px;

  color: #071442;

  text-decoration: none;
}


/* =========================
   Sign In
========================= */

.sign-in-btn {
  width: 100%;
  height: 55px;

  border: none;
  border-radius: 7px;

  background: #a60bd5;

  color: white;

  font-size: 19px;
  font-weight: 500;

  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;

  cursor: pointer;

  transition: 0.2s;

  box-shadow:
    0 8px 18px rgba(161, 0, 212, 0.15);
}

.sign-in-btn:hover {
  background: #9005bb;
}


/* =========================
   Support
========================= */

.support-text {
  text-align: center;

  margin-top: 34px;

  font-size: 13px;

  color: #555;
}

.support-text a {
  color: #168243;

  text-decoration: none;
}


/* =========================
   Mobile
========================= */

@media (max-width: 600px) {
  .login-page {
    padding: 24px;
  }

  .header {
    margin-bottom: 70px;
  }

  .brand h1 {
    font-size: 17px;
  }

  .brand p {
    font-size: 10px;
  }

  .admin-btn {
    padding: 0 10px;

    font-size: 11px;
  }
}
</style>